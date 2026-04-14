import scrapy
from ..items import CrawlerItem
from datetime import datetime, timedelta
import re
import pytz
from ..keywords import KEYWORDS
from ..settings import YEARS
from ..utils import (
    search_gangs, 
    search_tags, 
    validate_article, 
    get_processed_kwords, 
    save_processed_kword
)
from base_spider import BaseSpider

class FolhaSpider(BaseSpider):
    """
    Spider para extração de notícias históricas do jornal Folha de S.Paulo.
    Utiliza o sistema de busca interna do portal para filtrar por períodos específicos.
    """
    name = "folha"
    allowed_domains = ["search.folha.uol.com.br", "www1.folha.uol.com.br"] 
    
    # Template de URL para busca personalizada por data
    SEARCH_PAGE_URL = "https://search.folha.uol.com.br/search?q={}&periodo=personalizado&sd={:02d}%2F{:02d}%2F{}&ed={:02d}%2F{:02d}%2F{}&site=todos"

    def __init__(self, **kwargs):
        """
        Inicializa o Spider e carrega o estado de progresso das palavras-chave.

        Args:
            **kwargs: Argumentos arbitrários passados via CLI.
        
        Notes:
            Recupera através da utilidade 'get_processed_kwords' os termos que já 
            foram finalizados em execuções anteriores para evitar duplicidade.
        """
        super().__init__(**kwargs)
        self.processed_kwords = get_processed_kwords(self.name)

    def start_requests(self):
        palavras = KEYWORDS["GANGS"] + KEYWORDS["ORGANIZED CRIME"]
        anos = YEARS
        meses = [m for m in range(1, 13)]

        for p in palavras:
            if self.processed_kwords is None:
                print(f"[AVISO] Arquivo {self.name}_processed_kwords.yaml está vazio. Iniciando pela primeira palavra-chave: {p}")
            elif p in self.processed_kwords:
                print(f"[AVISO] Palavra-chave {p} já foi processada. Pulando...")
                continue
            else:
                print(f"[PROCESSO] Processando palavra-chave: {p}")

            for year in anos:
                for month in meses:
                    # Começa no dia 1 de cada mês
                    # date agora é um objeto que entende a lógica do calendário (dia 31 de fevereiro)
                    date = datetime(year, month, 1)
                        
                    # Itera enquanto estiver dentro do mesmo mês
                    while date.month == month:
                        # Formata a URL para o dia específico
                        url = self.SEARCH_PAGE_URL.format(
                            p, 
                            date.day, date.month, date.year,
                            date.day, date.month, date.year
                        )
                            
                            # Passamos a keyword via meta
                        yield scrapy.Request(
                            url=url, 
                            callback=self.parse, 
                            meta={
                                'keyword': p,
                                'url' : url
                                } 
                            )
                        date += timedelta(days=1)

            print(f"[SUCESSO] A palavra-chave {p} foi totalmente processada. Salvando...")
            save_processed_kword(p, self.name)

    # Método padrão scrapy: é chamado automaticamente; retorna um Item ou Request
    def parse(self, response):
        keyword = response.meta.get('keyword')
        links = response.css(".c-headline__content a::attr(href)").getall()

        for link in links:
            yield response.follow(link, callback=self.parse_item, meta={'keyword': keyword})

        # Se houver mais de uma página para o MESMO DIA, o Scrapy continua
        proxima_pagina = response.css(".c-pagination__item--next a::attr(href)").get()
        if proxima_pagina:
            yield response.follow(proxima_pagina, callback=self.parse, meta={'keyword': keyword})
    
    def parse_item(self, response):
        item = CrawlerItem()

        if response.css(".c-content-head__title::text").get():
            raw_title = response.css(".c-content-head__title::text").get()
            full_title = "".join(raw_title)
            title = re.sub(r'\\n', '', full_title).strip()
            item["title"] = title
            
            raw_article = response.css(".c-news__body p ::text").getall()
            full_text = " ".join(raw_article)
            article = re.sub(r'\n', '', full_text).strip()
            article = re.sub(r'\'', '', article)
            article = re.sub(r'Mais                              ', '', article)
            article = re.sub(r'                                     ', '', article)

            item["article"] = article
            item["keyword"] = response.meta.get("keyword") # Caso quisermos adicionar um segundo parâmetro, o segundo parâmetro terá o valor caso não obtivermos sucesso no get()


            raw_pub_date = (response.css("time.c-more-options__published-date::attr(datetime)").get())
            fmt_date =  datetime.strptime(raw_pub_date[:10], r'%Y-%m-%d').strftime(r'%d-%m-%Y')
            item["publication_date"] = fmt_date

            if response.css("time.c-more-options__modified-date::attr(datetime)").get():
                raw_up_date = response.css("time.c-more-options__modified-date::attr(datetime)").get()
                fmt_date = datetime.strptime(raw_up_date[:10], r'%Y-%m-%d').strftime(r'%d-%m-%Y')
                item["last_update"] = fmt_date
            else:
                item["last_update"] = fmt_date

            item["acquisition_date"] = datetime.now(pytz.timezone('America/Sao_Paulo')).strftime(r'%d-%m-%Y') 
            item["newspaper"] = "FolhaSP"
            item["url"] = response.url
            item["tags"] = search_tags(article)
            item["accepted_by"] = validate_article(article) 
            item["gangs"] = search_gangs(article)
            item["manual_relevance_class"] = None 
            item["id_event"] = None
        
        elif response.css('[itemprop="headline"]').get():
            item['title'] = str(response.css('[itemprop="headline"]::text').get()).strip()

            raw_article = response.css('[class="content"] > p::text').getall()
            article = ""

            for line in raw_article:
                if re.findall(r'www', line):
                    continue

                article = article + " " + str(line).strip()

            item['article'] = article

            item['keyword'] = response.meta.get('keyword')

            publication_date = str(response.css('.author ~ time::attr(datetime)').get())[:10].strip()
            item['accepted_by'] = validate_article(article)
            item['publication_date'] = str(publication_date).strip()
            item['acquisition_date'] = datetime.now(pytz.timezone('America/Sao_Paulo')).strftime(r'%d-%m-%Y')
            item['last_update'] = str(publication_date).strip()
            item['newspaper'] = "Folha de São Paulo" 
            item['url'] = response.url
            item['tags'] = search_tags(article)
            item['gangs'] = search_gangs(article)
            item['manual_relevance_class'] = None
        elif response.css('#articleNew'):
            item['title'] = str(response.css('h1::text')[1].get()).strip()
            article = ""

            raw_article = response.css('#articleNew > p::text').getall()

            for line in raw_article:
                article = article + " " + str(line).strip( )

            item['article'] = article
            item['keyword'] = response.meta.get('keyword')

            publication_date = str(response.css('#articleDate::text')[1].get()).strip()
            item['accepted_by'] = validate_article(article)
            item['publication_date'] = publication_date
            item['acquisition_date'] = datetime.now(pytz.timezone('America/Sao_Paulo')).strftime(r'%d-%m-%Y')
            item['last_update'] = publication_date
            item['newspaper'] = "FolhaSP" 
            item['url'] = response.url
            item['tags'] = search_tags(article)
            item['gangs'] = search_gangs(article)
            item['manual_relevance_class'] = None

        yield item

    def variate_publication_date(self, response):
        """
        Tenta extrair a data de publicação em diferentes seletores CSS 
        devido à inconsistência de layouts da Folha.

        Args:
            response (scrapy.http.Response): A resposta da página da notícia.

        Returns:
            str | None: O texto da data se encontrado, ou None caso os seletores falhem.
        
        Notes:
            Esta é uma função de fallback para casos onde o seletor principal 
            do 'parse_item' não captura o metadado de tempo.
        """
        if response.css('header [datetime*="-"]::text').getall()[1]:
            return response.css('header [datetime*="-"]::text').getall()[1]
        elif response.css('[datetime*="-"]::text').getall()[0]:
            return response.css('[datetime*="-"]::text').getall()[0]
        else:
            print("[AVISO] A data está em formato diferente")
            return None