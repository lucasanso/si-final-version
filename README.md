# Extração de Dados para Análise de Notícias sobre Crime Organizado

Este projeto de Iniciação Científica, desenvolvido na Universidade Federal de Goiás (UFG), em parceria com a Faculdade de Ciências Sociais (FCS) da UFG, foca na construção de um pipeline robusto de Engenharia de Dados (ETL) para coletar e processar informações sobre o crime organizado a partir de grandes portais de notícias brasileiros.

O objetivo central foi transformar milhões de dados brutos da web em um dataset estruturado e quantitativo, viabilizando a realização de análises sobre padrões e tendências da segurança pública pelos discentes da FCS.
## Stack Tecnológica e Arquitetura

A arquitetura do projeto foi desenhada para lidar com alta volumetria e diversidade de estruturas de HTML, garantindo resiliência e performance no processo de raspagem.

    Scrapy: Utilizado como motor principal de crawling para percorrer milhões de URLs com alta performance e gerenciamento eficiente de requisições.

    BeautifulSoup & Regex: Empregados na camada de parsing para extrair informações específicas e limpar ruídos dos textos, garantindo a precisão dos dados coletados.

    MongoDB: Escolhido como banco de dados NoSQL para armazenar os dados semiestruturados de forma flexível durante as etapas de extração.

    Pandas: Utilizado para gerar automaticamente relatórios em .csv sobre o quantitativo de notícias.

## Escala e Resultados

O projeto alcançou números expressivos, demonstrando a eficiência da lógica aplicada e a robustez da infraestrutura de dados:

    8 portais de notícias monitorados simultaneamente (G1, Folha de São Paulo, Brasil de Fato, Correio do Povo, Carta Capital, Le Monde Brasil Diplomatique, Diário da Manhã e Estadão).

    3,5 milhões de URLs percorridas pelos crawlers.

    120 mil notícias validadas e integradas ao dataset final após critérios rigorosos de filtragem sobre crime organizado.

## Configuração de Credenciais

Para cada módulo que possua um arquivo config_example.yaml, você deve inserir suas credenciais e renomeá-lo:

```bash
cp config_example.yaml config.yaml
``` 

## Inicialização do Cluster

Suba os serviços (crawlers e processador de dados do MongoDB) em segundo plano:
```bash
docker compose up -d
```

## Interação com os Módulos
### Processamento de Dados

Para realizar o tratamento dos dados armazenados no MongoDB:
```bash
docker exec -it data_processing bash
```

### Execução de Crawlers (Scrapy)

Para gerenciar os extratores de portais específicos:
```bash
docker exec -it portals-extractors bash
# Dentro do container, execute o bot desejado:
scrapy crawl <nome_do_bot>
```

### Extrator do portal Diário da Manhã (BS4)

Este portal utiliza um módulo dedicado via Python puro:

```bash
docker exec -it diario-extractor bash
# Dentro do  container, execute o comando abaixo:
python3 app.py
```

## Contexto Acadêmico e Disponibilidade

Por se tratar de uma pesquisa de iniciação científica, o dataset resultante (120 mil notícias sobre crime organizado) é de uso restrito ao ambiente de pesquisa acadêmica.

No entanto, a lógica de engenharia de dados, os padrões de extração e a arquitetura do pipeline estão documentados para demonstrar a viabilidade técnica e o rigor metodológico aplicados no tratamento de grandes volumes de dados.
