from unidecode import unidecode
import re
from .keywords import VALIDATION_KEYWORDS, KEYWORDS
import os
import yaml
from pathlib import Path

def validate_article(article: str) -> str | bool:
    """
    Valida se um artigo é relevante cruzando a presença de grupos e ações criminosas.

    Args:
        article (str): O corpo do texto da notícia processada.

    Returns:
        str | bool: Retorna uma string formatada "grupo - ação" se ambos forem encontrados, 
                   ou False caso o artigo não atenda aos critérios mínimos de relevância.
    
    Notes:
        Esta é a função de filtragem principal. Um artigo só é "aceito" se mencionar 
        pelo menos um termo de organização criminosa E um termo de ação (drogas ou armas).
    """
    GROUP = VALIDATION_KEYWORDS["GANGS"] + VALIDATION_KEYWORDS["ORGANIZED CRIME"]
    ACTIONS = VALIDATION_KEYWORDS["DRUGS"] + VALIDATION_KEYWORDS["ARMED INTERACTIONS"]
    group = False
    action = False

    for k in GROUP:
        if re.findall(fr'{k}', article):
            group = k

    for k in ACTIONS:
        if re.findall(fr'{k}', article):
            action = k

    return f"{group} - {action}" if group and action else False



def search_tags(article: str) -> list:
    """
    Identifica e extrai termos relacionados a crimes (drogas e armas) no texto.

    Args:
        article (str): O corpo do texto da notícia.

    Returns:
        list: Uma lista contendo todas as palavras-chave de ação encontradas.
    """
    TAGS = KEYWORDS["DRUGS"] + KEYWORDS["ARMED INTERACTIONS"]
    tags = []
    for k in TAGS:
        if re.findall(fr'{k}', article):
            tags.append(k)

    return tags

def search_gangs(article: str) -> list:
    """
    Identifica e extrai nomes de facções ou termos de crime organizado no texto.

    Args:
        article (str): O corpo do texto da notícia.

    Returns:
        list: Uma lista contendo os nomes dos grupos criminosos identificados.
    """
    GANGS = KEYWORDS["GANGS"] + KEYWORDS["ORGANIZED CRIME"]
    gangs = []
    for k in GANGS:
        if re.findall(fr'{k}', article):
            gangs.append(k)

    return gangs

def save_processed_kword(keyword: str, crawler: str):
    """
    Registra uma palavra-chave como 'concluída' em um arquivo YAML persistente.

    Args:
        keyword (str): A palavra-chave que acabou de ser processada.
        crawler (str): O nome do spider (ex: 'g1', 'folha') para organizar os arquivos.

    Notes:
        Cria o diretório 'kwords-processing' e o arquivo correspondente caso não existam. 
        Isso evita que o Spider re-processe termos em execuções futuras.
    """
    if os.path.exists(f'kwords-processing/{crawler}_processed_kwords.yaml'):
        pass
    else:
        print("[AVISO] O arquivo processed_kwords.yaml não existe.")
        Path.touch(f'kwords-processing/{crawler}-processed_kwords.yaml')

    write_in_yaml(f'kwords-processing/{crawler}_processed_kwords.yaml', keyword)

def write_in_yaml(file: str, keyword: str):
    """
    Executa a escrita física da palavra-chave no arquivo de controle.

    Args:
        file (str): O caminho para o arquivo YAML.
        keyword (str): O termo a ser salvo.
    """
    with open(f"{file}", "a") as file:
        file.write(f"\n{keyword}")
        print(f"[SUCESSO] Palavra {keyword} foi salva.")

def get_processed_kwords(crawler: str) -> list:
    """
    Lê a lista de palavras-chave já processadas para um spider específico.

    Args:
        crawler (str): O nome do spider.

    Returns:
        list: Uma lista de strings com os termos já finalizados.

    Notes:
        Se o arquivo não existir, ele é criado com uma lista vazia. 
        Inclui um cálculo de log que mostra quantos termos ainda restam no escopo total.
    """
    try:
        processed_kwords = []
        file_path = f'kwords-processing/{crawler}_processed_kwords.yaml'
        
        if os.path.exists(file_path):
            with open(file_path, "r", encoding='utf-8') as file:
                processed_kwords = yaml.safe_load(file) or []
                total_kwords = len(KEYWORDS['GANGS'] + KEYWORDS['ORGANIZED CRIME'])
                remaining = total_kwords - len(processed_kwords)
                print(f'[SUCESSO] Palavras-chave encontradas. Restam {remaining}')
        else:
            print(f"[AVISO] O arquivo {file_path} não existe. Criando...")
            os.makedirs('kwords-processing', exist_ok=True)
            with open(file_path, 'w') as f:
                yaml.dump([], f) 

        return processed_kwords

    except Exception as e:
        print(f"[ERRO] Erro ao obter palavras-chave: {e}")
        return []