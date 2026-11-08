# FloodGuard — especificação inicial

## Decisões confirmadas

- Projeto da Global Solution da Fase 3.
- Aplicação Python com interação exclusivamente pelo terminal.
- Persistência em um arquivo CSV simples: `dados/ocorrencias.csv`.
- Uso de dados simulados, sem serviços externos, sensores ou banco de dados.

## Modelo proposto de ocorrência

Cabeçalho do CSV: `id,bairro,categoria,descricao,urgencia,status`.

- `id`: identificador único e estável, como FG-001.
- `bairro`: nome obrigatório, sem espaços excedentes.
- `categoria`: iluminação, acessibilidade, limpeza ou conservação.
- `descricao`: texto obrigatório explicando o problema.
- `urgencia`: baixa, média ou alta.
- `status`: aberta, em análise ou concluída; começa como aberta.

Ler e escrever em UTF-8 pelo módulo `csv`, preservando acentos, vírgulas e aspas nos campos. Usar `newline=""` ao abrir o arquivo. Criar o CSV com cabeçalho quando ainda não existir; não sobrescrever um arquivo ilegível ou inválido silenciosamente. Salvar após cada alteração bem-sucedida e preservar os identificadores ao reiniciar.

## Menu proposto

1. Cadastrar ocorrência.
2. Listar e filtrar ocorrências.
3. Atualizar status.
4. Exibir indicadores.
5. Exibir ranking por bairro.
0. Sair.

Entradas inválidas devem mostrar uma mensagem e permitir nova tentativa.

## Indicadores e ranking propostos

Exibir total de ocorrências e quantidade por status. O ranking contará ocorrências ainda não concluídas por bairro, em ordem decrescente de quantidade, com desempate pelo nome do bairro. O resultado descreve apenas os registros simulados cadastrados; não mede risco real de inundação.

## Estruturas de dados previstas

A proposta menciona listas, filas, pilhas, dicionários, matrizes e a hierarquia bairro → categoria → ocorrências. A aplicação concreta de cada estrutura deve ser definida após conferir o enunciado oficial, evitando presumir requisitos apenas a partir da proposta.

## Validação prevista

Verificar cadastro, filtros, atualização de status, ranking, entradas inválidas e persistência após reiniciar. Incluir descrições com acentos, vírgulas e aspas para validar a leitura e a gravação do CSV.
