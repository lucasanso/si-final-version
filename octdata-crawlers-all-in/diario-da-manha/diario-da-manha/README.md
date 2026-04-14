🚀 Guia de Início Rápido

Siga os passos abaixo para configurar seu ambiente local e iniciar a extração.
1. Clonar e Preparar o Ambiente

Primeiro, clone o repositório e crie um ambiente virtual para isolar as dependências:
Bash

# Criar ambiente virtual
python3 -m venv venv

# Ativar o ambiente
# No Linux/macOS:
source venv/bin/activate
# No Windows:
.\venv\Scripts\activate

2. Instalar Dependências

Com o ambiente ativo, instale os pacotes necessários:
Bash

pip install -r requirements.txt

3. Configuração do Projeto

O crawler utiliza um arquivo config.yaml para gerenciar termos de busca e credenciais de acesso. Existe um modelo pronto para você usar:

    Localize o arquivo config_example.yaml na raiz do projeto.

    Duplique-o e renomeie a cópia para config.yaml.

    Edite o config.yaml com suas credenciais de banco de dados e os termos que deseja monitorar.

    [!IMPORTANT]
    O projeto não iniciará sem a presença do arquivo config.yaml corretamente preenchido.

4. Execução

Tudo pronto! Para iniciar o processo de crawling, execute:
Bash

python3 app.py