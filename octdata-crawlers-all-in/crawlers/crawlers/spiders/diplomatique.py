import scrapy
import pytz
from datetime import datetime
from base_spider import BaseSpider
from ..items import CrawlerItem
from ..utils import (
    search_gangs, 
    search_tags, 
    validate_article, 
    get_processed_kwords, 
    save_processed_kword
)
from ..keywords import KEYWORDS

class DiplomatiqueSpider(BaseSpider):
    """
    Spider especializado para o portal Le Monde Diplomatique Brasil.
    
    Diferente dos spiders anteriores, este utiliza um sistema de contagem de 
    requisições pendentes (outstanding_requests) para gerenciar a transição 
    assíncrona entre diferentes palavras-chave sem sobrepor os processos.
    """
    name = 'diplomatique'
    allowed_domains = ['diplomatique.org.br']
    
    custom_settings = {
        'HTTPERROR_ALLOWED_CODES': [404],
        'HTTPERROR_ALLOW_ALL': True,
    }

    # Seletores XPath e configurações de URL
    SEARCH_PAGE_URL = 'https://diplomatique.org.br/page/1/?s={keyword}&orderby=date&order=DESC'
    search_results_selector = '//h3/a/@href | //h2/a/@href'
    next_page_selector = '//a[@class="number nextp"]/@href'
    article_title_selector = '//h1[contains(@class, "post-title")]/a/text()'
    article_date_selector = '//time[contains(@class, "entry-date")]/@datetime | //time[contains(@class, "datapublicacao")]/@datetime'
    article_content_selector = '//div[@class="entry-content"]//p//text()'
    article_newspaper_name = 'Le Monde Brasil Diplomatique'
    payed_articles_selector = '//div[@class="paywall-placeholder"]'

    def __init__(self, keyword=None, *args, **kwargs):
        """
        Inicializa o spider configurando o controle de fluxo de palavras-chave.

        Args:
            keyword (str, optional): Palavra-chave específica passada via CLI (-a keyword=...).
            *args: Argumentos posicionais da superclasse.
            **kwargs: Argumentos nomeados da superclasse.

        Notes:
            Inicializa 'outstanding_requests' em 0 para rastrear o processamento assíncrono.
        """
        super(DiplomatiqueSpider, self).__init__(*args, **kwargs)
        self.user_keyword = keyword
        self.outstanding_requests = 0
        self.keyword_index = 0
        self.current_keyword = None
        self.search_keywords = []
        
        self._initialize_keywords()

    def _initialize_keywords(self):
        """
        Prepara e filtra a lista de termos de busca.

        Notes:
            Consolida as listas 'GANGS' e 'ORGANIZED CRIME' e remove termos 
            que já constam no log de processados do utilitário 'get_processed_kwords'.
        """
        if self.user_keyword:
            full_list = [self.user_keyword]
        else:
            full_list = KEYWORDS.get('GANGS', []) + KEYWORDS.get('ORGANIZED CRIME', [])

        done = get_processed_kwords(self.name)
        self.search_keywords = [k for k in full_list if k not in done]

    def start_requests(self):
        yield from self.process_next_keyword()

    def process_next_keyword(self):
        """
        Orquestra a transição para a próxima palavra-chave da lista.

        Yields:
            scrapy.Request: A requisição inicial para a página de busca do novo termo.

        Notes:
            Incrementa o 'keyword_index' e limpa o contador de requisições pendentes.
        """
        if self.keyword_index < len(self.search_keywords):
            self.current_keyword = self.search_keywords[self.keyword_index]
            print(f'[PROCESSO] Processando palavra-chave: {self.current_keyword}')
            self.keyword_index += 1
            
            search_url = self.SEARCH_PAGE_URL.format(keyword=self.current_keyword.replace(' ', '+'))
            
            self.outstanding_requests = 1
            yield scrapy.Request(url=search_url, callback=self.parse)
        else:
            print("[SUCESSO] Todas as palavras-chave foram processadas.")

    def parse(self, response):
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
            yield scrapy.Request(url=response.urljoin(next_page), callback=self.parse)

        self.outstanding_requests -= 1
        if self.outstanding_requests <= 0:
            yield from self.check_and_advance()

    def parse_item(self, response):
        # Ignora se for conteúdo exclusivo (paywall)
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
        """
        Trata falhas de conexão ou erros de requisição nas notícias individuais.

        Args:
            failure (twisted.python.failure.Failure): Objeto contendo os detalhes do erro.

        Notes:
            Decrementa o contador de requisições e verifica se é necessário avançar 
            para o próximo termo caso esta tenha sido a última pendência.
        """
        self.outstanding_requests -= 1
        if self.outstanding_requests <= 0:
            yield from self.check_and_advance()

    def check_and_advance(self):
        """
        Finaliza o ciclo de vida de uma palavra-chave.

        Yields:
            Generator: Chama 'process_next_keyword' para buscar o próximo termo.

        Notes:
            Salva a palavra-chave atual no log de concluídos via 'save_processed_kword' 
            antes de reiniciar os contadores.
        """
        if self.current_keyword:
            save_processed_kword(self.name, self.current_keyword)
            print(f"[SUCESSO] Termo '{self.current_keyword}' concluído e salvo.")

        self.outstanding_requests = 0 
        yield from self.process_next_keyword()