# Guia prático para inicialização dos crawlers

Siga os passos abaixo para preparar seu ambiente e começar a extrair:
1. Configuração de Credenciais

Antes de rodar os motores, você precisa configurar suas chaves e acessos.

    Localize o arquivo config_example.yaml.

    Crie uma cópia chamada config.yaml.

    Preencha os campos necessários com suas credenciais.

2. Preparação do Ambiente

É recomendado o uso de um ambiente virtual para manter as dependências isoladas e organizadas.

```bash
# Criar o ambiente virtual

python -m venv .venv

source .venv/bin/activate

```
3. Instalação do Playwright

```bash
# Como alguns crawlers lidam com conteúdo dinâmico, precisamos instalar os navegadores do Playwright:

playwright install
```
Como Utilizar

```bash
# Com tudo configurado, basta chamar o bot desejado através do comando padrão do Scrapy:

scrapy crawl <id_do_bot>
```
Lista de bots
| id do bot | Portal de Notícias |
| :--- | :--- |
| `bdf` | Brasil de Fato |
| `g1` | G1 |
| `folha` | Folha de S. Paulo |
| `estadao` | Estadão |
| `monde` | Le Monde Diplomatique |
| `correio` | Correio do Povo |
| `carta` | Carta Capital |
