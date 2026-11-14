# Mudanças do protótipo e resultado da revisão

Revisão de 14/11/2026, comparando a implementação atual com a versão inicial do FloodGuard, commit `0e8ca60`.

## Problema e comportamento resultante

O cadastro inicial aceitava qualquer grafia de bairro, exigia preencher tudo antes de cancelar e deixava a urgência a critério de quem cadastrava. A aplicação atual usa localidades e problemas predefinidos, permite voltar e corrigir o preenchimento e calcula a prioridade com regras explícitas.

A comunidade consulta uma prioridade compreensível. A equipe acompanha uma fila ordenada por pontuação, inclusive entre ocorrências que já estão no nível Crítico.

| Área | Versão inicial | Implementação atual |
| --- | --- | --- |
| Localização | Bairro digitado livremente | Escolha por distrito e bairro, com busca por parte do nome |
| Cobertura | Sem recorte definido | Oito distritos e 18 bairros de referência da região central de São Paulo |
| Problema | Categoria e descrição manual | Quatro categorias, 24 tipos com descrição inicial e Outro em cada categoria |
| Navegação | Confirmação apenas no final | Voltar, preservar preenchimento, revisar e corrigir antes de salvar |
| Urgência | Escolhida no cadastro | Base predefinida por tipo e prioridade calculada |
| Solicitações adicionais | Novos registros independentes | Reforço explícito por código, acumulado na mesma ocorrência |
| Atendimento | Status e ranking por bairro | Painel da equipe com pontuação, parcelas do cálculo e fila ordenada |
| Dados | CSV com seis campos | CSV com histórico e leitura compatível com formatos anteriores |
| Execução | `python3 src/main.py` | `python src/sistema.py`, mantendo a entrada anterior |

## Organização do código

| Arquivo | Responsabilidade |
| --- | --- |
| `src/sistema.py` | Iniciar a aplicação pelo comando pedido no enunciado |
| `src/main.py` | Menus, cadastro, consultas, reforços, status, resumo e persistência das ocorrências |
| `src/localidades.py` | Ler e validar distritos e bairros e oferecer escolha por número ou busca |
| `src/prioridades.py` | Níveis iniciais, pontuação e leitura/gravação do dia simulado |

A aplicação usa funções, condicionais, laços, listas, dicionários, tuplas e operações simples. Não usa classes de negócio, banco de dados, APIs ou bibliotecas externas. A revisão substituiu as compreensões, expressões geradoras e `lambda` por laços e funções com nome.

`sorted` é uma função do Python. A chave da fila é uma tupla: pontuação negativa para ordenar do maior para o menor, dia de abertura crescente e código numérico crescente. Isso explica o desempate sem criar um algoritmo avançado. Os testes usam `unittest` da biblioteca padrão, em arquivo separado do código da aplicação.

## Pontuação e reforços

`pontos = base + (dia_atual - dia_abertura) + (solicitacoes - 1)`.

Base: Baixa = 0, Média = 3 e Alta = 6. A prioridade apresentada é Baixa para 0–2, Média para 3–5, Alta para 6–8 e Crítico para 9 ou mais. A pontuação numérica não tem limite artificial.

Exemplo: um relato inicialmente Baixa, com três dias e quatro solicitações vinculadas, soma `0 + 3 + 3 = 6`, prioridade Alta. Uma ocorrência com 30 pontos aparece antes de outra com 12, mesmo que ambas sejam Críticas.

O cadastro representa a primeira solicitação. A ação Reforçar exige código e confirmação do problema antes de acrescentar outra. O programa não assume que todo relato do mesmo bairro e tipo é o mesmo problema. O total é acumulado, sem subtração por encerramento de outras ocorrências.

Concluídas saem da fila e não recebem reforços. Uma reabertura mantém a data inicial e o contador; as mudanças de status ficam no histórico. A equipe pode avançar o dia simulado. O valor confirmado fica em um TXT.

## CSVs e preservação dos dados

