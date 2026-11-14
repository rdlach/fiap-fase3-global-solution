# FloodGuard — Global Solution FIAP | Fase 3

Protótipo em Python para registrar e acompanhar demandas comunitárias na região central de São Paulo. Toda a interação acontece pelo terminal; os registros e o atendimento são simulados.

## Escopo

- Oito distritos e 18 nomes de bairros de referência do Centro.
- Cadastro com localização, categoria, tipo, descrição inicial e revisão antes de salvar.
- Consulta por distrito, bairro, categoria ou status.
- Solicitações adicionais vinculadas explicitamente a uma ocorrência existente.
- Visão da comunidade com prioridade simplificada; painel da equipe com pontuação e fila ordenada.
- Atualização de status, indicadores básicos e avanço de dias simulados.
- Persistência local em CSV e TXT, sem serviços externos durante o uso.

## Como executar

Na pasta do projeto:

```bash
python src/sistema.py
```

No Windows: `py src/sistema.py`. A entrada `src/main.py` continua funcionando. Usa somente biblioteca padrão, sem instalação de pacotes.

Ao iniciar, escolher `1. Comunidade`, `2. Equipe de acompanhamento` ou `0. Encerrar`. Os perfis são simulados por menus, sem autenticação ou controle de acesso real.

## Comunidade

1. Registrar um novo problema.
2. Consultar ocorrências.
3. Reforçar uma ocorrência existente.
4. Ver resumo.
5. Ver pendências por bairro.
0. Voltar.

A comunidade vê problema, status e prioridade (Baixa, Média, Alta ou Crítico). Pontos, fórmula e ordenação interna ficam no painel da equipe.

Ao reforçar, informar o código da ocorrência, conferir se é o mesmo problema e confirmar com `s`. Isso acrescenta uma solicitação ao mesmo registro, mantendo seu ID. Uma ocorrência diferente, mesmo no mesmo bairro e categoria, deve ser cadastrada separadamente. Ocorrências concluídas não recebem reforços.

## Equipe de acompanhamento

1. Ver fila por pontuação.
2. Atualizar status.
3. Avançar dias da simulação.
4. Ver resumo.
0. Voltar.

A fila apresenta primeiro a maior pontuação, inclusive entre ocorrências Críticas. Em empate, atende à abertura mais antiga e depois ao menor código numérico. Concluídas ficam fora da fila.

A equipe vê a decomposição da pontuação em base, dias e solicitações adicionais. O dia simulado atualizado na equipe também passa a valer para as consultas da comunidade.

## Cadastro e navegação

Fluxo: distrito → bairro → categoria → tipo → descrição/complemento → revisão.

- `0` volta uma etapa. Na seleção inicial da localização, cancela o cadastro. No menu principal, encerra o programa.
- A descrição inicial pode ser aceita com Enter; o complemento é opcional. Outro problema exige descrição.
- Ao editar complemento, Enter mantém, um texto novo substitui o complemento anterior e `-` remove o complemento.
- Na revisão: `1` salva, `2` altera bairro, `3` altera descrição, `4` altera categoria, `5` apresenta uma orientação geral sobre a prioridade, `6` cancela e `7` altera tipo.
- Alterar categoria ou tipo exige conferir os campos dependentes. Desistir da edição preserva os valores anteriores.
- Nenhum cadastro ou reforço é gravado antes da confirmação correspondente.

## Recorte central

| Distrito | Bairros de referência no catálogo |
| --- | --- |
| Bela Vista | Bela Vista; Morro dos Ingleses |
| Bom Retiro | Bom Retiro; Luz |
| Cambuci | Cambuci; Vila Deodoro |
| Consolação | Consolação; Higienópolis; Pacaembu; Vila Buarque |
| Liberdade | Aclimação; Liberdade |
| República | República; Santa Efigênia |
| Santa Cecília | Barra Funda; Campos Elíseos; Santa Cecília |
| Sé | Centro |

A opção `9. Buscar bairro pelo nome` encontra parte do nome, ignorando acentos e maiúsculas. O nome digitado não cria bairro: o usuário escolhe um preset por número. O recorte corresponde à região Centro da Seade; as associações bairro/distrito são referências da base de origem, documentadas em [docs/catalogo_sao_paulo.md](docs/catalogo_sao_paulo.md).

