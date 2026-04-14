import scrapy
from datetime import datetime, timedelta
from urllib.parse import quote
import pytz
from scrapy_playwright.page import PageMethod
from ..utils import (
    search_gangs, 
    search_tags, 
    validate_article, 
    get_processed_kwords, 
    save_processed_kword
)
from ..items import CrawlerItem
from ..keywords import KEYWORDS
from base_spider import BaseSpider

# Configurações de URL e Arquivos
ORDER = 'recent'
SPECIES = quote('notícias')
SEARCH_DATE_FORMAT = r'%Y-%m-%d'
PAGE_SEARCH_URL_TEMPLATE = 'https://g1.globo.com/busca/?q={}&order={}&from={}T00%3A00%3A00-0300&to={}T23%3A59%3A59-0300&species={}'

def should_abort_request(request):
    """
    Determina se uma requisição deve ser interrompida para otimizar o carregamento.

    Args:
        request (scrapy.http.Request): Objeto da requisição interceptada pelo Playwright.

    Returns:
        bool: True se o tipo de recurso for dispensável (imagem, mídia, etc), False caso contrário.
    
    Notes:
        Esta função ajuda a reduzir o consumo de banda e processamento ao ignorar arquivos binários e CSS.
    """
    return request.resource_type in ["image", "media", "font", "stylesheet"]

def build_page_search_url(keyword, date):
    """
    Constrói a URL de busca do G1 formatada com a palavra-chave e data específica.

    Args:
        keyword (str): A palavra-chave ou termo de busca.
        date (datetime): Objeto datetime representando o dia da busca.

    Returns:
        str: URL completa e formatada para a requisição de busca.
    """
    day_str = date.strftime(SEARCH_DATE_FORMAT)
    return PAGE_SEARCH_URL_TEMPLATE.format(quote(keyword), ORDER, day_str, day_str, SPECIES)

