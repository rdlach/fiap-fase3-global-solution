# FloodGuard — Global Solution FIAP | Fase 3

Aplicação em Python para registrar, consultar e acompanhar ocorrências urbanas relacionadas a alagamentos, drenagem e infraestrutura comunitária.

Toda a interação será pelo terminal, com menu de opções. Os dados serão lidos e gravados em um arquivo CSV simples, usando o módulo `csv` da biblioteca padrão do Python.

## Escopo definido

- Cadastrar ocorrências com bairro, categoria, descrição e urgência.
- Consultar ocorrências e filtrar por bairro, categoria e status.
- Atualizar o status: aberta, em análise ou concluída.
- Exibir indicadores e ranking de problemas de drenagem por bairro a partir dos registros simulados.
- Carregar os registros ao iniciar e salvar alterações no CSV.

Categorias: iluminação, acessibilidade, limpeza e conservação. Urgências: baixa, média e alta.

Os registros e o atendimento são simulados. O sistema não representa monitoramento em tempo real.

## Tecnologias

Python, terminal, CSV, Git e GitHub. A aplicação usará a biblioteca padrão, sem dependências externas.

## Estrutura

- `src/`: código Python e interface pelo terminal.
- `tests/`: testes e cenários de validação.
- `docs/`: especificação e documentação.
- `dados/`: arquivo CSV das ocorrências.
- `entregas/`: relatório, apresentação e links finais.

## Estado atual

Estrutura inicial criada. A implementação ainda não começou.

A proposta técnica está em [docs/especificacao.md](docs/especificacao.md). A aderência aos requisitos da FIAP deverá ser conferida com o enunciado oficial.
