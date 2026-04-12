import scrapy
import pytz
from datetime import datetime
from ..keywords import KEYWORDS
from ..items import CrawlerItem 
from ..utils import validate_article, search_gangs, save_processed_kword

class CartaSpider(scrapy.Spider):
    """
    Característica: não existem notícias dos anos 2009, 2010 e 2011.
    """
    name = 'carta'
    allowed_domains = ['cartacapital.com.br']
    
    # Configurações extraídas da antiga PortalInterface
    BASE_SEARCH_URL = 'https://www.cartacapital.com.br/page/{page}/?s={keyword}'
    FIRST_PAGE = 1

    def start_requests(self):
        search_terms = KEYWORDS ['GANGS'] + KEYWORDS['ORGANIZED CRIME']
        
        for keyword in search_terms:
            self.logger.info(f'[PROCESSO] Processando palavra-chave: {keyword}')
            url = self.format_url(keyword, self.FIRST_PAGE)
            yield scrapy.Request(
                url, 
                meta={'keyword': keyword, 'page': self.FIRST_PAGE},
                callback=self.parse
            )

    def format_url(self, keyword, page):
        """Substitui o antigo build_search_url"""
        return self.BASE_SEARCH_URL.format(
            keyword=keyword.replace(' ', '+'), 
            page=page
        )

    def parse(self, response):
        keyword = response.meta['keyword']
        current_page = response.meta['page']

        # 1. Extrai links das notícias na listagem
        news_urls = response.css('a.l-list__item::attr(href)').getall()
        for url in news_urls:
            yield scrapy.Request(
                url, 
                meta={'keyword': keyword}, 
                callback=self.parse_news
            )

        # 2. Paginação: verifica se existe o botão "Próxima"
        has_next = response.xpath('//span[text()="Próxima"]').get()
        if has_next:
            next_page = current_page + 1
            yield scrapy.Request(
                self.format_url(keyword, next_page),
                meta={'keyword': keyword, 'page': next_page},
                callback=self.parse
            )
        else:
            print(f'[AVISO] Palavra-chave {keyword} finalizada. Salvando.')
            save_processed_kword(keyword, self.name)

    def parse_news(self, response):
        # Extração de dados (lógica do antigo parse_news da CartaCapital)
        item = CrawlerItem() 
        title = response.css('h1::text').get()
        
        # O seletor 'section.contentsingle' captura o corpo do texto
        article_body = response.css('.content-closed.contentOpen p::text, .content-closed.contentOpen a::text, p > strong::text,  span.s1::text').getall()

        # Validação de Paywall simples (se não tem subtítulo, geralmente está bloqueado)
        if not article_body:
            return

        full_text = ' '.join(article_body).strip()

        # Aqui entraa lógica de validação externa
        accepted = validate_article(full_text)

        if accepted:
            
            tz_sp = pytz.timezone('America/Sao_Paulo')
            now = datetime.now(tz_sp)
            
            pub_date_raw = response.css("meta[property='article:published_time']::attr(content)").get()
            mod_date_raw = response.css("meta[property='article:modified_time']::attr(content)").get()

            item['keyword'] = response.meta['keyword']
            item['acquisition_date'] = now.strftime('%d-%m-%Y')
            item['publication_date'] = self.format_date(pub_date_raw)
            item['accepted_by'] = accepted
            item['last_update'] = self.format_date(mod_date_raw) or item['publication_date']
            
            item['newspaper'] = 'CartaCapital'
            item['title'] = title.strip() if title else ""
            item['article'] = full_text
            
            tags = response.css("meta[property='article:tag']::attr(content)").getall()
            section = response.css("meta[property='article:section']::attr(content)").get()
            item['tags'] = tags + [section] if section else tags
            
            item['url'] = response.url
            item['gangs'] = search_gangs(item['title'] + " " + item['article'])
            item['manual_relevance_class'] = None
        else:
            item['url'] = response.url
        
        yield item

    def format_date(self, iso_date):
        """Auxiliar para formatar datas ISO vindas das meta tags"""
        if not iso_date:
            return None
        try:
            return datetime.fromisoformat(iso_date).strftime('%d-%m-%Y')
        except ValueError:
            return None