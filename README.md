# Introdução Desafio Jusbrasil

Projeto desenvolvido a partir de desafio feito pela empresa Jusbrasil.

# Descrição

Este projeto simula um cenário real de scraping jurídico em produção, onde o site alvo possui autenticação dinâmica, limitação de requisições e mudanças frequentes de comportamento. A solução implementa uma arquitetura em camadas, tratamento robusto de falhas e mecanismos de cache para garantir estabilidade e performance.

## 📖 Sumário

1. [Introdução](#introdução-desafio-jusbrasil)  
2. [Descrição](#descrição)  
3. [Iniciando](#iniciando)  
   - [Dependências](#dependências)  
   - [Instalação](#instalação)  
   - [Executando o Projeto](#executando-projeto)  
4. [Funcionalidades da API](#funcionalidades-da-api)  
   - [Buscando processo](#buscando-processo)
   - [Verificando o Status do Serviço](#verificando-o-status-do-serviço) 
5. [Executando os Testes](#executando-os-testes)
6. [Relatório  Final](#relatório-final)
7. [Autor](#autor)  

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
docker compose -f docker-compose.prod.yml build
```
* O docker irá buildar a imagem, depois rode. 
```
docker compose -f docker-compose.prod.yml up
```
* O container com api irá subir.
## Funcionalidades da API
### Buscando processo

#### Exemplo de Chamada

```
curl -X POST \
    "http://0.0.0.0:8000/search_npu?force_refresh=true" \
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
| force_refresh| boolean| Força nova consulta ao tribunal, ignorando o cache |

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
        {"status":"ok",
         "api":"ok",
         "tribunal_site":"ok",
         "response_time_ms":812.19}
}
```

### Executando os Testes
#### No Windows
* Abrir terminal ou powershell
* Navegar até a pasta do projeto
* Buildar o docker com as bibliotecas de teste 
```
docker compose build --no-cache
```
* Para executar o docker e os testes rode
```
docker compose run --rm api poetry run pytest -q
```  
* Os testes devem executar automaticamente e o resultado será exibido na tela

# Relatório Final
## Descrição da fonte e dos principais desafios técnicos encontrados
* A fonte utilizada foi a consulta processual do TJRS(Tribunal de Justiça do Estado do Rio Grande do Sul).
### Principais desafios técnicos
* Entre os principais desafios, destaca-se o processo de investigação do mecanismo de acesso ao site, que envolveu a identificação da existência de um token de autenticação, a compreensão de como esse token é gerado e a recriação do seu processo de formação. O token era composto por um challenge e por um segredo gerado a partir de código identificado nos initiators da ferramenta de desenvolvedor do navegador. Além disso, durante o desenvolvimento, o site alterou o método de geração desse segredo em duas ocasiões, o que motivou a criação de uma automação capaz de extrair dinamicamente os números utilizados na formação do segredo.
* Outro desafio foi lidar com erros HTTP 429 (limite de requisições permitidas). Esse problema foi contornado por meio de um mecanismo de retentativas com tempo de espera (retry com backoff), evitando que a API retornasse erros de forma imediata. Além disso, foi implementado um sistema de cache com Redis para reduzir consultas desnecessárias quando uma busca já havia sido realizada anteriormente.
##Estratégias adotadas para realizar a coleta
* A coleta dos dados foi relativamente simples, uma vez que o site disponibiliza as informações em formato JSON. Assim, foi necessário apenas realizar o parse das respostas e extrair os campos de interesse.
## Resultados obtidos com o protótipo
* O protótipo desenvolvido demonstrou ser capaz de realizar consultas automatizadas ao sistema do TJRS de forma eficiente e confiável. A solução implementada permitiu a obtenção dos dados processuais por meio da reprodução do mecanismo de autenticação do site, incluindo a resolução do challenge e a geração do token de acesso. Além disso, o protótipo incorporou mecanismos de tratamento de erros, como retentativas com controle de tempo de espera para lidar com limitações de requisições (HTTP 429), e um sistema de cache baseado em Redis, que reduziu significativamente o número de consultas repetidas ao servidor. Como resultado, o sistema apresentou maior estabilidade, desempenho e resiliência frente às variações do comportamento do site.
## Validações implementadas para garantir qualidade dos dados;
* Foram implementadas validações para garantir a qualidade e a consistência dos dados coletados. Entre essas validações, destacam-se a verificação do formato do número do processo (NPU), o tratamento de respostas inválidas ou incompletas do servidor, a validação da estrutura dos dados retornados em JSON e o controle de erros durante o processo de extração. Essas medidas contribuíram para assegurar a confiabilidade das informações obtidas pelo protótipo.
## Possíveis melhorias para reduzir falhas e facilitar manutenção
* Melhorar a resiliência à mudança do JavaScript do site: reduzir dependência de regex “frágeis” e adicionar validações/fallbacks na extração do algoritmo de obfuscação (por exemplo, verificar se os dois BigInt numéricos foram encontrados e registrar alerta quando o padrão mudar).
* Cache distribuído para parâmetros do segredo e do token: além do cache do resultado da consulta (Redis), armazenar também o main.js/BigInts e o token em cache compartilhado com TTL curto. Isso reduz recomputações em múltiplos workers e diminui a quantidade de requisições ao TJRS.
* Controle de concorrência com lock distribuído: em cenários com múltiplas instâncias, aplicar lock no Redis para evitar que vários workers tentem regenerar token/segredo ao mesmo tempo, reduzindo picos de requisições e chances de 401/429.
* Backoff mais aderente ao upstream: priorizar o header Retry-After quando presente e manter jitter no backoff, reduzindo falhas recorrentes por rate limit.
* Observabilidade e diagnósticos: incluir logs estruturados (com npu, comarca, tentativa, status code e origem cache/upstream) e métricas (taxa de 401/429/5xx e tempo de resposta) para facilitar detecção de mudanças no site e acelerar a manutenção.
* Expansão e refinamento dos testes automatizados: adicionar testes específicos para cenários críticos (401 → refresh do token; 429 → backoff; retorno HTML; JSON inválido; indisponibilidade do Redis), reduzindo regressões e aumentando confiabilidade.
## Autor
[Paulo Henrique De Souza Gomes](https://www.linkedin.com/in/paulo-henrique-4a849139/)
