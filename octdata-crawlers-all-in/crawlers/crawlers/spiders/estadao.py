import scrapy
import re
import pytz
import calendar
from datetime import datetime
from ..keywords import KEYWORDS
from ..settings import YEARS
from ..items import CrawlerItem
from ..utils import (
    search_gangs, 
    search_tags, 
    validate_article, 
    get_processed_kwords, 
    save_processed_kword
)

class EstadaoSpider(scrapy.Spider):
    """
    Spider especializado para o portal Estadão. 
    Diferencia-se por lidar com resultados de busca gerados dinamicamente via JavaScript,
    utilizando Playwright para navegar pela paginação interna das buscas.
    """
    name = "estadao"
    allowed_domains = ['www.estadao.com.br']

    # Configurações específicas para suportar execução assíncrona do Playwright
    custom_settings = {
        'DOWNLOAD_HANDLERS': {
            'http': 'scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler',
            'https': 'scrapy_playwright.handler.ScrapyPlaywrightDownloadHandler',
        },
        'TWISTED_REACTOR': 'twisted.internet.asyncioreactor.AsyncioSelectorReactor',
        'PLAYWRIGHT_LAUNCH_OPTIONS': {'headless': True, 'timeout': 30000},
        'CONCURRENT_REQUESTS': 3, # Valor baixo para evitar bloqueios por rate limiting
    }

    # URL base contendo o token de busca (JSON encodado) para filtros de data
    SEARCH_URL = "https://www.estadao.com.br/busca/?token=%257B%2522query%2522%253A%2522{}%2522%252C%2522date_range%2522%253A%2522{:02d}%252F{:02d}%252F{}%252C{:02d}%252F{:02d}%252F{}%2522%257D"

    def __init__(self, **kwargs):
        """
        Inicializa o spider do Estadão carregando o histórico de processamento.

        Args:
            **kwargs: Argumentos passados via comando Scrapy (ex: -a y=2024).

        Notes:
            A lista 'self.processed' é usada para pular palavras-chave que já
            foram completamente extraídas em execuções passadas.
        """
        super().__init__(**kwargs)
        self.processed = get_processed_kwords(self.name)

    def start_requests(self):
        words = KEYWORDS['GANGS'] + KEYWORDS['ORGANIZED CRIME']
        
        for w in words:
            if self.processed and w in self.processed:
                continue
            
            keyword_encoded = w.replace(" ", "%2520")
            for y in YEARS:
                for m in range(1, 13):
                    _, last_day = calendar.monthrange(y, m)
                    for d in range(1, last_day + 1):
                        url = self.SEARCH_URL.format(keyword_encoded, d, m, y, d, m, y)
                        
                        # Request limpa. O Playwright só entra no callback.
                        yield scrapy.Request(
                            url=url,
                            callback=self.parse,
                            meta={'keyword': w, 'date_str': f"{d:02d}/{m:02d}/{y}"}
                        )
            save_processed_kword(w, self.name)

    async def parse(self, response):
        keyword = response.meta.get('keyword')
        date_str = response.meta.get('date_str')
        page = response.meta.get("playwright_page")

        # Se ainda não iniciou o Playwright para esta URL, reinicia a si mesmo com ele
        if not page:
            yield scrapy.Request(
                url=response.url,
                callback=self.parse,
                meta={
                    'keyword': keyword,
                    'date_str': date_str,
                    'playwright': True,
                    'playwright_include_page': True,
                },
                dont_filter=True
            )
            return

        try:
            current_p = 1
            while True:
                # Espera os links carregarem
                try:
                    await page.wait_for_selector(".headline", timeout=10000)
                except:
                    self.logger.info(f"Sem resultados para {keyword} em {date_str}")
                    break

                # Extrai links da página atual
                content = await page.content()
                sel = scrapy.Selector(text=content)
                links = sel.css('.headline::attr(href)').getall()
                
                self.logger.info(f"[PROCESSO] {date_str} | Pág {current_p} | Links: {len(links)}")

                for link in links:
                    yield response.follow(link, callback=self.parse_item, meta={'keyword': keyword})

                # Verificação de paginação (Lógica do .cancel)
                # Se o botão de 'Próximo' NÃO tiver a classe 'cancel', a gente clica.
                next_btn = await page.query_selector('.arrow.right:not(.cancel)')
                
                if next_btn:
                    first_link_before = links[0] if links else ""
                    
                    await next_btn.click()
                    await page.wait_for_timeout(3000) # Espera o JS trocar os dados
                    
                    # Validação de troca de página
                    new_content = await page.content()
                    new_sel = scrapy.Selector(text=new_content)
                    first_link_after = new_sel.css('.headline::attr(href)').get()
                    
                    if first_link_before == first_link_after:
                        break # Página não mudou, encerra o dia
                    
                    current_p += 1
                else:
                    # Botão com classe .cancel ou inexistente: fim do dia.
                    break
        finally:
            await page.close()

    def parse_item(self, response):
        item = CrawlerItem()
        all_paragraphs = response.css('#content p::text, p em::text, p a::text, p strong::text').getall()
        full_text = ' '.join([p for p in all_paragraphs if not re.search(r'publicidade', p, re.I)])
        
        validate = validate_article(full_text)
        if validate:
            item['title'] = response.css('h1::text').get()
            item['article'] = full_text
            item['keyword'] = response.meta.get('keyword')
            raw_date = response.css('time::text').get()
            date = raw_date[:10] if raw_date else ""
            item['publication_date'] = date
            item['last_update'] = date
            item['acquisition_date'] = datetime.now(pytz.timezone('America/Sao_Paulo')).strftime(r'%d-%m-%Y')
            item['accepted_by'] = validate
            item['newspaper'] = 'Estadão'
            item['gangs'] = search_gangs(full_text)
            item['tags'] = search_tags(full_text)

        item['url'] = response.url

        yield item