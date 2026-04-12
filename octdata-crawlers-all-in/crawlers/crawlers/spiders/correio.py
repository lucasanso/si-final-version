import os
import re
import yaml
import scrapy
import pytz
from datetime import datetime
from scrapy import signals

# Assumindo que estas dependências continuam existindo no seu projeto
from ..items import CrawlerItem
from ..utils import search_gangs, search_tags, validate_article
from ..keywords import KEYWORDS 

class SpiderCorreioDoPovo(scrapy.Spider):
    name = 'correio'
    allowed_domains = ['correiodopovo.com.br']

    custom_settings = {
        "DOWNLOAD_HANDLERS": {
            "http": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
            "https": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
        },
        "TWISTED_REACTOR": "twisted.internet.asyncioreactor.AsyncioSelectorReactor",
        "PLAYWRIGHT_LAUNCH_OPTIONS": {"headless": False, "timeout": 20000},
        "ROBOTSTXT_OBEY": False,
        "COOKIES_ENABLED": True,
        "DEFAULT_REQUEST_HEADERS": {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36...',
            'Accept-Language': 'pt-BR,pt;q=0.9',
            'Referer': 'https://www.google.com/'
        },
    }

    # Seletores e Templates
    search_url_template = 'https://www.correiodopovo.com.br/busca?q={keyword}&page={page_number}&sort=date'
    next_page_selector = '//li/a[@title="Next page"]' 
    article_title_selector = '//h1[contains(@class, "article__headline")]/text() | //h1/text()'
    article_date_selector = '//time/@datetime'
    article_content_selector = '//div[contains(@class, "article__body")]/p//text() | //div[contains(@class, "content-text")]/p//text()'
    payed_articles_selector = '//div[contains(@class, "conteudo_pago")]'
    news_pattern = re.compile(r'-\d+\.\d+$')

    def __init__(self, keyword=None, *args, **kwargs):
        super(SpiderCorreioDoPovo, self).__init__(*args, **kwargs)
        self.user_keyword = keyword
        self.outstanding_requests = 0
        self.keyword_index = 0
        self.current_keyword = None
        
        # Inicialização
        self.search_keywords = self._initialize_keywords()

    # --- Persistência YAML ---
    @property
    def checkpoint_path(self):
        folder = 'kwords-processing'
        if not os.path.exists(folder):
            os.makedirs(folder)
        return os.path.join(folder, f"{self.name}_processed_kwords.yaml")

    def _get_ignored_keywords(self):
        if not os.path.exists(self.checkpoint_path):
            return set()
        try:
            with open(self.checkpoint_path, 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
                return set(data) if isinstance(data, list) else set()
        except:
            return set()

    def _mark_as_done(self, keyword):
        if not keyword: return
        done = self._get_ignored_keywords()
        if keyword not in done:
            done.add(keyword)
            with open(self.checkpoint_path, 'w', encoding='utf-8') as f:
                yaml.dump(list(done), f, allow_unicode=True, default_flow_style=False)

    def _initialize_keywords(self):
        full_list = [self.user_keyword] if self.user_keyword else \
                    KEYWORDS.get('GANGS', []) + KEYWORDS.get('ORGANIZED CRIME', [])
        done = self._get_ignored_keywords()
        return [k for k in full_list if k not in done]

    def start_requests(self):
        for req in self.process_next_keyword():
            yield req

    def process_next_keyword(self):
        if self.keyword_index < len(self.search_keywords):
            self.current_keyword = self.search_keywords[self.keyword_index]
            self.keyword_index += 1
            
            url = self.search_url_template.format(keyword=self.current_keyword.replace(' ', '+'), page_number=1)
            self.outstanding_requests = 1
            yield scrapy.Request(
                url=url, 
                callback=self.parse_search_results,
                meta={'playwright': True, 'playwright_include_page': True},
                errback=self.errback_close_page
            )

    async def parse_search_results(self, response):
        page = response.meta.get("playwright_page")
        try:
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await page.wait_for_timeout(2000)

            hrefs = await page.evaluate("() => Array.from(document.querySelectorAll('a')).map(a => a.href)")
            article_links = list(set([l for l in hrefs if l and self.news_pattern.search(l)]))

            for link in article_links:
                self.outstanding_requests += 1
                yield scrapy.Request(url=link, callback=self.parse_item, errback=self.handle_failure, dont_filter=True)

            # Paginação
            curr_page = int(re.search(r'page=(\d+)', response.url).group(1)) if 'page=' in response.url else 1
            sel = scrapy.Selector(text=await page.content())
            
            if sel.xpath(self.next_page_selector).get():
                self.outstanding_requests += 1
                next_url = self.search_url_template.format(keyword=self.current_keyword.replace(' ', '+'), page_number=curr_page + 1)
                yield scrapy.Request(
                    url=next_url, 
                    callback=self.parse_search_results,
                    meta={'playwright': True, 'playwright_include_page': True},
                    errback=self.errback_close_page
                )
        finally:
            if page: await page.close()

        self.outstanding_requests -= 1
        if self.outstanding_requests <= 0:
            for req in self.check_and_advance():
                yield req

    def parse_item(self, response):
        item = CrawlerItem()
        if not response.xpath(self.payed_articles_selector).get():
            body = ' '.join(response.xpath(self.article_content_selector).getall()).strip()
            validate = validate_article(body)
            if validate:
                item['title'] = response.xpath(self.article_title_selector).get()
                item['url'] = response.url
                item['acquisition_date'] = datetime.now(pytz.timezone('America/Sao_Paulo')).strftime('%d-%m-%Y')
                item['newspaper'] = 'Correio do Povo'
                item['article'] = body
                item['keyword'] = self.current_keyword
                item['accepted_by'] = validate
                item['gangs'] = search_gangs(body)
                item['tags'] = search_tags(body)
                dt = response.xpath(self.article_date_selector).get()
                item['publication_date'] = dt.split('T')[0] if dt and 'T' in dt else dt
            
            else:
                item['url'] = response.url

            item['keyword'] = self.current_keyword
            dt = response.xpath(self.article_date_selector).get()
            item['publication_date'] = dt.split('T')[0] if dt and 'T' in dt else dt

            yield item

        self.outstanding_requests -= 1
        if self.outstanding_requests <= 0:
            for req in self.check_and_advance():
                yield req

    def check_and_advance(self):
        if self.current_keyword:
            self._mark_as_done(self.current_keyword)
        self.outstanding_requests = 0 
        for req in self.process_next_keyword():
            yield req

    def handle_failure(self, failure):
        self.outstanding_requests -= 1
        if self.outstanding_requests <= 0:
            return self.check_and_advance()

    async def errback_close_page(self, failure):
        page = failure.request.meta.get("playwright_page")
        if page: await page.close()
        self.outstanding_requests -= 1
        if self.outstanding_requests <= 0:
             for req in self.check_and_advance():
                yield req

    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        spider = super(SpiderCorreioDoPovo, cls).from_crawler(crawler, *args, **kwargs)
        crawler.signals.connect(spider.spider_closed, signal=signals.spider_closed)
        return spider

    def spider_closed(self, spider):
        self.logger.info("Spider fechada. Encerrando recursos remanescentes...")
        # O Scrapy-Playwright já tenta fechar o browser automaticamente aqui,
        # mas se você tivesse instâncias manuais, fecharia aqui.