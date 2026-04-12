import pandas as pd
import logging
from datetime import date

class LoadData:
    def _load_csv(self, archive, name):
        try:
            print("[PROCESSO] Salvando informações")
            df = pd.DataFrame(archive)
        
            # A ordem de alcançar determinado diretório é da esquerda para a direita
            # Retirar esse diretório hard-code abaixo
            # Deve ser relativo ao código que executa
            df.to_csv(f"data/relatorios/{name}-{date.today()}.csv", index=False, header=False)

            print("[SUCESSO] As informações foram salvas")
            logging.info(f"Arquivo {name} foi salvo")
        except Exception as e:
            print("[ERRO] Não foi possível salvar as informações")
            logging.error(f"{e}")

    def _load_json(self, archive, name):
        pass

    def generate_backup(self):
        pass