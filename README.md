# Introdução Desafio Jusbrasil

Projeto desenvolvido a partir de desafio feito pela empresa Jusbrasil.

# Descrição

Este projeto tem como objetivo montar uma aplicação REST para extrair dados de processo do site TJRS. A aplicação estara rodando dentro de um docker que receberá as requisições, irá processá-las e entregar os resultados correspondentes.

## 📖 Sumário

1. [Introdução](#introdução-challenge-neoway)  
2. [Descrição](#descrição)  
3. [Iniciando](#iniciando)  
   - [Dependências](#dependências)  
   - [Instalação](#instalação)  
   - [Executando o Projeto](#executando-projeto)  
4. [Funcionalidades da API](#funcionalidades-da-api)  
   - [Criando um Cliente](#criando-um-cliente-no-banco)  
   - [Listando Clientes](#listando-clientes-do-banco)  
   - [Busca por Nome](#busca-pelo-nome)  
   - [Busca por CPF ou CNPJ](#buscando-cliente-por-cpf-ou-cnpj)  
   - [Deletando um Cliente](#deletando-um-cliente-no-banco)  
   - [Atualizando um Cliente](#atualizando-um-cliente-no-banco)  
   - [Verificando o Status do Serviço](#verificando-o-status-do-serviço)  
5. [Executando os Testes](#executando-os-testes)  
6. [Autor](#autor)  

# Iniciando

## Dependências
* Python 3.11
* Docker
##### Windows
https://docs.docker.com/desktop/setup/install/windows-install/
##### Linux
```
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
```
## Instalação

### Clonar projeto do git.
* Abrir terminal
* Navegar até a pasta para onde desejar importar o projeto
* Executar o comando
```
git clone git@github.com:Pauloh7/challengeneoway.git
```
## Executando Projeto
##### Buildar docker e subir aplicação com banco e api.
* Abrir terminal ou powershell
* Navegar até a pasta do projeto
* Executar o comando
```
docker-compose up --build
```
* O docker compose irá rodar o alembic na primeira execução, caso não seja criada a tabela Cliente no banco de dados ou tenha algum problema utilize o comando abaixo para criação da tabela
```
docker exec -it api_neoway poetry run alembic upgrade head
```
## Funcionalidades da API
### Criando um Cliente no Banco

#### Exemplo de Chamada

```
curl -X POST \
    "http://0.0.0.0:8000/cliente" \
    -H "Content-Type: application/json" \
    -H "Accept: application/json" \
    -d '{
         "nome": "Bruno",
         "documento": "065.556.430-64"
        }'
```

#### Parâmetros da Requisição

| Parâmetro  | Tipo   | Descrição |
|------------|--------|-------------|
| nome       | string | Nome do cliente a ser criado no banco |
| documento  | string | Documento CPF ou CNPJ do cliente a ser criado |
| block_list | boolean (opcional) | Indica se o cliente está na lista bloqueada |

#### Exemplo de Resposta

```
HTTP/1.1 200 OK
Content-Type: application/json

{
    "nome": "Bruno",
    "documento": "065.556.430-64",
    "blocklist": false
}
```

### Listando Clientes do Banco
#### Exemplo de Chamada

```
curl -X POST \
    "http://0.0.0.0:8000/cliente_list" \
    -H "Content-Type: application/json" \
    -H "Accept: application/json" \
   -d '{
         "nome":""
      }'
```

#### Parâmetros da Requisição

| Parâmetro  | Tipo   | Descrição |
|------------|--------|-------------|
| nome       | string (opcional)| Nome do cliente a ser buscado no banco |

#### Exemplo de Resposta

```
HTTP/1.1 200 OK
Content-Type: application/json

[
    {
        "nome": "Ana",
        "documento": "605.120.690-69",
        "blocklist": true
        "pessoa_juridica":false
    }
    {
        "nome": "Bruno",
        "documento": "065.556.430-64",
        "blocklist": false
        "pessoa_juridica":false    
    }
    {
        "nome": "Carlos",
        "documento": "93.074.074/0001-53",
        "blocklist": false
        "pessoa_juridica":True
    }
]
```
### Busca pelo nome
#### Exemplo de Chamada

```
curl -X POST \
    "http://0.0.0.0:8000/cliente_list" \
    -H "Content-Type: application/json" \
    -H "Accept: application/json" \
    -d '{
         "nome": "Bruno"
        }'
```

#### Parâmetros da Requisição

| Parâmetro  | Tipo   | Descrição |
|------------|--------|-------------|
| nome       | string (opcional)| Nome do cliente a ser buscado no banco |

#### Exemplo de Resposta
```
HTTP/1.1 200 OK
Content-Type: application/json

[
    {
        "nome": "Bruno",
        "documento": "065.556.430-64",
        "blocklist": false
        "pessoa_juridica":false 
    }
]
```
### Buscando Cliente por CPF ou CNPJ

#### Exemplo de Chamada

```
curl -X GET \
    "http://0.0.0.0:8000/cliente/065.556.430-64" \
    -H "Accept: application/json"
```

#### Parâmetros da Requisição

| Parâmetro  | Tipo   | Descrição |
|------------|--------|-------------|
| documento  | string | CPF ou CNPJ do cliente a ser buscado |

#### Exemplo de Resposta

```
HTTP/1.1 200 OK
Content-Type: application/json

{
    "nome": "Bruno",
    "documento": "065.556.430-64",
    "blocklist": false
    "pessoa_juridica":false 
}
```

### Deletando um Cliente no Banco

#### Exemplo de Chamada

```
curl -X DELETE \
    "http://0.0.0.0:8000/cliente/065.556.430-64" \
    -H "Accept: application/json"
```

#### Parâmetros da Requisição

| Parâmetro  | Tipo   | Descrição |
|------------|--------|-------------|
| documento  | string | CPF ou CNPJ do cliente a ser deletado |

#### Exemplo de Resposta

```
HTTP/1.1 200 OK
Content-Type: application/json

{
    "message": "Cliente deletado com sucesso",
}
```
### Atualizando um Cliente no Banco

#### Exemplo de Chamada

```
curl -X PATCH \
    "http://0.0.0.0:8000/cliente/065.556.430-64" \
    -H "Content-Type: application/json" \
    -H "Accept: application/json" \
    -d '{
         "nome": "Bruno Silva",
         "blocklist": true
        }'
```

#### Parâmetros da Requisição

| Parâmetro  | Tipo   | Descrição |
|------------|--------|-------------|
| documento  | string | CPF ou CNPJ do cliente a ser atualizado |
| nome       | string (opcional) | Novo nome do cliente |
| blocklist  | boolean (opcional) | Indica se o cliente está na lista bloqueada |

#### Exemplo de Resposta

```
HTTP/1.1 200 OK
Content-Type: application/json

{
    "nome": "Bruno Silva",
    "documento": "065.556.430-64",
    "blocklist": true
    "pessoa_juridica":false 
}
```
### Verificando o Status do Serviço

#### Exemplo de Chamada

```
curl -X GET "http://0.0.0.0:8000/status" -H "Accept: application/json"
```

#### Exemplo de Resposta

```
HTTP/1.1 200 OK
Content-Type: application/json

{
    "uptime": "00:05:23",
    "status": "healthy",
    "database": "connected",
    "request_count": 42
}
```

### Executando os Testes
#### No Windows
* Baixar o git/bash em https://git-scm.com/downloads/win
* Baixar o make em https://gnuwin32.sourceforge.net/packages/make.htm
* Instalar tanto o git/bash, quanto o make
* Abrir um terminal git/bash
* Navegar até o diretorio do projeto
* Executar o comando
```
make test
```
* Os testes devem executar automaticamente e o resultado será exibido na tela
#### No linux
* Abra o terminal
* Navegue até o diretorio do projeto
* Rode o comando
```
make test
```
* Os testes devem executar automaticamente e o resultado será exibido na tela
## Autor

[Paulo Henrique De Souza Gomes](https://www.linkedin.com/in/paulo-henrique-4a849139/)
