# Introdução Desafio Jusbrasil

Projeto desenvolvido a partir de desafio feito pela empresa Jusbrasil.

# Descrição

Este projeto tem como objetivo montar uma aplicação REST para extrair dados de processo do site TJRS. A aplicação estará rodando dentro de um docker que receberá as requisições, irá processá-las e entregar os resultados correspondentes.

## 📖 Sumário

1. [Introdução](#introdução-desafio-jusbrasil)  
2. [Descrição](#descrição)  
3. [Iniciando](#iniciando)  
   - [Dependências](#dependências)  
   - [Instalação](#instalação)  
   - [Executando o Projeto](#executando-projeto)  
4. [Funcionalidades da API](#funcionalidades-da-api)  
   - [Buscando processo](#buscando-processo)  
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
git clone git@github.com:Pauloh7/CrawlerJus.git
```
## Executando Projeto
##### Buildar docker e subir aplicação.
* Abrir terminal ou powershell
* Navegar até a pasta do projeto
* Executar o comando
```
docker build -t crawler_jus .
```
* O docker irá buildar a imagem. Então rode o comando
```
docker run --rm -p 8000:8000 crawler_jus
```
## Funcionalidades da API
### Buscando processo

#### Exemplo de Chamada

```
curl -X POST \
    "http://0.0.0.0:8000/search_npu" \
    -H "Content-Type: application/json" \
    -H "Accept: application/json" \
    -d '{
         "npu": "5001646-66.2026.8.21.0008"
        }'
```

#### Parâmetros da Requisição

| Parâmetro  | Tipo   | Descrição |
|------------|--------|-------------|
| npu       | string | Número do processo a ser extraido |

#### Exemplo de Resposta

```
HTTP/1.1 200 OK
Content-Type: application/json

{
  "nomeClasse": "CUMPRIMENTO DE SENTENÇA",
  "nomeNatureza": "Compromisso, Espécies de contratos, Obrigações, DIREITO CIVIL",
  "classeCNJ": "CUMPRIMENTO DE SENTENÇA",
  "assuntoCNJ": "Compromisso, Espécies de contratos, Obrigações, DIREITO CIVIL",
  "partes": [
    {
      "descricaoTipo": "EXEQUENTE",
      "nome": "UNIFERTIL - UNIVERSAL DE FERTILIZANTES S/A"
    },
    {
      "descricaoTipo": "EXECUTADO",
      "nome": "BANCO BRADESCO S.A."
    },
    {
      "descricaoTipo": "EXECUTADO",
      "nome": "PETRÓLEO BRASILEIRO S/A - PETROBRÁS"
    }
  ],
  "movimentos": [
    {
      "data": "15/01/2026",
      "descricao": "Conclusos para decisão/despacho"
    },
    {
      "data": "15/01/2026",
      "descricao": "Distribuído por dependência (CAN2CIV1J) - Número: 50019831220138210008/RS"
    }
  ]
}
```


### Executando os Testes
#### No Windows
* Abrir terminal ou powershell
* Navegar até a pasta do projeto
* Buildar o docker com as bibliotecas de teste 
```
docker build -t crawler_jus --build-arg ENV=dev .
```
* Para executar o docker e os testes rode
```
docker run --rm -it -w /crawlerjus crawler_jus pytest -q
```  
* Os testes devem executar automaticamente e o resultado será exibido na tela
## Autor

[Paulo Henrique De Souza Gomes](https://www.linkedin.com/in/paulo-henrique-4a849139/)
