import re
import scrapy
import pytz
import calendar
from datetime import datetime
from scrapy import signals
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

class SpiderCorreioDoPovo(BaseSpider):
    """
    Spider para o portal Correio do Povo.
    
    Combina o uso de Playwright para renderização de resultados dinâmicos e paginação, 
    com o Scrapy puro para a extração ágil do conteúdo das notícias (itens). 
    Utiliza padrões de Regex para identificar links de notícias no meio de outros elementos.
    """
    name = 'correio'
    allowed_domains = ['correiodopovo.com.br']

    custom_settings = {
        "DOWNLOAD_HANDLERS": {
            "http": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
            "https": "scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler",
        },
        "TWISTED_REACTOR": "twisted.internet.asyncioreactor.AsyncioSelectorReactor",
        "PLAYWRIGHT_LAUNCH_OPTIONS": {"headless": True, "timeout": 20000},
        "ROBOTSTXT_OBEY": False,
        "COOKIES_ENABLED": True,
        "DEFAULT_REQUEST_HEADERS": {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept-Language': 'pt-BR,pt;q=0.9',
            'Referer': 'https://www.google.com/'
        },
    }

    # Configurações de Seletores e Padrões
    search_url_template = 'https://www.correiodopovo.com.br/busca?q={keyword}&page={page_number}&sort=date'
    next_page_selector = '//li/a[@title="Next page"]' 
    article_title_selector = '//h1[contains(@class, "article__headline")]/text() | //h1/text()'
    article_date_selector = '//time/@datetime'
    article_content_selector = '//div[contains(@class, "article__body")]/p//text() | //div[contains(@class, "content-text")]/p//text()'
    payed_articles_selector = '//div[contains(@class, "conteudo_pago")]'
    
    # Regex para validar URLs de notícias que terminam em ID numérico (ex: -1.123456)
    news_pattern = re.compile(r'-\d+\.\d+$')

    def start_requests(self):
        """
        Lógica centralizada: filtra as keywords já processadas antes de iniciar o loop.
        """
        # 1. Define a lista base
        if hasattr(self, 'user_keyword') and self.user_keyword:
            all_terms = [self.user_keyword]
        else:
            all_terms = KEYWORDS.get('GANGS', []) + KEYWORDS.get('ORGANIZED CRIME', [])
        
        # 2. Busca palavras já processadas (carregadas na RAM via utilitário)
        processed_terms = get_processed_kwords(self.name)
        
        # 3. Filtra apenas as que não foram feitas
        search_terms = [k for k in all_terms if k not in processed_terms]
        
        self.logger.info(f'[FILTRO] Total: {len(all_terms)} | Processadas: {len(processed_terms)} | Restantes: {len(search_terms)}')

        for keyword in search_terms:
            url = self.search_url_template.format(keyword=keyword.replace(' ', '+'), page_number=1)
            yield scrapy.Request(
                url=url, 
                callback=self.parse,
                meta={
                    'playwright': True, 
                    'playwright_include_page': True,
                    'keyword': keyword,
                    'page_number': 1
                },
                errback=self.errback_close_page
            )

    async def parse(self, response):
        page = response.meta.get("playwright_page")
        keyword = response.meta.get("keyword")
        curr_page = response.meta.get("page_number")

        try:
            # Scroll para carregar elementos dinâmicos
            await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
            await page.wait_for_timeout(2000)

            hrefs = await page.evaluate("() => Array.from(document.querySelectorAll('a')).map(a => a.href)")
            article_links = list(set([l for l in hrefs if l and self.news_pattern.search(l)]))

            for link in article_links:
                yield scrapy.Request(
                    url=link, 
                    callback=self.parse_item, 
                    meta={'keyword': keyword},
                    errback=self.handle_failure, 
                    dont_filter=True
                )

            # Lógica de Paginação
            sel = scrapy.Selector(text=await page.content())
            if sel.xpath(self.next_page_selector).get():
                next_page = curr_page + 1
                next_url = self.search_url_template.format(keyword=keyword.replace(' ', '+'), page_number=next_page)
                yield scrapy.Request(
                    url=next_url, 
                    callback=self.parse,
                    meta={
                        'playwright': True, 
                        'playwright_include_page': True,
                        'keyword': keyword,
                        'page_number': next_page
                    },
                    errback=self.errback_close_page
                )
            else:
                # Se não há próxima página, a keyword foi concluída
                self.logger.info(f'[CONCLUÍDO] Keyword finalizada: {keyword}')
                save_processed_kword(keyword, self.name)

        finally:
            if page: 
                await page.close()

    def parse_item(self, response):
        keyword = response.meta.get("keyword")
        
        if not response.xpath(self.payed_articles_selector).get():
            item = CrawlerItem()
            body = ' '.join(response.xpath(self.article_content_selector).getall()).strip()
            validate = validate_article(body)
            
            item['keyword'] = keyword
            item['url'] = response.url
            
            if validate:
                item['title'] = (response.xpath(self.article_title_selector).get() or "").strip()
                item['acquisition_date'] = datetime.now(pytz.timezone('America/Sao_Paulo')).strftime('%d-%m-%Y')
                item['newspaper'] = 'Correio do Povo'
                item['article'] = body
                item['accepted_by'] = validate
                item['gangs'] = search_gangs(body)
                item['tags'] = search_tags(body)
                
                dt = response.xpath(self.article_date_selector).get()
                item['publication_date'] = dt.split('T')[0] if dt and 'T' in dt else dt
                yield item
            else:
                # Opcional: retornar item negado apenas com URL e keyword
                yield item

    def handle_failure(self, failure):
        """
        Realiza o log de erros em requisições de notícias individuais.

        Args:
            failure (twisted.python.failure.Failure): Objeto de falha do Twisted/Scrapy.
        
        Notes:
            Utilizado no errback das requisições geradas pelo parse_search_results 
            para garantir que falhas em notícias específicas não interrompam o spider.
        """
        self.logger.error(f"Erro na requisição: {failure.request.url}")

    async def errback_close_page(self, failure):
        """
        Garante o fechamento da página do navegador em caso de erro no Playwright.

        Args:
            failure (twisted.python.failure.Failure): Objeto de falha contendo a meta 'playwright_page'.

        Notes:
            Essencial para evitar vazamento de memória (memory leaks) caso o navegador 
            trave ou a página de busca falhe em carregar.
        """
        page = failure.request.meta.get("playwright_page")
        if page: 
            await page.close()
        self.logger.error(f"Erro de Playwright na busca: {failure.request.url}")

    @classmethod
    def from_crawler(cls, crawler, *args, **kwargs):
        """
        Método de fábrica para instanciar o spider e conectar sinais do Scrapy.

        Args:
            crawler (scrapy.crawler.Crawler): Objeto crawler do Scrapy.
            *args: Argumentos variáveis.
            **kwargs: Argumentos nomeados.

        Returns:
            SpiderCorreioDoPovo: Instância do spider conectada ao sinal de fechamento.
        """
        spider = super(SpiderCorreioDoPovo, cls).from_crawler(crawler, *args, **kwargs)
        crawler.signals.connect(spider.spider_closed, signal=signals.spider_closed)
        return spider

    def spider_closed(self, spider):
        """
        Hook executado quando o spider termina suas atividades.

        Args:
            spider (scrapy.Spider): A instância do spider que foi fechada.
            
        Notes:
            Útil para encerramento de conexões ou logs finais de auditoria.
        """
        self.logger.info("Spider encerrada.")