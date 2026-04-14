from sshtunnel import open_tunnel
from pymongo import MongoClient
from time import sleep
import yaml
from params.keywords import SEARCH_KEYWORDS, VALIDATION_KEYWORDS, GROUP_KEYWORDS, GROUP_VALIDATION_KEYWORDS, ACTIONS_VALIDATION_KEYWORDS, ACTIONS_KEYWORDS
from modules.middlewares import DuplicatedUrls

try:
    with open ("config.yaml", "r") as f:
        configs = yaml.safe_load(f)

        ssh_configs = configs["lamcad"]
        mongo_db_configs = configs["mongodb_lamcad"]

        # ATENÇÃO: A coleção aqui é a testDB
        db = mongo_db_configs["database"]
        collection = mongo_db_configs["accepted_news_collection"]

except FileNotFoundError as e:
    print(f"[ERRO] {e}")

class ConnectionsDiario:
    """
    Gerencia o ciclo de vida das conexões de rede do projeto.
    
    Responsável por estabelecer o túnel SSH (Port Forwarding) e a conexão 
    com o cluster MongoDB, garantindo que o tráfego de dados seja criptografado 
    e seguro entre a máquina local e o servidor LAMCAD.
    """
    def __init__(self):
        """
        Inicializa a instância da classe de conexão.
        """
        pass
    
    def connect_ssh(self):
        """
        Estabelece um túnel SSH seguro para redirecionamento de porta.

        Utiliza as configurações lidas do YAML para mapear uma porta local 
        para o serviço do MongoDB no servidor remoto.

        Returns:
            sshtunnel.SSHTunnelForwarder: O objeto do servidor de túnel. 
                                          Requer chamada ao método .start() para ativar.
        
        Notes:
            O túnel é essencial quando o banco de dados MongoDB não está exposto 
            diretamente à internet por razões de segurança.
        """
        SERVER = (ssh_configs["server_ip"], ssh_configs["server_port"])
        LOCAL = (ssh_configs["local_bind_ip"], ssh_configs["local_bind_port"])
        REMOTE = (ssh_configs["remote_bind_ip"], ssh_configs["remote_bind_port"])

        self.server = open_tunnel (
            SERVER,
            ssh_username = ssh_configs["ssh_username"],
            ssh_password = ssh_configs["ssh_password"],
            remote_bind_address = REMOTE,
            local_bind_address = LOCAL
        )

        print("[SUCESSO] Conexão SSH estabelecida")
        return self.server

    def connect_mongodb(self):
        """
        Inicia o cliente de conexão com o banco de dados MongoDB.

        Returns:
            pymongo.MongoClient: Instância do cliente MongoDB pronta para 
                                 acessar bancos e coleções.
        
        Notes:
            A conexão deve ser realizada APÓS o início do túnel SSH para que 
            a URI aponte corretamente para a porta local mapeada.
        """
        connection_string = mongo_db_configs["uri"]
        self.client = MongoClient(connection_string)

        print("[SUCESSO] Conexão com o MongoDB estabelecida")
        return self.client
    
    def close_connection(self):
        """
        Realiza o fechamento gracioso (graceful shutdown) de todas as conexões.

        Encerra primeiro o cliente do banco de dados e, em seguida, interrompe 
        o túnel SSH para liberar as portas do sistema operacional.
        """
        if self.client:
            self.client.close()

        if self.server:
            self.server.stop()