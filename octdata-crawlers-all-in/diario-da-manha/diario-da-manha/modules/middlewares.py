from pymongo import MongoClient

class DuplicatedUrls:
    """
    Gerencia a lógica de deduplicação de URLs utilizando o histórico do MongoDB.
    
    Esta classe centraliza a busca de links que já foram processados em execuções 
    anteriores, tanto para notícias aceitas quanto para as descartadas pelo validador.
    """

    def __init__(self) -> None:
        """
        Inicializa a classe de verificação de duplicatas.
        """
        print("[PROCESSO] Obtendo todas as notícias já vistas do MongoDB")

    def get_all_seen_urls(self, connection_mongodb: MongoClient) -> set:
        """
        Recupera e consolida todas as URLs presentes no banco de dados.

        Busca em duas coleções distintas ('newsData' e 'unacceptedNews') para 
        garantir que o robô não tente re-processar notícias que já foram 
        analisadas, independentemente de terem sido validadas ou não.

        Args:
            connection_mongodb (MongoClient): Instância ativa de conexão com o servidor MongoDB.

        Returns:
            set: Um conjunto (set) contendo as strings de URLs. O uso de 'set' é 
                 estratégico para garantir buscas de complexidade O(1).

        Notes:
            A deduplicação é crítica para economizar banda e evitar bloqueios (IP bans) 
            nos portais, garantindo que o Crawler foque apenas em conteúdo inédito.
        """
        lst = []
        
        # Carrega URLs de notícias que passaram na validação
        accepted_urls = [doc['url'] for doc in connection_mongodb.get_database("couser").get_collection("newsData").find({}, {'url': 1})]
        lst.extend(accepted_urls)
        
        print(f"[SUCESSO] Notícias aceitas já percorridas totalmente carregadas {len(lst)}")
        
        # Carrega URLs de notícias que foram recusadas (mas já lidas)
        unaccepted_urls = [doc['url'] for doc in connection_mongodb.get_database("couser").get_collection("unacceptedNews").find({}, {'url': 1})]
        lst.extend(unaccepted_urls)

        qtd = len(lst) 

        print(f"[SUCESSO] Todas as notícias foram carregadas. Quantidade [{qtd}]")

        # Conversão para set para otimização de busca
        return set(lst)