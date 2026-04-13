from sshtunnel import open_tunnel
import pymongo 
import sys
import yaml
from .items import CrawlerItem
from datetime import datetime
from .keywords import KEYWORDS
import scrapy

try:
    with open('config.yaml', 'r') as configs_file:
        configs = yaml.safe_load(configs_file)
        print("[SUCESSO] Arquivo .yaml de configurações foi lido com sucesso")

except FileNotFoundError as e:
    print(f"[ERRO] Não foi possível encontrar o arquivo config.yaml {e}")

    sys.exit(1)

class CrawlersPipeline:
    """
    Classe responsável pelas conexões SSH e cliente do MongoDB para realizar inserção de notícias, envio de email e logs automatizados.
    """
    def __init__(self) -> None:
        self.accepted = 0
        self.unaccepted = 0
        self.mongodb_uri = configs['mongodb_lamcad']['uri']
        self.mongodb_database = configs['mongodb_lamcad']['database']
        self.mongodb_accepted_news_collection = configs['mongodb_lamcad']['accepted_news_collection']
        self.mongodb_unaccepted_news_collection = configs['mongodb_lamcad']['unaccepted_news_collection']
        self.newsLogs = configs['mongodb_lamcad']['logs_collection']
        self.all = [""]

        self.server = None
        self.client = None

    def open_spider(self, spider: scrapy.Spider) -> None:
        """
        Método chamado automaticamente pelo scrapy.

        Args:
            spider(scrapy.Spider): Bot em execução.
        """
        print(f'[PROCESSO] Iniciando bot de extração: {spider.name}')
        lamcad_configs = configs['lamcad']
        try:
            self.server = open_tunnel(
                (lamcad_configs['server_ip'], lamcad_configs['server_port']),
                ssh_username=lamcad_configs['ssh_username'],
                ssh_password=lamcad_configs['ssh_password'],
                local_bind_address=(lamcad_configs['local_bind_ip'], lamcad_configs['local_bind_port']),
                remote_bind_address=(lamcad_configs['remote_bind_ip'], lamcad_configs['remote_bind_port'])
            )
            self.server.start()
            spider.logger.info(
                f"[SUCESSO] Conexão com o LamCAD criada com o seguinte IP e porta: {self.server.local_bind_address}")

            self.client = pymongo.MongoClient(self.mongodb_uri)
            database = self.client[self.mongodb_database]
            self.accepted_news_collection = database[self.mongodb_accepted_news_collection]
            self.unaccepted_news_collection = database[self.mongodb_unaccepted_news_collection]
            self.newsLogs_collection = database[self.newsLogs]

            self.all = self.get_all_urls()

        except Exception as e:
            spider.logger.error(f"[ERRO] Erro crítico ao conectar no banco ou SSH: {e}")
            
    def close_spider(self, spider: scrapy.Spider) -> None:
        """
        Método que é chamado automaticamente pelo scrapy no momento em que encerra-se a extração.
        
        Args:
            spider(scrapy.Spider): Bot em execução.

        Note:
            Uma extração pode ser finalizada ou interrompida.

            Finalizada: Todas as palavras-chave foram processadas.

            Interrompida: O responsável pela execução do código pressionou CTRL + C. 
        """
        print("[AVISO] Encerrando extração.")

        self.generate_log(spider.name)

        if self.client:
            self.client.close()
        if self.server:
            self.server.stop()

    def process_item(self, item: CrawlerItem, spider: scrapy.Spider) -> None:
        """
        Orquestra o fluxo de persistência de um item extraído.

        Realiza a deduplicação via URL, diferencia notícias aceitas/não aceitas 
        com base nas palavras-chave e incrementa os contadores da sessão.

        Args:
            item (CrawlerItem): Objeto contendo os dados estruturados da notícia.
            spider (scrapy.Spider): Bot em execução.

        Note:
            A deduplicação é feita consultando o conjunto 'self.all' carregado no início da execução.
        """
        self.data = dict(CrawlerItem(item))
        
        if self.data.get("url") not in self.all:
            if self.data.get("accepted_by"):
                spider.logger.info(f"[SUCESSO] Inserindo URL {self.data.get('url')} aceita")
                
                self.data['id_event'] = self.get_next_id_event()
                self.accepted_news_collection.insert_one(self.data)
                self.accepted += 1

            else:
                url = {'url' : self.data.get('url')}
                spider.logger.info(f"[AVISO] URL {self.data.get('url')} não aceita sendo inserida")

                self.unaccepted_news_collection.insert_one(url)
                self.unaccepted += 1

            self.all.add(self.data.get("url"))

        elif self.data.get('url') is None:
            print(f"[AVISO] A notícia possui formatação totalmente diferente.")
        
        else:
            print(f'[AVISO] {self.data['url']} já está no banco. Pulando...')

    def get_all_urls(self) -> set:
        """
        Obtém todas as notícias percorridas do banco para lógica de deduplicação.

        Returns:
            set: Retorna um conjunto (set) contendo todas as URLs. (Comparação O(1))
        """
        all_seen_urls = []

        try:
            print('[PROCESSO] Carregando notícias aceitas...') 
            accepted_urls = [doc['url'] for doc in self.accepted_news_collection.find({}, {'url': 1})]
            all_seen_urls.extend(accepted_urls)

            print(f"[SUCESSO] Quantidade total de notícias aceitas: {len(all_seen_urls)}")
            
            print(f'[PROCESSO] Carregando todas as notícias...')
            unaccepted_urls = [doc['url'] for doc in self.unaccepted_news_collection.find({}, {'url': 1})]
            all_seen_urls.extend(unaccepted_urls)
            
            print(f"[SUCESSO] Quantidade total de notícias vistas: {len(all_seen_urls)}")
            
            return set(all_seen_urls)
        except Exception as e:
            print(f'[ERRO] Erro ao obter as notícias do banco {e}')
    
    def generate_log(self, spider: scrapy.Spider, log_on: bool = False) -> dict:
        """
        Registra o log de extração no MongoDB.

        Args:
            spider(scrapy.Spider): Bot que está executando uma extração de notícias.
            save(bool): Se True, será habilitado o salvamento do log da extração na coleção newsLogs.
        Returns:
            dict: Retorna o log formatado em dicionário.
        Note:
            É settado como False por padrão.
        """
        if log_on:
            print('[AVISO] Salvando log no banco...')
            try:
                spider_name = spider.name if hasattr(spider, 'name') else spider
                with open(f'kwords-processing/{spider_name}_processed_kwords.yaml', 'r') as file:
                    processed = [str(k).strip() for k in list(file)]
                    remaining = [k for k in KEYWORDS['GANGS'] + KEYWORDS['ORGANIZED CRIME'] if k not in processed]

                    log = {
                        'bot_name': spider_name,
                        'extraction_endtime' : datetime.now(),
                        'num_accepted' : self.accepted,
                        'num_unaccepted' : self.unaccepted,
                        'last_year' : self.data.get('publication_date'),
                        'last_keyword' : self.data.get('keyword'),
                        'processed_keywords' : [k for k in processed],
                        'remaining_keywords': [k for k in remaining]
                    }

                self.newsLogs_collection.insert_one(log)

                return log
            except Exception as e:
                print(f'[ERRO] Erro ao salvar log: {e}')

    def get_next_id_event(self) -> int: 
        """
        Retorna o id_event da última notícia da coleção de notícias aceitas do banco.

        Caso a coleção esteja vazia, retorna 1.

        Returns:
            int: id_event da última notícia da coleção newsData
        """
        last_record = self.accepted_news_collection.find_one(sort=[('id_event', -1)])
        
        if last_record and 'id_event' in last_record:
            return last_record['id_event'] + 1
            
        return 1 