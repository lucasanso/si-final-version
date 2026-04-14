import scrapy
import pytz
from datetime import datetime
from ..keywords import KEYWORDS
from ..items import CrawlerItem 
from ..utils import (
    search_gangs, 
    validate_article, 
    get_processed_kwords,
    save_processed_kword
)
from base_spider import BaseSpider

class CartaSpider(BaseSpider):
    """
    Spider para extração de notícias do portal CartaCapital.
    
    Este spider é otimizado para lidar com a estrutura de busca e paginação do WordPress,
    além de extrair metadados técnicos (datas e tags) diretamente das meta tags de SEO 
    da página, garantindo maior precisão cronológica.
    
    Notes:
        Conforme observado no desenvolvimento, o portal não possui registros indexados 
        para os anos de 2009, 2010 e 2011.
    """
    name = 'carta'
    allowed_domains = ['cartacapital.com.br']
    
    # Template para busca via query string. O WordPress utiliza o parâmetro ?s=
    BASE_SEARCH_URL = 'https://www.cartacapital.com.br/page/{page}/?s={keyword}'
    FIRST_PAGE = 1

    def start_requests(self):
        # Carrega todas as palavras-chave possíveis
        all_terms = KEYWORDS['GANGS'] + KEYWORDS['ORGANIZED CRIME']
        
        # Carrega as palavras que já foram totalmente processadas para este spider
        processed_terms = get_processed_kwords(self.name)
        
        # Filtra: só processa o que NÃO está na lista de processadas
        search_terms = [term for term in all_terms if term not in processed_terms]
        
        self.logger.info(f'[STATUS] Total: {len(all_terms)} | Já processadas: {len(processed_terms)} | Restantes: {len(search_terms)}')

        for keyword in search_terms:
            self.logger.info(f'[PROCESSO] Iniciando palavra-chave: {keyword}')
            url = self.format_url(keyword, self.FIRST_PAGE)
            yield scrapy.Request(
                url, 
                meta={'keyword': keyword, 'page': self.FIRST_PAGE},
                callback=self.parse
            )

    def format_url(self, keyword, page):
        """
        Gera a URL de busca formatada para uma palavra-chave e página específica.

        Args:
            keyword (str): O termo de busca a ser pesquisado.
            page (int): O número da página de resultados.

        Returns:
            str: URL completa com o termo de busca escapado para web.
        """
        return self.BASE_SEARCH_URL.format(
            keyword=keyword.replace(' ', '+'), 
            page=page
        )

    def parse(self, response):
        keyword = response.meta['keyword']
        current_page = response.meta['page']

        news_urls = response.css('a.l-list__item::attr(href)').getall()
        for url in news_urls:
            yield scrapy.Request(
                url, 
                meta={'keyword': keyword}, 
                callback=self.parse_item
            )

        # Paginação
        has_next = response.xpath('//span[text()="Próxima"]').get()
        if has_next:
            next_page = current_page + 1
            yield scrapy.Request(
                self.format_url(keyword, next_page),
                meta={'keyword': keyword, 'page': next_page},
                callback=self.parse
            )
        else:
            # Ao chegar na última página, marca a keyword como concluída
            self.logger.info(f'[SUCESSO] Palavra-chave "{keyword}" finalizada.')
            save_processed_kword(keyword, self.name)

    def parse_item(self, response):
        item = CrawlerItem() 
        title = response.css('h1::text').get()
        
        article_body = response.css('.content-closed.contentOpen p::text, .content-closed.contentOpen a::text, p > strong::text, span.s1::text').getall()

        if not article_body:
            return

        full_text = ' '.join(article_body).strip()
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
        """
        Converte strings de data no formato ISO 8601 para o padrão brasileiro dd-mm-aaaa.

        Args:
            iso_date (str | None): String de data original (ex: '2023-10-27T14:30:00-03:00').

        Returns:
            str | None: Data formatada ou None em caso de entrada inválida ou erro de conversão.
            
        Notes:
            Utiliza o método 'fromisoformat' nativo do datetime, sendo resiliente a 
            falhas de tipagem ou valores nulos vindos das meta tags.
        """
        if not iso_date:
            return None
        try:
            return datetime.fromisoformat(iso_date).strftime('%d-%m-%Y')
        except (ValueError, TypeError):
            return None