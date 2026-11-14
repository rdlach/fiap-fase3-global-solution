# Uso de inteligência artificial

## Apoio nesta etapa — 14/11/2026

A IA apoiou a análise da versão inicial do FloodGuard, a pesquisa de fontes dos presets de localidades, a implementação dos menus e validações, a criação dos tipos e descrições de problema, a pontuação aprovada pela equipe e a documentação.

As decisões de escopo foram discutidas com a equipe: região central de São Paulo, quatro categorias, 24 tipos e Outro, retorno entre etapas, Crítico derivado e pontuação sem teto. O modelo final usa base 0/3/6, mais um ponto por dia e por solicitação adicional explicitamente vinculada ao mesmo código. As regras anteriores foram substituídas; a documentação atual reflete o modelo final.

## Origem dos dados

Distritos e zonas vieram da Fundação Seade; bairros de referência vieram de uma base pública identificada e atribuída em `catalogo_sao_paulo.md`. Os códigos originais dos 18 bairros foram preservados. A IA não definiu uma lista oficial de bairros.

A IA gerou 12 ocorrências fictícias para `dados/ocorrencias_exemplo.csv`, usando apenas localidades e tipos válidos, sem dados pessoais. O arquivo de uso e o relógio local da equipe foram preservados e excluídos do versionamento por regras de `.gitignore`.

## Como os resultados foram verificados

A revisão inicial executou 31 testes com `unittest`, biblioteca padrão do Python. O arquivo `tests/test_sistema.py` permite reproduzi-los com `python -m unittest discover -s tests -v`.

Foram verificados catálogos, os 24 cadastros predefinidos, CSV com acentos, aspas e BOM, campos inválidos, formatos anteriores, retorno e cancelamento, falha de gravação, solicitações vinculadas, pontuação, ordem de atendimento, separação de informações entre os menus e fluxo real com gravação e reinício.

Resultado: 31 testes aprovados, sem falhas nem erros. O CSV e o relógio existentes foram conferidos por hash antes e depois da execução e permaneceram inalterados. O resumo está em `tests/resultado_revisao.json`. Os relatórios intermediários foram arquivados na pasta de análise do workspace e não compõem o commit desta etapa.

## Responsabilidade da equipe

Os testes foram conduzidos com apoio de IA e não representam validação já realizada por todos os integrantes. A equipe deve executar o roteiro manual, revisar o código, justificar os presets e a pontuação e registrar os responsáveis pela conferência antes da entrega acadêmica.

O apoio de IA não substitui a compreensão da solução. A IA apoiou a montagem do histórico, da fila FIFO, da pilha e dos indicadores, além da revisão dos fluxos da base de exemplo. O andamento da entrega está em `mudancas.md`.
