from abc import ABC, abstractmethod
import scrapy

class BaseSpider(scrapy.Spider, ABC):
    @abstractmethod
    def start_requests(self, spider: scrapy.Spider):
        """
        Método chamado automaticamente pelo scrapy.

        Args:
            spider(scrapy.Spider): Bot em execução.

        Yields:

        Note:
            
        """
        ...

    @abstractmethod
    def parse(self, spider: scrapy.Spider, response: scrapy.http.Response):
        """
        Método chamado automaticamente pelo scrapy. Realiza a inserção de cada URL encontrada numa lista.

        Args:
            spider(scrapy.Spider): Bot em execução.
            response(scrapy.http.Response): Resposta da URL pesquisada com a palavra-chave.

        Yields:

        Note:

        """
        ...

    @abstractmethod    
    def parse_item(self, spider):
        """
        Método 

        Args:

        Yields:

        Note:
        
        """
        ...
