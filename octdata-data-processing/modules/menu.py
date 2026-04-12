import sys
from time import sleep

class Menu:
    def __init__(self):
        pass

    def msg(self):
        print(
            "\nQual operação deseja realizar?\n\n"
            "1. Retirar espaço em branco de determinado campo do JSON.\n"
            "2. Formatar data TIMESTAMPZ para ISO.\n"
            "3. Formatar data ISO invertido para ISO.\n"
            "4. Formatar data 'DD de MM de YYYY' para 'DD-MM-YYYY'.\n" 
            "5. Inserir índice 'id_event' em documentos.\n"
            "6. Atualizar nome de um portal.\n"
            "7. Mover urls de um portal para outro.\n"
            "8. Próximo menu.\n"
            "9. Settando\n"
            "0. Encerrar o programa."
        )

    def menu_read_only(self):
        print(
            "\nQual operação deseja realizar?\n\n"
            "1. Obter relatório de notícias/ano.\n"
            "2. Gerar backup da coleção newsData.\n"
            "3. Gerar backup da coleção unacceptedData.\n"
            "4. Converter arquivo .csv\n"
            "5. Menu anterior.\n"
            "0. Encerrar o programa."
        )

    def care_menu(self):
        while True:
            option = input("[AVISO] Esta operação interagirá diretamente com os dados do banco, tem certeza de que deseja prosseguir?\n[s/n]\n")

            if option == 's' or option == 'S':
                return True
            
            elif option == 'n' or option == 'N':
                return False
            
            else:
                print("[ERRO] Opção inválida. Tente novamente." )