class G1Spider(BaseSpider):
    name = "g1"
    allowed_domains = ["g1.globo.com", "globo.com"]
    
    custom_settings = {
        'DOWNLOAD_HANDLERS': {
            'http': 'scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler',
            'https': 'scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler',
        },
        'TWISTED_REACTOR': 'twisted.internet.asyncioreactor.AsyncioSelectorReactor',
        'PLAYWRIGHT_LAUNCH_OPTIONS': {'headless': True, 'timeout': 5000},
        'CONCURRENT_REQUESTS': 16,
        'PLAYWRIGHT_ABORT_REQUEST': should_abort_request
    }
    
    def __init__(self, **kwargs):
        """
        Inicializa o Spider definindo o escopo de palavras-chave e o ano alvo.

        Args:
            **kwargs: Argumentos passados via linha de comando (ex: -a y=2024 -a k="crime").
        
        Notes:
            Se 'k' não for fornecido, utiliza as listas 'GANGS' e 'ORGANIZED CRIME' de keywords.py.
            O ano padrão (target_year) é 2023 caso não seja especificado.
        """
        super().__init__(**kwargs)
        self.seen_urls = set()
        self.processed_kwords = []
        self.processed_kwords = get_processed_kwords(self.name)
        self.keywords = KEYWORDS['GANGS'] + KEYWORDS['ORGANIZED CRIME']
        if kwargs.get('k'): 
            self.keywords = [kwargs.get('k')]
        
        self.target_year = int(kwargs.get('y')) if kwargs.get('y') else 2023

    def start_requests(self):
        scroll_script = """
            async () => {
                let lastHeight = document.body.scrollHeight;
                while (true) {
                    window.scrollTo(0, document.body.scrollHeight);
                    await new Promise(resolve => setTimeout(resolve, 2000));
                    let newHeight = document.body.scrollHeight;
                    if (newHeight === lastHeight) break;
                    lastHeight = newHeight;
                }
            }
        """
        
        start_date = datetime(self.target_year, 1, 1)
        end_date = datetime.now() if self.target_year == datetime.now().year else datetime(self.target_year, 12, 31)

        for keyword in self.keywords:
            if keyword in self.processed_kwords:
                print(f'[AVISO] Palavra-chave {keyword} já foi processada. Pulando...')
                continue
            print(f"[PROCESSO] Processando palavra-chave: {keyword}")
            curr = start_date
            while curr <= end_date:
                url = build_page_search_url(keyword, curr)
                
                yield scrapy.Request(
                    url, 
                    self.parse, 
                    meta={
                        'keyword': keyword, 
                        'date': curr,
                        'playwright': True, 
                        'playwright_include_page': True,
                        'playwright_page_methods': [
                            PageMethod("wait_for_selector", "ul.results__list", timeout=15000),
                            PageMethod("evaluate", scroll_script),
                            PageMethod("wait_for_timeout", 1000), 
                        ]
                    },
                    errback=self.errback_close,
                    dont_filter=True
                )
                curr += timedelta(days=1)
            
            save_processed_kword(keyword, self.name)

    async def parse(self, response):
        page = response.meta["playwright_page"]
        keyword = response.meta['keyword']
        curr_date = response.meta['date'].strftime('%Y-%m-%d')
        
        try:
            # Seleciona os links dos cards de notícias
            links = response.css("li.widget--card a.widget--info__media::attr(href)").getall() or \
                    response.css("li.widget--card a.widget--info__text-container::attr(href)").getall()

            for url in links:
                if 'u=' in url:
                    try: 
                        from urllib.parse import parse_qs, urlparse
                        url = parse_qs(urlparse(url).query)['u'][0]
                    except: pass

                yield scrapy.Request(
                    url, 
                    self.parse_news, 
                    meta={'keyword': keyword},
                    dont_filter=False # Deixe o Scrapy filtrar URLs repetidas
                )
        
        finally:
            await page.close()

    def parse_news(self, response):
        # Validação básica de título
        title = response.css("h1.content-head__title::text").get() or response.css("h1.entry-title::text").get()
        if not title: 
            return

        # Agora recebemos o item DIRETAMENTE (não é mais um gerador)
        item = self.try_parse(response, self.parse_news_v2) or self.try_parse(response, self.parse_news_v1)
        
        if item:
            yield item # Envia o objeto CrawlerItem para o Pipeline

    def try_parse(self, response, method):
        """
        Tenta executar um método de extração específico lidando com exceções.

        Args:
            response (scrapy.http.Response): A resposta da página da notícia.
            method (callable): A função de parsing (v1 ou v2) a ser testada.

        Returns:
            CrawlerItem | None: Retorna o item preenchido se o parsing tiver sucesso, 
                               ou None se houver erro ou o layout não for compatível.
        """
        try: 
            return method(response) 
        except Exception as e:
            return None

    def parse_news_v1(self, response):
        """
        Realiza o parsing de notícias utilizando seletores do layout antigo do G1.

        Args:
            response (scrapy.http.Response): A resposta da página.

        Returns:
            CrawlerItem | None: Item processado ou None se o conteúdo for insuficiente.
        """
        texts = response.css("div#materia-letra p::text, div.entry-content p::text").getall()
        article = self.clean_text(texts)
        if not article: return None
        return self._base_item(response, article)

    def parse_news_v2(self, response):
        """
        Realiza o parsing de notícias utilizando seletores do layout moderno do G1.

        Args:
            response (scrapy.http.Response): A resposta da página.

        Returns:
            CrawlerItem | None: Item processado incluindo o subtítulo no corpo do texto.
        """
        sub = response.css("h2.content-head__subtitle::text").get() or ""
        texts = response.css("article p.content-text__container::text, div.mc-column.content-text p::text").getall()
        art = self.clean_text(texts)
        if not art: return None
        full_art = (sub.strip() + " " + art).strip()
        return self._base_item(response, full_art)

    def _base_item(self, response, article):
        """
        Gera e valida o objeto CrawlerItem com metadados e conteúdo extraído.

        Args:
            response (scrapy.http.Response): A resposta da página.
            article (str): O texto completo e limpo da notícia.

        Returns:
            CrawlerItem: O item populado com campos de tags, facções, data e jornal.
        
        Notes:
            A validação de relevância (validate_article) é executada antes de preencher campos sensíveis.
        """
        item = CrawlerItem()
        validate = validate_article(article)

        if validate:
            item['title'] = (response.css("h1.content-head__title::text").get() or response.css("h1.entry-title::text").get() or "").strip()
            item['article'] = article
            item['accepted_by'] = validate
            item['gangs'] = search_gangs(article)
            item['tags'] = search_tags(article)
            item['acquisition_date'] = datetime.now(pytz.timezone('America/Sao_Paulo')).strftime(r'%d-%m-%Y')
            item['newspaper'] = 'G1'
            item['manual_relevance_class'] = None 

        item['url'] = response.url
        item['keyword'] = response.meta['keyword']
        pub_date = self.extract_date(response)
        item['publication_date'] = pub_date

        return item

    def clean_text(self, text_list):
        """
        Limpa e concatena uma lista de strings em um único bloco de texto.

        Args:
            text_list (list): Lista de strings extraídas via seletores CSS.

        Returns:
            str | None: Texto formatado ou None se o resultado for menor que 50 caracteres.
        """
        if not text_list: return None
        full_text = ' '.join([t.strip() for t in text_list if t.strip()])
        return full_text if len(full_text) > 50 else None

    def extract_date(self, response):
        """
        Extrai a data de publicação da notícia de diferentes possíveis locais no HTML.

        Args:
            response (scrapy.http.Response): A resposta da página.

        Returns:
            str | None: Data formatada como 'dd-mm-aaaa' ou None se não encontrada.
        
        Notes:
            Tenta primeiro o atributo ISO 'datetime' e depois formatos de texto legível.
        """
        iso = response.css('time[itemprop="datePublished"]::attr(datetime)').get()
        if iso:
            return datetime.strptime(iso[:10], r'%Y-%m-%d').strftime(r'%d-%m-%Y')
        
        text = response.css('time[itemprop="datePublished"]::text, .content-publication-data__updated time::text, abbr.published::text').get()
        if text:
            try: return datetime.strptime(text.strip()[:16], r'%d/%m/%Y %Hh%M').strftime(r'%d-%m-%Y')
            except: pass
        return None

    async def errback_close(self, failure):
        """
        Trata falhas em requisições Playwright, garantindo o fechamento da página.

        Args:
            failure (twisted.python.failure.Failure): Objeto de erro do Scrapy/Twisted.
        
        Yields:
            Nada diretamente, mas executa o fechamento assíncrono da página do navegador.
        """
        if failure.request.meta.get("playwright_page"):
            await failure.request.meta["playwright_page"].close()