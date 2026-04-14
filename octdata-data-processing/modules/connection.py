"""
Módulo de Infraestrutura e Conectividade - MongoDB via SSH

Este módulo fornece as ferramentas necessárias para estabelecer uma conexão 
segura com um banco de dados MongoDB hospedado em um servidor remoto, 
utilizando SSH Tunneling para contornar restrições de firewall.
"""

from sshtunnel import open_tunnel
from pymongo import MongoClient
import yaml
import logging
from modules.settings import COLLECTIONS

# Configuração de Logging: Registra erros e eventos importantes em 'logs/process.log'
logging.basicConfig(
    level=logging.INFO, 
    filename="logs/process.log", 
    format="%(asctime)s - %(levelname)s - %(message)s"
)

# --- Carregamento de Configurações Globais ---
try:
    with open("config.yaml", "r") as f:
        configs = yaml.safe_load(f)
        print("[SUCESSO] Arquivo .yaml foi lido com sucesso")

        # Extração de dicionários de configuração para uso posterior
        mongodb_configs = configs["mongodb_lamcad"]
        ssh_configs = configs["lamcad"]
        db = mongodb_configs["database"]

except FileNotFoundError as e:
    print(f"[ERRO] Não foi possível encontrar arquivo .yaml")
    logging.error(f"Erro ao carregar config.yaml: {e}")
except KeyError as e:
    print(f"[ERRO] Chave de configuração ausente no YAML: {e}")
    logging.error(f"Chave ausente: {e}")


class ConnectMongoSSH:
    """
    Gerenciador de conexões híbridas (SSH + MongoDB).
    
    Esta classe encapsula a lógica de criação de túneis SSH e instanciação 
    do cliente MongoDB, permitindo operações em bancos de dados remotos 
    como se fossem locais.

    Attributes:
        collections (list): Lista de nomes de coleções válidas importadas de settings.
        client (MongoClient): Instância do cliente MongoDB após conexão.
        server (SSHTunnelForwarder): Instância do túnel SSH ativo.
    """

    def __init__(self):
        """
        Inicializa a classe carregando a lista de coleções permitidas.
        """
        self.collections = COLLECTIONS
        self.client = None
        self.server = None

    def _connect_to_mongo(self):
        """
        Estabelece a conexão com o cliente MongoDB e seleciona a coleção.

        O método solicita via console a coleção desejada e valida se ela 
        está presente na lista de coleções permitidas (self.collections).

        Returns:
            pymongo.collection.Collection: Objeto da coleção selecionada para consulta/inserção.
        
        Raises:
            Exception: Caso ocorra erro na string de conexão ou falha de autenticação.
        """
        print("[PROCESSO] Iniciando conexão com o MongoDB")
        connection_string = mongodb_configs["uri"]

        try:
            self.client = MongoClient(connection_string)
            
            valid = True
            while valid:
                collection = input("[AVISO] Digite a coleção que deseja acessar no MongoDB:\n")

                if collection in self.collections:
                    print(f"[SUCESSO] A coleção [{collection}] foi encontrada.")
                    valid = False
                else:
                    print("[ERRO] A coleção digitada não existe.")
            
            print(f"[SUCESSO] Conexão com o MongoDB estabelecida")
            return self.client.get_database(db).get_collection(collection)

        except Exception as e:
            print(f"[ERRO] Falha ao conectar ao MongoDB: {e}")
            logging.error(f"MongoDB Connection Error: {e}")
            raise

    def _connect_to_ssh(self):
        """
        Abre um túnel SSH (Port Forwarding) para o servidor remoto.

        Utiliza as configurações lidas do YAML para mapear uma porta local 
        para a porta do MongoDB no servidor remoto.

        Returns:
            sshtunnel.SSHTunnelForwarder: O objeto do túnel em estado 'started'.
        
        Note:
            É fundamental que as chaves 'local_bind_port' e 'remote_bind_port' 
            estejam sincronizadas com a URI do MongoDB no arquivo config.
        """
        SERVER = (ssh_configs["server_ip"], ssh_configs["server_port"])

        try:
            print("[PROCESSO] Iniciando conexão SSH")
            self.server = open_tunnel(
                SERVER,
                ssh_username=ssh_configs["ssh_username"],
                ssh_password=ssh_configs["ssh_password"],
                remote_bind_address=(ssh_configs["remote_bind_ip"], ssh_configs["remote_bind_port"]),
                local_bind_address=(ssh_configs["local_bind_ip"], ssh_configs["local_bind_port"])
            )
            self.server.start() # Inicia explicitamente o túnel
            print("[SUCESSO] Conexão SSH estabelecida")

            return self.server

        except Exception as e:
            print(f"[ERRO] Falha na conexão SSH: {e}")
            logging.error(f"SSH Tunnel Error: {e}")
            raise
        
    def _close_connection(self, connection) -> None:
        """
        Encerra de forma segura a conexão com o MongoDB ou o túnel SSH.

        Args:
            connection: O objeto de conexão (client ou server) a ser fechado.
        """
        if connection:
            connection.close()
            print("[AVISO] A Conexão foi encerrada com sucesso.")