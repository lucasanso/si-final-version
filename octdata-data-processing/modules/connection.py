from sshtunnel import open_tunnel
from pymongo import MongoClient
import yaml
import logging
from modules.settings import COLLECTIONS

logging.basicConfig(level=logging.INFO, filename="logs/process.log", format="%(asctime)s - %(levelname)s - %(message)s")

try:
    with open("config.yaml", "r") as f:
        configs = yaml.safe_load(f)

        print("[SUCESSO] Arquivo .yaml foi lido com sucesso")

        mongodb_configs = configs["mongodb_lamcad"]
        ssh_configs = configs["lamcad"]
        db = mongodb_configs["database"]

except FileNotFoundError as e:
    print(f"[ERRO] Não foi possível encontrar arquivo .yaml")
    logging.error(f"{e}")

class ConnectMongoSSH:
    def __init__ (self):
        self.collections = COLLECTIONS
        pass

    def _connect_to_mongo(self):
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
            print(f"[ERRO] {e}")

    
    def _connect_to_ssh(self):
        SERVER = (ssh_configs["server_ip"], ssh_configs["server_port"])

        try:
            print("[PROCESSO] Iniciando conexão SSH")
            self.server = open_tunnel(
                SERVER,
                ssh_username =  ssh_configs["ssh_username"],
                ssh_password = ssh_configs["ssh_password"],
                remote_bind_address = (ssh_configs["remote_bind_ip"], ssh_configs["remote_bind_port"]),
                local_bind_address = (ssh_configs["local_bind_ip"], ssh_configs["local_bind_port"])
            )
            print("[SUCESSO] Conexão SSH estabelecida")

            return self.server

        except Exception as e:
            print(f"[ERRO] {e}")
        
    def _close_connection(self, connection) -> None:
        if connection:
            connection.close()
            print("[AVISO] A Conexão com o banco de dados foi encerrada")

