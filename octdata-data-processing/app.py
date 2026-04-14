import warnings
warnings.filterwarnings('ignore')

from modules.processing import TransformData
from modules.convert import ConvertFormat
from modules.menu import Menu
from modules.connection import ConnectMongoSSH
from modules.reado import ReadOnly

# Módulo principal. Tentar fazer interface de gerar relatório de notícias/portal e palavras-chave mais incidentes de cada portal.

class App:
    def __init__(self):
        self.server = ConnectMongoSSH()
        self.server = self.server._connect_to_ssh()
        self.server.start()
        
        self.worker = TransformData()
        self.read = ReadOnly()
        self.convert = ConvertFormat()
        self.the_menu = Menu()
        
        self.commands = {
            '1': self.worker.remove_date_blank_space,
            '2': self.worker.cvt_timestampz_to_date,
            '3': self.worker.cvt_inverted_date,
            '4': self.worker.string_date_processing,
            '5': self.worker.set_documents_id_event,
            '6': self.worker.update_newspaper_name,
            '7': self.worker.merge_unaccepted_collections,
            '8' : self.worker.setAttribute,
            '9' : True
        }

        self.readoptions = {
            '1' : self.read.generate_news_report,
            '2' : self.convert.cvt_csv_to_ods,
            '3': True
        }
        
        print("\n---------- Controle de dados MongoDB -----------")
        
        self.menu()
                    
    def menu(self):
        while(True):
            self.the_menu.menu_processing()
            option = input()

            if option == "0":
                print("Encerrando. © Lucas Santos Soares | UFG")
                break

            elif option in self.commands:
                if option == "9":
                    self.the_menu.menu_read_only()
                    opcao = input()

                    if opcao in self.readoptions:
                        if opcao == "3":
                            pass
                        elif opcao == "0":
                            break
                        else:
                            self.readoptions.get(f"{opcao}")()
                    else:
                        print("[ERRO] Opção inválida. Retornando...")
                else:        
                    self.the_menu.care_menu()
                    self.commands.get(f"{option}")()
            else:
                print("[ERRO] Opção inválida. Tente novamente")
            
if __name__ == "__main__":
    execute = App()
