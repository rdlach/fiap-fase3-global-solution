# Especificação do protótipo FloodGuard

## Escopo e execução

Interface pelo terminal, Python básico e biblioteca padrão. Recorte: oito distritos e 18 bairros de referência da região central de São Paulo. Executar `python src/sistema.py` ou `py src/sistema.py` no Windows.

## Dados

CSV: `id,id_bairro,bairro,zona,distrito,categoria,tipo,descricao,urgencia,status,dia_abertura,solicitacoes`.

ID único `FG-001`; localização escolhida no catálogo; categoria entre as quatro obrigatórias; tipo compatível; descrição obrigatória, gerada nos presets ou preenchida em Outro; nível inicial Baixa, Média ou Alta; status Aberta, Em análise ou Concluída; abertura inteira positiva e não posterior ao dia atual; solicitações como inteiro positivo, inicialmente 1.

Os CSVs de seis, nove, dez e onze campos anteriores continuam aceitos. Preencher campos ausentes por regras documentadas: tipo Outro da categoria, localização por correspondência única, abertura dia 1 e contador 1. Preservar valores existentes. Não sobrescrever arquivo inválido ou regravar apenas por consultar. Salvar após confirmação usando arquivo temporário e substituição.

## Estruturas e funções

Lista de dicionários para as ocorrências e os presets; dicionário de listas para os 24 tipos; dicionário para descrições e níveis iniciais. A fila de atendimento é uma lista derivada dos pendentes, ordenada por pontos, abertura e código. O menu da equipe também tem uma fila FIFO que mostra os pendentes pelo código de registro.

O cálculo usa `pontos = base + dias + (solicitacoes - 1)`, com base 0, 3 ou 6 e sem teto. A prioridade pública segue 0–2 Baixa, 3–5 Média, 6–8 Alta e 9+ Crítico. Detalhes em `docs/prioridades.md`.

## Menus e navegação

Menu principal: Comunidade, Equipe de acompanhamento ou encerrar. São perfis simulados, sem autenticação.

Comunidade: cadastrar, consultar, reforçar ocorrência, resumo e pendências por bairro. Mostra prioridade simplificada, sem pontos, fórmula ou componentes internos.

Equipe: fila com pontuação, atualizar status, avançar dias simulados e resumo. Mostra pontos e componentes, com fila decrescente e desempate por abertura e ID. O dia atualizado é retornado ao menu principal para uso nas próximas consultas da comunidade.

Cadastro: distrito → bairro → categoria → tipo → descrição → revisão. Usar 0 para voltar, preservar preenchimento e permitir correções antes de salvar. A revisão oferece salvar, alterar campos, orientação geral ou cancelar. Mudar categoria exige tipo e descrição compatíveis.

Reforço: consultar pelo código, mostrar o problema e pedir confirmação explícita. Acrescentar uma solicitação ao mesmo registro. Não inferir vínculo por bairro ou tipo. Bloquear reforços em concluídas. Falha ou cancelamento não altera memória nem CSV.

Consultas: todos os registros ou filtros por distrito, bairro, categoria e status. Voltar de um filtro retorna à escolha de consulta. Na atualização de status, voltar da confirmação retorna à escolha do status, e voltar do status retorna ao código.

## Indicadores e limitações

O resumo mostra a matriz categoria × status, os totais, os percentuais e a média de solicitações por ocorrência. A consulta por bairro agrupa as ocorrências por categoria. A base de demonstração tem 12 ocorrências e 10 mudanças fictícias de status. No modo normal, cada mudança confirmada guarda o código, o dia, o status anterior e o novo status no mesmo CSV. O histórico mostra os eventos na ordem em que ocorreram. A pilha mostra o mais recente primeiro.

## Validação

Roteiro atual: `tests/cenarios_pontuacao.md`; resultados: `tests/resultado_revisao.json`. Conferir pontuação sem teto, faixas, exemplos aprovados, contagem explícita, ordenação entre críticos, reforços, cancelamento, gravação, datas, leitura dos formatos anteriores e separação das informações nos menus.

Os CSVs aceitam UTF-8 com ou sem BOM. Os catálogos de bairros e distritos são conferidos em conjunto; repetições e cobertura incompleta são rejeitadas. O código dos testes reproduzíveis está em `tests/test_sistema.py`; executar `python -m unittest discover -s tests -v`. Resultado da revisão: 31 testes aprovados. Registros e relógio locais são ignorados pelo Git; os exemplos fictícios são versionados.