| Arquivo | Finalidade | Entra no versionamento? |
| --- | --- | --- |
| `dados/distritos_sp.csv` | Oito distritos do Centro e metadados de referência | Sim |
| `dados/bairros_sp.csv` | 18 bairros de referência com IDs estáveis | Sim |
| `dados/ocorrencias_exemplo.csv` | Doze registros fictícios para demonstração e testes | Sim |
| `dados/ocorrencias.csv` | Registros criados no uso local | Não; preservado no computador e ignorado pelo Git |
| `dados/dia_simulado.txt` | Dia atual do uso local | Não; criado após avanço confirmado e ignorado pelo Git |

Os leitores aceitam UTF-8 com ou sem BOM. O separador é vírgula; o módulo `csv` preserva acentos, aspas, vírgulas e quebras dentro dos campos. CSVs inválidos são sinalizados, sem sobrescrita silenciosa.

O cabeçalho atual é:

```text
id,id_bairro,bairro,zona,distrito,categoria,tipo,descricao,urgencia,status,dia_abertura,solicitacoes
```

| Campo | Significado e regra |
| --- | --- |
| `id` | Código único positivo no padrão FG-001; após 999, a numeração continua normalmente |
| `id_bairro` | ID estável do catálogo de bairros |
| `bairro`, `zona`, `distrito` | Valores correspondentes ao preset; zona sempre Centro |
| `categoria` | Uma das quatro categorias obrigatórias |
| `tipo` | Um tipo compatível com a categoria ou Outro |
| `descricao` | Texto não vazio, gerado ou preenchido pelo usuário |
| `urgencia` | Nível inicial Baixa, Média ou Alta; não guarda a pontuação derivada |
| `status` | Aberta, Em análise ou Concluída |
| `dia_abertura` | Inteiro positivo, não posterior ao dia atual |
| `solicitacoes` | Total inteiro positivo, incluindo a primeira solicitação |
| `historico` | Lista JSON com a ordem, o código, o dia e os dois status de cada mudança |

Formatos anteriores de seis, nove, dez, onze e doze campos continuam aceitos. Dados sem abertura recebem dia 1 por convenção; sem contador, recebem 1. Descrições e IDs são preservados. A leitura não regrava o arquivo: a próxima alteração confirmada usa o formato atual.

Os dois catálogos são conferidos em conjunto. Cabeçalho, campos obrigatórios, repetições, recorte central e cobertura dos oito distritos são validados. As fontes e limitações geográficas estão em [catalogo_sao_paulo.md](catalogo_sao_paulo.md).

## Verificações reproduzíveis

Na raiz do projeto:

```bash
python -m unittest discover -s tests -v
```

No Windows, pode-se substituir `python` por `py`. Resultado da revisão: **31 testes aprovados**, sem falhas ou erros, em Python 3.14.7. Os testes usam arquivos temporários e não modificam os registros de uso.

Foram conferidos os 18 bairros, os 24 tipos, codificação dos CSVs, migração, IDs, campos ausentes e inconsistentes, contadores, cancelamento, navegação, reforços, falha de gravação, privacidade das informações na interface, pontuação sem teto, ordenação e fluxo real em outro processo com reinício.

O resumo está em `tests/resultado_revisao.json`; o código reproduzível, em `tests/test_sistema.py`. Relatórios intermediários foram preservados fora do conjunto do commit, na pasta de análise do workspace, para evitar confusão com as regras atuais.

## Situação da entrega acadêmica

Esta revisão valida o comportamento implementado; não certifica o cumprimento integral da Global Solution.

- A base de exemplo do terminal tem 12 ocorrências e 10 mudanças de status.
- A equipe pode consultar a fila FIFO, a fila por pontuação, o histórico e a pilha de últimas atualizações.
- O resumo tem matriz, percentuais e média de solicitações. A comunidade pode navegar pelo agrupamento por bairro e categoria.
- Para a entrega final, preencher os RMs, confirmar a opção de competição, gravar o vídeo e montar o TXT com os links.
- Conferir a tabela específica de arquivos da atividade no FIAP ON e a organização exigida pelo modelo oficial.
- Os perfis são simulados por menus, sem autenticação. A aplicação deve ser usada por uma instância de cada vez; não há sincronização de gravações entre sessões.

As solicitações não identificam moradores; quantidades não equivalem a pessoas distintas. Os dados de demonstração são fictícios e os critérios de pontuação são acadêmicos, sem conexão com serviços públicos.
