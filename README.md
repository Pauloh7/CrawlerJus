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
         "npu": "5056077-84.2025.8.21.0008"
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
  "numeroProcesso": "5056077-84.2025.8.21.0008",
  "numeroProcessoCNJ": "50560778420258210008",
  "classeCNJ": "CUMPRIMENTO DE SENTENÇA",
  "assuntoCNJ": "Compromisso, Espécies de contratos, Obrigações, DIREITO CIVIL",
  "nomeClasse": "CUMPRIMENTO DE SENTENÇA",
  "nomeNatureza": "Compromisso, Espécies de contratos, Obrigações, DIREITO CIVIL",
  "comarca": "CANOAS",
  "codigoComarca": "8",
  "dataDistribuicao": "04/12/2025 09:25:41",
  "dataPropositura": null,
  "situacaoProcesso": "MOVIMENTO",
  "segredoJustica": false,
  "tipoProcesso": "EPROC",
  "orgaoJulgador": "1º Juízo da 2ª Vara Cível da Comarca de Canoas",
  "partes": [
    {
      "descricaoTipo": "EXEQUENTE",
      "nome": "SERAFINI ADVOGADOS"
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
  "processosVinculados": [
    {
      "numeroProcesso": "50019831220138210008",
      "numeroFormatado": null,
      "classe": null,
      "assunto": null,
      "comarca": "0008",
      "orgaoJulgador": null,
      "ultimaMovimentacao": null
    }
  ],
  "movimentos": [
    {
      "data": "21/01/2026",
      "descricao": "Publicado no DJEN - no dia 21/01/2026 - Refer. ao Evento: 4"
    },
    {
      "data": "13/01/2026",
      "descricao": "PETIÇÃO PROTOCOLADA JUNTADA - PETIÇÃO"
    },
    {
      "data": "12/01/2026",
      "descricao": "PETIÇÃO PROTOCOLADA JUNTADA - PETIÇÃO"
    },
    {
      "data": "09/01/2026",
      "descricao": "Ato cumprido pela parte ou interessado - depósito de bens/dinheiro - Confirmação de recolhimento - GUIA DE DEPÓSITO: 265002332"
    },
    {
      "data": "31/12/2025",
      "descricao": "Ato Ordinatório - Vinculado depósito judicial BACENJUD/SISBAJUD - GUIA: 255823179"
    },
    {
      "data": "28/12/2025",
      "descricao": "Confirmada a intimação eletrônica - Refer. ao Evento: 5 - Ciência Tácita"
    },
    {
      "data": "19/12/2025",
      "descricao": "Disponibilizado no DJEN - no dia 19/12/2025 - Refer. ao Evento: 4"
    },
    {
      "data": "18/12/2025",
      "descricao": "Expedida/certificada a intimação eletrônica (EXECUTADO -  PETRÓLEO BRASILEIRO S/A - PETROBRÁS)  prazo: 30 dias  Data final: 09/03/2026 23:59:59"
    },
    {
      "data": "18/12/2025",
      "descricao": "Expedida/certificada a intimação eletrônica (EXECUTADO -  BANCO BRADESCO S.A.)  prazo: 30 dias  Data final: 09/03/2026 23:59:59"
    },
    {
      "data": "18/12/2025",
      "descricao": "Proferido despacho de mero expediente"
    },
    {
      "data": "04/12/2025",
      "descricao": "Conclusos pra decisão/despacho"
    },
    {
      "data": "04/12/2025",
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
* A fonte escolhida foi o sistema de consulta processual do TJRS (Tribunal de Justiça do Rio Grande do Sul).
### Principais desafios técnicos
O maior desafio foi descobrir como o site autentica as requisições. Ele usa um token que depende de um "challenge" e de um segredo escondido no JavaScript. Precisei fazer engenharia reversa no main.js para entender o algoritmo — basicamente, dois números BigInt que mudam o hash. No meio do desenvolvimento, o site mudou a forma como esses números aparecem no código duas vezes em poucos dias. Foi frustrante, mas acabou virando oportunidade: criei uma lógica que busca esses valores dinamicamente no JS, em vez de ficar com números fixos.

Outro problema recorrente foi o rate limit (HTTP 429). O TJRS limita bastante as chamadas, e quando bate, trava tudo. Tive que implementar retentativas com backoff, detectar o erro tanto pelo status quanto pelo corpo da resposta, e usar cache no Redis para não sobrecarregar o servidor com a mesma consulta.
## Estratégias adotadas para realizar a coleta
Fiz tudo com requisições HTTP puras (usando curl_cffi para simular browser), sem Selenium nem Playwright — exatamente como o desafio pedia, para ficar leve e rápido.
#### Depois de entender o fluxo de autenticação, reproduzi a geração do token em Python: resolvi o challenge com SHA-256 e brute force limitado pelo maxnumber que o servidor manda. para deixar mais robusto, criei exceções específicas para cada tipo de erro:
* 401/403 → renova o token automaticamente
* 429 → backoff + retry-after quando tem header
* 5xx ou HTML inesperado → erro de upstream
* JSON quebrado → erro de parsing
Coloquei cache no Redis para guardar tanto o resultado da consulta quanto o token (TTL curto), evitando regenerar o segredo toda hora. Depois que a resposta chega, faço uma limpeza rápida, valido os campos principais e monto um JSON organizado.
## Resultados obtidos com o protótipo
No final, o protótipo funciona bem estável. Consegue consultar processos do TJRS de forma automática, reproduzindo o auth do site (inclusive o challenge obfuscado), tratando erros comuns e usando cache para não abusar do servidor.
Testei com vários NPUs reais e o cache reduziu bastante as chamadas repetidas. A solução suporta variações do site melhor do que uma versão estática, e quando bate rate limit, não trava: espera, tenta de novo e continua.
## Validações implementadas para garantir qualidade dos dados
Adicionei várias camadas de validação evitando o retorno de dados indesejados:
* Verifico se o NPU tem 20 dígitos e calculo o dígito verificador (módulo 97) para garantir que é válido
* Checo se a resposta veio como JSON válido e com a estrutura esperada
* Trato respostas incompletas ou com campos nulos de forma graciosa (sem crashar)
* No parsing, uso try/except para capturar qualquer erro de extração e levantar exceção customizada
Isso ajuda a evitar que dados errados ou parciais cheguem ao cliente.
## Possíveis melhorias para reduzir falhas e facilitar manutenção
* Tornar a extração dos BigInts menos dependente de regex (talvez usar AST ou parser JS leve para encontrar os valores de forma mais segura)
* Cachear também o main.js e o token em Redis com TTL bem curto, para múltiplas instâncias não ficarem baixando tudo de novo
* Usar lock distribuído no Redis quando vários workers tentam regenerar o token ao mesmo tempo (evita picos de 401/429)
* Respeitar mais o Retry-After do header quando vem, e adicionar jitter no backoff para parecer mais "humano"
* Colocar logs estruturados (com JSON) e métricas simples (quantas 429, tempo médio de resposta, hit rate do cache) para facilitar debug quando o site mudar de novo
* Expandir os testes para cobrir mais cenários ruins: token expirado, Redis down, resposta HTML no lugar de JSON, etc.
No geral, foi um projeto ótimo de se fazer e bem desafiador — exigiu bastante debug e paciência, mas no final gerou algo que realmente funciona em produção.
## Autor
[Paulo Henrique De Souza Gomes](https://www.linkedin.com/in/paulo-henrique-4a849139/)
