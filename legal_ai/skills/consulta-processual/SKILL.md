---
name: consulta-processual
description: Consulta dados de um processo judicial quando o usuário fornece ou referencia um NPU e os dados ainda não estão disponíveis.
---

# Consulta processual

Use esta skill quando o usuário solicitar informações sobre um processo.

## Regras

1. Identifique o NPU informado pelo usuário.
2. Se o processo já estiver disponível em `process_data`, reutilize os dados.
3. Não faça nova consulta externa desnecessariamente.
4. Se os dados não estiverem disponíveis, utilize a tool `consultar_processo`.
5. Responda apenas com informações presentes nos dados retornados.
6. Não invente informações processuais.