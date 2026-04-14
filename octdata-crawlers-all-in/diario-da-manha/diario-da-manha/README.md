# Guia de Início Rápido

Siga os passos abaixo para configurar seu ambiente local e iniciar a extração.

## Criar ambiente virtual
```bash
python3 -m venv venv
```

## Ativar o ambiente
```bash
source venv/bin/activate
``` 

## Instalar Dependências

Com o ambiente ativo, instale os pacotes necessários:

```
pip install -r requirements.txt
```

## Configuração do Projeto

O crawler utiliza um arquivo config.yaml para gerenciar termos de busca e credenciais de acesso. Existe um modelo pronto para você usar:

    Localize o arquivo config_example.yaml na raiz do projeto.

    Duplique-o e renomeie a cópia para config.yaml.

    Edite o config.yaml com suas credenciais de banco de dados e os termos que deseja monitorar.

    [IMPORTANTE]
    O projeto não iniciará sem a presença do arquivo config.yaml corretamente preenchido.

## Execução

Para iniciar o processo de crawling, execute:

```bash
python3 app.py
```
