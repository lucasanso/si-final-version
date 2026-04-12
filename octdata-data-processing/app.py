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
        
        
        print("\n---------- Controle de dados MongoDB -----------")
        
        self.menu()
                    
    def menu(self):
        valid = True

        while(valid):
            self.the_menu.msg()
            variavel = input()

            match (variavel):
                case '1':
                    permission = self.the_menu.care_menu()
                    if permission:
                        self.worker.remove_date_blank_space()
                               
                case '2':
                    permission = self.the_menu.care_menu()

                    if permission:
                        self.worker.cvt_timestampz_to_date()

                case '3':
                    permission = self.the_menu.care_menu()

                    if permission:
                        self.worker.cvt_inverted_date()

                case '4':
                    permission = self.the_menu.care_menu()

                    if permission: 
                        self.worker.string_date_processing()
                case '5':
                    permission = self.the_menu.care_menu()

                    if permission:
                        self.worker.set_documents_id_event()

                case '6':
                    permission = self.the_menu.care_menu()

                    if permission:
                        self.worker.update_newspaper_name()

                case '7':
                    permission = self.the_menu.care_menu()

                    if permission:
                        self.worker.merge_unaccepted_collections()

                case '8': 
                    validR = True
                    self.the_menu.menu_read_only()

                    while validR:
                        options = input()

                        match(options):
                            case '1':
                                self.read.generate_news_report()
                                validR = False
                            case '2':
                                pass
                            case '3':
                                pass

                            case '4':
                                self.convert.cvt_csv_to_ods(input("[AVISO] Digite o diretório do arquivo .csv que deseja converter para .ods:\n"), input("[AVISO] Digite o nome que deseja salvar o novo arquivo.ods:\n"))

                            case '5':
                                validR = False
                                
                            case '0':
                                try:
                                    self.server.close()
                                    print("[AVISO] Conexão SSH finalizada")
                                except Exception as e:
                                    print(f"[ERRO] {e}")

                                print("Finalizando o programa. Obrigado por utilizar! © Lucas Santos Soares")
                                validR = False
                                valid = False
                            case _ :
                                print("[AVISO] Opção inválida, tente novamente.")
                case '9':
                    self.worker.setAttribute()
                
                case '0':
                    try:
                        self.server.close()
                        print("[AVISO] Conexão SSH finalizada")
                    except Exception as e:
                        print(f"[ERRO] {e}")
                    
                    print("Finalizando o programa. Obrigado por utilizar! © Lucas Santos Soares")
                    valid = False

                case _ :
                    print("[AVISO] Opção inválida, tente novamente.")

if __name__ == "__main__":
    execute = App()
