import os
import yaml
import scrapy
import pytz
from datetime import datetime

from ..items import CrawlerItem
from ..utils import search_gangs, search_tags, validate_article
from ..keywords import KEYWORDS

class DiplomatiqueSpider(scrapy.Spider):
    """
    Spider do portal Le Monde Brasil Diplomatique

    Extração: iteração sobre as palavras-chave definidas em KEYWORDS.

    Controle: Ignora palavras-chave já listadas no YAML de checkpoint.
    """

    name = 'diplomatique'
    allowed_domains = ['diplomatique.org.br']
    
    custom_settings = {
        'HTTPERROR_ALLOWED_CODES': [404],
        'HTTPERROR_ALLOW_ALL': True,
    }

    SEARCH_PAGE_URL = 'https://diplomatique.org.br/page/1/?s={keyword}&orderby=date&order=DESC'
    search_results_selector = '//h3/a/@href | //h2/a/@href'
    next_page_selector = '//a[@class="number nextp"]/@href'
    article_title_selector = '//h1[contains(@class, "post-title")]/a/text()'
    article_date_selector = '//time[contains(@class, "entry-date")]/@datetime | //time[contains(@class, "datapublicacao")]/@datetime'
    article_content_selector = '//div[@class="entry-content"]//p//text()'
    article_newspaper_name = 'Le Monde Brasil Diplomatique'
    payed_articles_selector = '//div[@class="paywall-placeholder"]'

    def __init__(self, keyword=None, *args, **kwargs):
        super(DiplomatiqueSpider, self).__init__(*args, **kwargs)
        self.user_keyword = keyword
        self.outstanding_requests = 0
        self.keyword_index = 0
        self.current_keyword = None
        self.search_keywords = []
        
        self._initialize_keywords()

    @property
    def checkpoint_path(self):
        folder = 'kwords-processing'
        if not os.path.exists(folder):
            os.makedirs(folder)
        return os.path.join(folder, f"{self.name}_processed_kwords.yaml")

    def _initialize_keywords(self):
        """Prepara a lista de termos ignorando os já processados no YAML."""
        if self.user_keyword:
            full_list = [self.user_keyword]
        else:
            # Consolida as listas do arquivo de keywords
            full_list = KEYWORDS.get('GANGS', []) + KEYWORDS.get('ORGANIZED CRIME', [])

        done = set()
        if os.path.exists(self.checkpoint_path):
            with open(self.checkpoint_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
                done = set(data) if isinstance(data, list) else set()

        # Filtra apenas o que não foi feito
        self.search_keywords = [k for k in full_list if k not in done]

    def _mark_as_done(self, keyword):
        """Persiste a keyword finalizada no YAML."""
        done = []
        if os.path.exists(self.checkpoint_path):
            with open(self.checkpoint_path, 'r', encoding='utf-8') as f:
                done = yaml.safe_load(f) or []
        
        if keyword not in done:
            done.append(keyword)
            with open(self.checkpoint_path, 'w', encoding='utf-8') as f:
                yaml.dump(done, f, allow_unicode=True)

    def start_requests(self):
        yield from self.process_next_keyword()

    def process_next_keyword(self):
        if self.keyword_index < len(self.search_keywords):
            self.current_keyword = self.search_keywords[self.keyword_index]
            print(f'[PROCESSO] Processando palavra-chave: {self.current_keyword}')
            self.keyword_index += 1
            
            search_url = self.SEARCH_PAGE_URL.format(keyword=self.current_keyword.replace(' ', '+'))
            
            self.outstanding_requests = 1
            yield scrapy.Request(url=search_url, callback=self.parse_search_results)
        else:
            print("[SUCESSO] Todas as palavras-chave foram processadas.")

    def parse_search_results(self, response):
        links = response.xpath(self.search_results_selector).getall()
        for link in links:
            self.outstanding_requests += 1
            yield scrapy.Request(
                url=response.urljoin(link), 
                callback=self.parse_item,
                errback=self.handle_failure
            )
            
        next_page = response.xpath(self.next_page_selector).get()
        if next_page:
            self.outstanding_requests += 1
            yield scrapy.Request(url=response.urljoin(next_page), callback=self.parse_search_results)

        self.outstanding_requests -= 1
        if self.outstanding_requests <= 0:
            yield from self.check_and_advance()

    def parse_item(self, response):
        if not response.xpath(self.payed_articles_selector).get():
            item = CrawlerItem()
            content_parts = response.xpath(self.article_content_selector).getall()
            article_body = ' '.join([p.strip() for p in content_parts if p.strip()])
            
            validate = validate_article(article_body)
            if validate:
                item['title'] = response.xpath(self.article_title_selector).get()
                item['url'] = response.url
                item['acquisition_date'] = datetime.now(pytz.timezone('America/Sao_Paulo')).strftime('%d-%m-%Y')
                item['newspaper'] = self.article_newspaper_name
                item['article'] = article_body
                item['accepted_by'] = validate
                item['gangs'] = search_gangs(article_body)
                item['tags'] = search_tags(article_body)
                item['manual_relevance_class'] = None
                
            else:
                item['url'] = response.url

            item['keyword'] = self.current_keyword
            date_raw = response.xpath(self.article_date_selector).get()
            item['publication_date'] = date_raw.split('T')[0] if date_raw and 'T' in date_raw else date_raw

            yield item

        self.outstanding_requests -= 1
        if self.outstanding_requests <= 0:
            yield from self.check_and_advance()

    def handle_failure(self, failure):
        self.outstanding_requests -= 1
        if self.outstanding_requests <= 0:
            yield from self.check_and_advance()

    def check_and_advance(self):
        if self.current_keyword:
            self._mark_as_done(self.current_keyword)
            print(f"[SUCESSO] Termo '{self.current_keyword}' concluído e salvo no YAML.")

        self.outstanding_requests = 0 
        yield from self.process_next_keyword()