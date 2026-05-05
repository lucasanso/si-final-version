# Extração de Dados e Análise de Notícias sobre Crime Organizado

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

Para garantir a saúde da operação, foi desenvolvido um painel de observabilidade, permitindo o acompanhamento em tempo real da extração e apoiando a tomada de decisão técnica durante o processo de coleta.

## Contexto Acadêmico e Disponibilidade

Por se tratar de uma pesquisa de iniciação científica, o dataset resultante e a ferramenta de extração são de uso restrito ao ambiente de pesquisa acadêmica.

No entanto, a lógica de engenharia de dados, os padrões de extração e a arquitetura do pipeline estão documentados para demonstrar a viabilidade técnica e o rigor metodológico aplicados no tratamento de grandes volumes de dados (Big Data).
