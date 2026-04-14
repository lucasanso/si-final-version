from modules.settings import NOMES_PORTAIS, ANOS_A_PERCORRER
import logging
from modules.connection import ConnectMongoSSH
from modules.load import LoadData
import time

class ReadOnly:
    def __init__(self):
        self.news_portal_name = NOMES_PORTAIS
        self.years = ANOS_A_PERCORRER
        self.loader = LoadData()
        
    # Deixar função mais legível e entendível
    def generate_news_report(self) -> None:
        """
        Função que salva em .csv a quantidade de notícias/ano

        Args:
            name (str): Nome que deseja salvar o arquivo gerado
        """
        name = None
        connection = ConnectMongoSSH()
        cursor = connection._connect_to_mongo()

        print("[AVISO] O relatório será salvo na pasta 'data'")
        time.sleep(4)

        print("[PROCESSO] Iniciando obtenção de notícias por ano [.csv]")

        tupla_inicial = [(
                            "Portal",
                            "2009",
                            "2010",
                            "2011",
                            "2012",
                            "2013",
                            "2014",
                            "2015",
                            "2016",
                            "2017",
                            "2018",
                            "2019",
                            "2020",
                            "2021",
                            "2022",
                            "2023",
                            "2024",
                            "2025",
                            "2026",
                            "Total de notícias extraídas do portal"                              
                            ),]
        
        try:
            for i in range (len(self.news_portal_name)):
                print(f"[PROCESSO] Percorrendo portal {self.news_portal_name[i]}")
                counter = cursor.count_documents(
                    {'newspaper' : self.news_portal_name[i]}
                )
            
                relevant = 0
                not_relevant = 0
                doubt = 0
                n_classificadas = 0


                counter_totais = ()
                counter_relevantes = ()
                counter_n_relevantes = ()
                counter_doubt = ()
                counter_n_classificadas = ()

                tupla_info = (self.news_portal_name[i],)
                tupla_relevance = (f'Classificadas como relevantes [1]',)
                tupla_not_relevance = (f'Classificadas como não relevantes [0]',)
                tupla_doubt = (f'Classificadas como dúvida [2]',)
                tupla_n_classificadas = (f'Não classificadas',)

                for y in self.years:
                    year_query = {'$regex': f'{y}'}
                    query = {
                    'newspaper': self.news_portal_name[i],
                    'publication_date' : year_query
                    }
                    
                    manual_relevance = {
                        'newspaper': self.news_portal_name[i],
                        'publication_date' : year_query,
                        'manual_relevance_class' : 1
                    }

                    manual_relevance_doubt = {
                        'newspaper' : self.news_portal_name[i],
                        'publication_date' : year_query,
                        'manual_relevance_class' : 2
                    }
                    
                    manual_relevance_not = {
                        'newspaper': self.news_portal_name[i],
                        'publication_date' : year_query,
                        'manual_relevance_class' : 0
                    }


                    # Não tá mapeando as notícias que tem 'manual_relevance_class' como null
                    manual_relevance_false = {
                        'newspaper' : self.news_portal_name[i],
                        'publication_date' : year_query,
                        'manual_relevance_class' : None 
                    }

                    counter_totais = counter_totais + (cursor.count_documents(query),)
                    counter_relevantes = counter_relevantes + (cursor.count_documents(manual_relevance),)
                    counter_n_relevantes = counter_n_relevantes + (cursor.count_documents(manual_relevance_not),)
                    counter_doubt = counter_doubt + (cursor.count_documents(manual_relevance_doubt),)
                    counter_n_classificadas = counter_n_classificadas + (cursor.count_documents(manual_relevance_false),)

                    relevant = relevant + cursor.count_documents(manual_relevance)
                    not_relevant = not_relevant + cursor.count_documents(manual_relevance_not)
                    doubt = doubt + cursor.count_documents(manual_relevance_doubt)
                    n_classificadas = n_classificadas + cursor.count_documents(manual_relevance_false)

                tupla_info = tupla_info + counter_totais + (counter,)
                tupla_relevance = tupla_relevance + counter_relevantes + (relevant,)
                tupla_not_relevance = tupla_not_relevance + counter_n_relevantes + (not_relevant,)
                tupla_doubt = tupla_doubt + counter_doubt + (doubt,)
                tupla_n_classificadas = tupla_n_classificadas + counter_n_classificadas + (n_classificadas,)

                tupla_inicial.append(tupla_info)
                tupla_inicial.append(tupla_relevance)
                tupla_inicial.append(tupla_not_relevance)
                tupla_inicial.append(tupla_doubt)
                tupla_inicial.append(tupla_n_classificadas)

                print(f"[SUCESSO] {self.news_portal_name[i]} concluído")

            print("[SUCESSO] As informações de cada um dos portais foram obtidas")
            logging.info("Todas as notícias/ano foram obtidas")
            name = input("[AVISO] Digite o nome do relatório (não é necessário colocar .csv)\n")
            self.loader._load_csv(tupla_inicial, name)
        except Exception as e:
            print(f"[ERRO] Erro ao tentar gerar relatório: {e}")

        finally:
            connection._close_connection(connection.client)