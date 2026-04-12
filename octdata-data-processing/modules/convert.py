import time
import logging
import pandas as pd

# Módulo responsável por fazer conversão de formato de arquivo.

class ConvertFormat:
    def __init__(self):
        pass

    def cvt_csv_to_ods(self, dir, name):
        print(f"[PROCESSO] Iniciando conversão do arquivo .csv do diretório {dir} para {name}.ods")
        
        try:
            df = pd.read_csv(dir)
            print(f"[SUCESSO] O arquivo foi encontrado com sucesso no diretório {dir}. Convertendo...")
            time.sleep(3)

            df.to_excel(f'{name}.ods', engine='odf', index=False)

            print("[SUCESSO] O arquivo foi convertido com sucesso")
            logging.info(f"Arquivo {name} foi salvo em .ods")

        except Exception as e:
            print(f"[ERRO] {e}")
            logging.error(f"{e}")