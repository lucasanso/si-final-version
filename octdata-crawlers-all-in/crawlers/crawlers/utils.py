from unidecode import unidecode
import re
from .keywords import VALIDATION_KEYWORDS, KEYWORDS
import os
import yaml
from pathlib import Path

def validate_article(article):
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

def search_tags (article):
    TAGS = KEYWORDS["DRUGS"] + KEYWORDS["ARMED INTERACTIONS"]
    tags = []
    for k in TAGS:
        if re.findall(fr'{k}', article):
            tags.append(k)

    return tags

def search_gangs (article):
    GANGS = KEYWORDS["GANGS"] + KEYWORDS["ORGANIZED CRIME"]
    gangs = []
    for k in GANGS:
        if re.findall(fr'{k}', article):
            gangs.append(k)

    return gangs

def save_processed_kword(keyword, crawler):
    if os.path.exists(f'kwords-processing/{crawler}_processed_kwords.yaml'):
        pass
    else:
        print("[AVISO] O arquivo processed_kwords.yaml não existe.")
        Path.touch(f'kwords-processing/{crawler}-processed_kwords.yaml')

    write_in_yaml(f'kwords-processing/{crawler}_processed_kwords.yaml', keyword)

def write_in_yaml(file, keyword):
    with open(f"{file}", "a") as file:
        file.write(f"\n{keyword}")

        print(f"[SUCESSO] Palavra {keyword} foi salva.")

def get_processed_kwords(crawler):
    try:
        processed_kwords = []
        file_path = f'kwords-processing/{crawler}_processed_kwords.yaml'
        
        if os.path.exists(file_path):
            with open(file_path, "r", encoding='utf-8') as file:
                processed_kwords = yaml.safe_load(file) or []
                print(f'[SUCESSO] Palavras-chave percorridas encontradas. Restam {len(KEYWORDS['GANGS'] + KEYWORDS['ORGANIZED CRIME']) - len(processed_kwords)}')
        else:
            print(f"[AVISO] O arquivo {file_path} não existe. Criando...")
            os.makedirs('kwords-processing', exist_ok=True)
            with open(file_path, 'w') as f:
                yaml.dump([], f) 

        return processed_kwords

    except Exception as e:
        print(f"[ERRO] Erro ao obter palavras-chave: {e}")
        return [] # Retorno de segurança para a Spider não travar

# fazer função que lida com o processamento diário com o airflow
def already_processed():
    pass

def processing_keyword():
    pass