## Categorias e tipos

| Categoria | Tipos predefinidos |
| --- | --- |
| Iluminação | Poste apagado; Luz piscando; Iluminação danificada; Poste danificado; Fiação elétrica exposta; Iluminação bloqueada por vegetação |
| Acessibilidade | Rampa obstruída; Calçada sem passagem; Piso tátil danificado; Escadaria sem corrimão; Travessia sem acesso rebaixado; Banheiro público sem acessibilidade |
| Limpeza | Lixo acumulado; Descarte de entulho; Bueiro com lixo; Esgoto a céu aberto; Animal morto em espaço público; Banheiro público sem limpeza |
| Conservação | Buraco na rua; Banco danificado; Brinquedo de praça quebrado; Vazamento de água; Árvore caída em espaço público; Sinalização de trânsito danificada |

São 24 tipos com descrição inicial e nível inicial. Cada categoria também tem Outro problema, na opção 7. Os presets ficam em um dicionário de listas, sem banco de dados ou framework.

## Pontuação interna

`pontos = base do tipo + dias desde abertura + solicitações adicionais vinculadas`.

| Base inicial | Pontos |
| --- | --- |
| Baixa | 0 |
| Média | 3 |
| Alta | 6 |

Cada dia simulado e cada solicitação adicional somam um ponto. A primeira solicitação já está representada pelo cadastro e não conta como adicional. A pontuação não tem teto e os reforços confirmados não são subtraídos quando outros registros são concluídos.

| Pontos | Prioridade pública |
| --- | --- |
| 0 a 2 | Baixa |
| 3 a 5 | Média |
| 6 a 8 | Alta |
| 9 ou mais | Crítico |

Exemplo: base Baixa, três dias e quatro solicitações no total: `0 + 3 + (4 - 1) = 6`, prioridade Alta. Os detalhes e níveis iniciais dos tipos estão em [docs/prioridades.md](docs/prioridades.md).

## Arquivos

- `src/`: funções, menus, catálogo de localidades e cálculo de prioridade.
- `dados/bairros_sp.csv`: 18 presets do recorte central, com IDs estáveis.
- `dados/distritos_sp.csv`: os oito distritos centrais e suas subprefeituras.
- `dados/ocorrencias_exemplo.csv`: 12 registros fictícios versionados para demonstração.
- `dados/ocorrencias.csv`: ocorrências de uso local; preservado no computador e ignorado pelo Git.
- `dados/dia_simulado.txt`: dia atual; criado no primeiro avanço confirmado. Sem esse arquivo, a simulação começa no dia 1.
- `docs/`: decisões, fontes, regras e registro de IA.
- `tests/`: roteiros e resultados de verificações de cada etapa.
- `entregas/`: arquivos finais da entrega acadêmica.

Formatos anteriores do CSV continuam aceitos. Registros sem contador recebem uma solicitação inicial; registros sem abertura recebem dia 1 por convenção. A leitura preserva o arquivo; a próxima alteração confirmada grava o formato atual.

## Estado e validação

O roteiro atual está em [tests/cenarios_pontuacao.md](tests/cenarios_pontuacao.md). A revisão executou 31 testes reproduzíveis com arquivos temporários, sem falhas, registrados em [tests/resultado_revisao.json](tests/resultado_revisao.json). Para repetir: `python -m unittest discover -s tests -v`. A equipe deve reproduzir e revisar os resultados. O código dos testes está em [tests/test_sistema.py](tests/test_sistema.py).

Os presets não criam relatos automaticamente. Uma base opcional com 12 ocorrências fictícias está disponível em `dados/ocorrencias_exemplo.csv`. O histórico de oito eventos e outros requisitos acadêmicos ainda precisam ser completados; a lista está em [docs/mudancas.md](docs/mudancas.md).

O apoio de IA está registrado em [docs/uso_ia.md](docs/uso_ia.md). A especificação atual está em [docs/especificacao.md](docs/especificacao.md).

A explicação das mudanças e da revisão está em [docs/mudancas.md](docs/mudancas.md). Para executar ou usar os exemplos em outra cópia limpa, seguir [docs/guia_execucao.md](docs/guia_execucao.md).
