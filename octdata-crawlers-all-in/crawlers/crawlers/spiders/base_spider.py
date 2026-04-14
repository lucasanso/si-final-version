from abc import ABC, abstractmethod
import scrapy

class BaseSpider(scrapy.Spider, ABC):
    """
    Classe Base Abstrata para padronização de Spiders.
    Define a interface obrigatória para a navegação e extração de dados.
    """

    @abstractmethod
    def start_requests(self):
        """
        Ponto de entrada do Scrapy. Inicializa o template da URL de busca.

        Args:
            Nenhum argumento direto além da instância da classe.

        Yields:
            scrapy.Request: Requisições iniciais formatadas com as palavras-chave 
                            e filtros de data para a página de busca do jornal.

        Note:
            Este método deve gerenciar a lógica de iteração sobre a lista de keywords
            e o controle de termos já processados para evitar duplicidade.
        """
        ...

    @abstractmethod
    def parse(self, response: scrapy.http.Response):
        """
        Processa a página de resultados da busca e extrai os links das notícias.

        Args:
            response (scrapy.http.Response): O objeto de resposta contendo o HTML 
                                             da página de resultados da pesquisa.

        Yields:
            scrapy.Request: Requisições para as URLs individuais de cada notícia encontrada.
            
        Note:
            Além de extrair os links das notícias, este método é geralmente responsável 
            por identificar o botão de 'Próxima Página' e realizar a paginação recursiva.
        """
        ...

    @abstractmethod    
    def parse_item(self, response: scrapy.http.Response):
        """
        Extrai as informações detalhadas de dentro de uma notícia específica.

        Args:
            response (scrapy.http.Response): O objeto de resposta da página da notícia.

        Yields:
            CrawlerItem: O objeto final populado com os dados extraídos (título, texto, data, etc.).

        Note:
            Utiliza seletores CSS ou XPath específicos do portal para minerar o 
            corpo do texto, metadados de publicação e realizar a limpeza dos dados.
        """
        ...