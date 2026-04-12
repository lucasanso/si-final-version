import datetime
import time
import re
from modules.connection import ConnectMongoSSH
from modules.load import LoadData
import logging
from modules.settings import NOMES_PORTAIS, ANOS_A_PERCORRER, DATA_FIELDS

# Implementar camada de segurança maior aqui pois as funções que atingem diretamente o banco de dados e atributos.

# Estilo de documentação: Type Hints & DocString
class TransformData:
    """
    Classe que contém funções que manipulam atributos de documentos do banco de dados.
    """
    def __init__(self) -> None:
        self.loader = LoadData()
        self.news_portal_name = NOMES_PORTAIS
        self.years = ANOS_A_PERCORRER
        self.data_fields = DATA_FIELDS

    def cvt_timestampz_to_date(self):
        """
        Função que formata datas de tipo TIMESTAMPZ para DATE.
        """

        connection = ConnectMongoSSH()
        cursor = connection._connect_to_mongo()
        valid = True

        while valid:
            field = input("[AVISO] Digite o campo de data que deseja formatar:\n")

            if field in self.data_fields:
                print(f"[SUCESSO] O campo de data [{field}] foi encontrado.")
                valid = False
            
            else:
                print("[ERRO] O campo de data digitado não existe. Tente novamente.")

        for i in range (len(self.news_portal_name)):
            print(f"[PROCESSO] Iniciando formatação de data de TIMESTAMPZ para ISO do portal {self.news_portal_name[i]}.")
            time.sleep(5)

            query = {
                'newspaper' : self.news_portal_name[i],
            }

            counter = 0
            processed = 0
            another_format = 0
            null_dates = 0

            for doc in cursor.find(query):
                if doc[field] is None:
                    print("[AVISO] A notícia possui data de publicação nula.")
                    null_dates = null_dates + 1

                    continue

                elif type(doc[field]) == datetime.datetime:
                    filtro = {field: doc[field]}

                    if type(filtro[field]) == datetime.datetime:
                        format_date = str(doc[field])[0:10]
                        print(format_date)
                        atualizar = {"$set": {field : format_date}}
                        cursor.update_one(filtro, atualizar)
                        print(f"[SUCESSO] Data {doc[field]} atualizada para ISO")

                        counter = counter + 1

                elif re.findall(r'[0-3][0-9]-..-....', doc[field]):
                    print("[AVISO] A data está em formato ISO invertido")
                    another_format = another_format + 1

                else:
                    print("[AVISO] A data já foi processada")
                    processed = processed + 1

            self.info.append(
                (self.news_portal_name[i],
                counter,
                processed,
                another_format,
                null_dates)
                )
             
            time.sleep(3)
        
        print("[SUCESSO] Todas as datas foram formatadas")
        logging.info("Todas as datas do tipo TIMESTAMPZ foram formatadas para ISO")
    
    def cvt_inverted_date(self) -> None:
        """
        Formata datas que estão em DD-MM-YYYY para YYYY-MM-DD.
        """
        connection = ConnectMongoSSH()
        cursor = connection._connect_to_mongo()
        valid = True
        
        while valid:
            field = input("[AVISO] Digite o campo de data que deseja formatar:\n")

            if field in self.data_fields:
                valid = False
                print(f"[SUCESSO] Campo de data [{field}] encontrado.")
            else:
                print("[ERRO] O campo de data digitado não existe. Tente novamente.")
    
        for i in range(len(self.news_portal_name)):
            print(f"[PROCESSO] Iniciando inversão de datas {self.news_portal_name[i]}")

            query = {
                'newspaper' : self.news_portal_name[i]
            }
            
            for doc in cursor.find(query):
                if doc[field] is None:
                    print("Data nula!")
                    time.sleep(0.15)

                elif re.findall(r'20..-..-..', doc[field]):
                    print("[AVISO] A data já está formatada em ISO")

                else:
                    print("[AVISO] A data está em formato invertido ISO. Alterando...")
                    filtro = {
                        field : doc[field]
                    }   

                    date = str(doc[field]).strip()   
                    print(date) 
                    date_formated = datetime.date(int(date[6:10]), int(date[3:5]), int(date[0:2]))
                    date_formated = str(date_formated)

                    atualizar = {
                        f'$set': {field : date_formated}
                    }

                    cursor.update_one(filtro, atualizar)
                    print("[SUCESSO] A data foi alterada")

        logging.info("Todas as datas em formato ISO invertido foram formatadas.")
        connection._close_connection(connection.client)    

    # Esta função está com lógica inadequada
    def remove_date_blank_space(self):
        """
        Remove espaços em branco de datas.
        """
        connection = ConnectMongoSSH()
        cursor = connection._connect_to_mongo()
        valid = True
        
        while valid:
            field = input("[AVISO] Digite o campo de data que deseja formatar:\n")

            if field in self.data_fields:
                valid = False
                print(f"[SUCESSO] Campo de data [{field}] encontrado.")
            else:
                print("[ERRO] O campo de data digitado não existe. Tente novamente.")

        for i in range (len(self.news_portal_name)):
            print(f"[PROCESSO] Iniciando limpeza de datas com espaço em branco do portal {self.news_portal_name[i]}")
            time.sleep(3)

            query = {
                'newspaper': self.news_portal_name[i]
            }

            for doc in cursor.find(query):
                if doc[field] is None:
                    print("[CRÍTICO] Data nula")
                    time.sleep(0.15)

                    continue
                elif re.findall(r'[0-3][1-9]-..-....', doc[field]):
                    print("[AVISO] A data está formatada em ISO invertido")
                    continue
                elif re.findall(r'....-..-.. ', doc[field]):
                    print("[PROCESSO] Formatando data")
                    filtro = {
                       field: doc[field]
                    }

                    date = str(doc[field]).strip()

                    atualizar = {
                        f'$set': {field : date} 
                    }
                    cursor.update_one(filtro, atualizar)

                    print("[SUCESSO] A data foi limpa (sem espaços em branco).")
                else:
                    print("[AVISO] A data já está limpa. Pulando...")

        print("[SUCESSO] Todas as datas foram formatadas.")
        logging.info("Campo em branco retirado das datas.")

        connection._close_connection(connection.client)

    def update_newspaper_name(self) -> None:
        """
        Altera o nome de um portal de notícias.

        Possui lógica de verificação de nome do portal.

        """
        connection = ConnectMongoSSH()
        cursor = connection._connect_to_mongo()
        valid = True

        while valid:
            newspaper = input("[AVISO] Digite o nome atual do portal:\n")
            if newspaper in self.news_portal_name:
                valid = False
            else:
                print("[ERRO] O portal digitado não existe. Tente novamente:\n")

        new_name = input("[AVISO] Digite o novo nome do portal:\n")

        query = {
            'newspaper' : newspaper
        }

        for doc in cursor.find(query):
            filtro = {'newspaper': doc['newspaper']}
            if filtro['newspaper'] == newspaper:
                atualizar = {f'$set': {'newspaper': new_name}}

                print("[AVISO] Foi encontrado nome do portal diferente. Alterando...")
                cursor.update_one(filtro, atualizar)

        print("[SUCESSO] Todas as notícias tiveram nome do portal atualizado.")

        connection._close_connection(connection.client)

    # Essa função foi criada exclusivamente para o portal Diário do Amanhã
    # Essa função está com problema de lógica para o mês de maio com dias 1 <= x < 10
    def string_date_processing(self) -> None:
        """
        Transforma data de 'DD de MM de YYYY' para 'DD-MM-YYYY'

        Esta função foi criada porque a data de publicação do portal Diário da Manhã possui a formatação citada acima.
        """
        connection = ConnectMongoSSH()
        cursor = connection._connect_to_mongo()
        valid = True
        
        while valid:
            field = input("[AVISO] Digite o campo de data que deseja formatar:\n")

            if field in self.data_fields:
                valid = False
                print(f"[SUCESSO] Campo de data [{field}] encontrado.")
            else:
                print("[ERRO] O campo de data digitado não existe. Tente novamente.")

        count = 0

        for i in range (len(self.news_portal_name)):
            print(f"[PROCESSO] Iniciando inversão de datas do portal {self.news_portal_name[i]}.")

            dict_month = {
                "janeiro" : "01",
                "fevereiro" : "02",
                "março" : "03",
                "abril" : "04",
                "maio" : "05",
                "junho" : "06",
                "julho" : "07",
                "agosto" : "08",
                "setembro" : "09",
                "outubro" : "10",
                "novembro" : "11",
                "dezembro" : "12"
            }

            query = {
                'newspaper' : self.news_portal_name[i],
            }

            for doc in cursor.find(query):
                if doc[field] is None:
                    print("[AVISO] Data nula!")
                    time.sleep(1)
                    continue
                
                elif re.findall(r' de ', doc[field]):
                    date_att = re.sub(r' de ', '-', doc[field])
        
                    for month in dict_month:
                        if re.findall(fr'{month}', date_att):
                            count += 1
                            date_att = re.sub(fr'{month}', dict_month[month], date_att)
                            if len(date_att) == 9:
                                date_att = "0" + date_att
                                
                            print(date_att)
                            break
                    
                    filtro = {
                        field: doc[field]
                    }

                    atualizar = {
                        "$set" : {field : date_att}
                    }

                    cursor.update_one(filtro, atualizar)

                    print("[SUCESSO] Data de string foi alterada para DD-MM-YY")

                else:
                    print("[AVISO] A data já está formatada")

        connection._close_connection(connection.client)

    def _get_last_id_event(self, cursor: ConnectMongoSSH._connect_to_mongo) -> int:
        """
        Obtém o valor do índice id_event do último documento para utilizá-lo como referência na função set_documents_id_event.

        Args:
            cursor (ConnectMongoSSH._connect_to_mongo): Cursor do MongoDB.

        Returns:
            int: Índice em inteiro.
        """
        query = {
            "id_event" : {"$exists" : True}
        }

        doc = cursor.find_one(query, sort=[("_id", -1)])

        if doc:
            return doc["id_event"] + 1
        else:
            return False

    # fazer essa funcao funcionar com o add de conjuntos para aumentar o id
    def set_documents_id_event(self) -> None:
        """
        Insere o atributo id_event em cada um dos documentos que não possui.

        Para que consigamos inserir notícias na coleção newsData é necessário que exista esse número de id_event.
        """
        try:
            id_event = self._get_last_id_event(self.cursor)
            cursor = ConnectMongoSSH()
            cursor = cursor._connect_to_mongo()
            print(id_event)
            for i in range (len(self.news_portal_name)):
                query = {
                    "newspaper" : self.news_portal_name[i],
                    "id_event": {"$exists": False}
                }

                for doc in cursor.find(query):
                    if doc:
                        try:
                            atualizar = {
                                "$set" : { "id_event" : id_event}
                            }
                            cursor.update_one(doc, atualizar)

                            doc = cursor.find_one(doc)

                            self.cursor.insert_one(doc)

                            id_event = self._get_last_id_event(cursor)
                            print(id_event)
                        except Exception as e:
                            print(f"[ERRO] {e}")
                    else:
                        continue
        except Exception as e:
            print(f"[ERRO] {e}")

        
    # inseriremos urls da coleção lida aqui para a principal (Ex: unacceptedNews primeiro e testeFSP em segundo)
    def merge_unaccepted_collections(self) -> None:
        """
        Insere URLs de uma coleção para outra.

        Comparamos URLs de uma coleção para outra. 

        Utiliza lógica de deduplicação para evitar de que sejam colocadas URLs repetidas e poluir os dados.
        """
        # Primeira coleção
        connection = ConnectMongoSSH()
        cursor = connection._connect_to_mongo()

        new_connection = ConnectMongoSSH()
        new_cursor = new_connection._connect_to_mongo()

        urls = self._getAllUrlsMainCollection()
        counter_in = 0
        counter_n_in = 0

        query = {
            "url" : {'$exists' : True}
        }

        for doc in new_cursor.find(query):
            if doc['url'] in urls:
                counter_in += 1
            
            else:
                create_dict = {
                    'url' : doc['url']
                }
                cursor.insert_one(create_dict)
                counter_n_in += 1
                print(f"Inserindo {counter_n_in}")

        print(
                f"Quantidade de urls que não estão em unaccepted: {counter_n_in}"
                f"\nQuantidade de urls que já estão em unaccepted: {counter_in}"
                f"\nQuantidade total de urls: {counter_in + counter_n_in}"
            )
        
        print("[AVISO] Encerrando primeira conexão")
        connection._close_connection(connection.client)

        print("[AVISO] Encerrando segunda conexão")
        connection._close_connection(new_connection.client)

    def _getAllUrlsMainCollection(self, cursor: ConnectMongoSSH._connect_to_mongo) -> set:
        """
        Retorna um conjunto contendo todas as URLs da coleção.

        Args:
            cursor(ConnectMongoSSH._connect_to_mongo): Cursor do MongoDB.

        Returns:
            set: Conjunto de URLs.
        """
        all_urls = set()
        
        query = {
            "url" : {'$exists': True}
        }

        for doc in cursor.find(query):
            all_urls.add(doc['url'])
        
        print(f"[SUCESSO] Todas as notícias foram obtidas {len(all_urls)}")
        return all_urls

    # Existem jornais que não possuem o atributo manual_relevance_class, que é importantíssimo para determinar a quantidade de notícias/ano
    def setAttribute(self):
        """
        Insere atributo 'manual_relevance_class' em cada um dos documentos.
        """
        connection = ConnectMongoSSH()
        cursor = connection._connect_to_mongo()
        
        for i in range(len(self.news_portal_name)):
            query = {
                'newspaper' : self.news_portal_name[i],
                'manual_relevance_class' : {'$exists' : False}
            }
            print(cursor.find_one(query))
            for doc in cursor.find(query):
                print("opa")
                update = {
                    '$set' : {'manual_relevance_class': None}
                }
                cursor.update_one(doc, update)

                print("[SUCESSO] Campo manual_relevance_class adicionado.")



    
