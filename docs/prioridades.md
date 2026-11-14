# Regras de prioridade na simulação

Essas regras foram definidas como critérios acadêmicos do protótipo em 14/11/2026. São ajustáveis pela equipe e precisam ser compreendidas, testadas e justificadas. O programa organiza relatos fictícios; os níveis não representam avaliação oficial de risco ou promessa de atendimento.

## Nível inicial por tipo

| Categoria | Tipo | Nível inicial |
| --- | --- | --- |
| Iluminação | Poste apagado | Média |
| Iluminação | Luz piscando | Baixa |
| Iluminação | Iluminação danificada | Média |
| Acessibilidade | Rampa obstruída | Alta |
| Acessibilidade | Calçada sem passagem | Alta |
| Acessibilidade | Piso tátil danificado | Média |
| Limpeza | Lixo acumulado | Baixa |
| Limpeza | Descarte de entulho | Média |
| Limpeza | Bueiro com lixo | Média |
| Conservação | Buraco na rua | Média |
| Conservação | Banco danificado | Baixa |
| Conservação | Brinquedo de praça quebrado | Alta |
| Iluminação | Poste danificado | Alta |
| Iluminação | Fiação elétrica exposta | Alta |
| Iluminação | Iluminação bloqueada por vegetação | Média |
| Acessibilidade | Escadaria sem corrimão | Média |
| Acessibilidade | Travessia sem acesso rebaixado | Alta |
| Acessibilidade | Banheiro público sem acessibilidade | Média |
| Limpeza | Esgoto a céu aberto | Alta |
| Limpeza | Animal morto em espaço público | Média |
| Limpeza | Banheiro público sem limpeza | Média |
| Conservação | Vazamento de água | Média |
| Conservação | Árvore caída em espaço público | Alta |
| Conservação | Sinalização de trânsito danificada | Média |
| Todas | Outro problema da categoria | Média |

A tabela fica no dicionário `URGENCIAS_INICIAIS`, em `src/prioridades.py`. O usuário escolhe o tipo; o nível inicial é atribuído pelo programa. Registros anteriores conservam o nível inicial que já estava salvo.

## Pontuação sem teto

A regra atual substitui os aumentos em blocos por uma pontuação contínua:

`pontos = pontos_iniciais + dias + (solicitacoes - 1)`.

- Baixa inicial: 0 pontos.
- Média inicial: 3 pontos.
- Alta inicial: 6 pontos.
- `dias = dia_atual - dia_abertura`: mais um ponto a cada dia simulado.
- A primeira solicitação é o próprio cadastro; cada reforço confirmado acrescenta uma solicitação e mais um ponto.

Crítico continua sendo apenas uma prioridade derivada; nenhum preset inicia nele. O total numérico não tem teto. Duas ocorrências Críticas podem ter 12 e 30 pontos, e a de 30 vem primeiro na fila.

| Pontos | Prioridade apresentada à comunidade |
| --- | --- |
| 0 a 2 | Baixa |
| 3 a 5 | Média |
| 6 a 8 | Alta |
| 9 ou mais | Crítico |

Exemplos: Baixa com três dias e quatro solicitações totais soma `0 + 3 + 3 = 6`, Alta. Baixa com sete dias e uma solicitação soma `0 + 7 + 0 = 7`, Alta. Baixa com nove dias e uma solicitação soma 9, Crítico.

## Vinculação explícita e contagem acumulada

Usar “Reforçar uma ocorrência existente” no menu da comunidade. O usuário informa o código, confere o problema e confirma. O mesmo registro recebe `solicitacoes + 1`, sem outro ID. Cancelar ou falhar a gravação não altera o contador.

O sistema não vincula automaticamente registros por bairro, categoria ou tipo. Dois postes apagados podem representar problemas diferentes. Essa escolha evita que a proximidade ou a classificação sejam usadas como prova de identidade do problema.

A contagem é acumulada por ocorrência e não diminui quando outro problema é concluído. Outro problema também pode receber reforços por código, com confirmação explícita. Não é possível reforçar uma ocorrência concluída.

A base não identifica pessoas: contagem de solicitações não comprova a quantidade de moradores distintos. São registros de demonstração sem mecanismo de votação ou identificação de usuários.

## Comunidade e equipe

A comunidade vê informações do problema, status e prioridade. Pontuação, parcelas de cálculo e ordem interna ficam no painel da equipe. Os perfis são simulados por menus, sem login ou controle real de acesso.

A fila da equipe ordena os pendentes por pontuação decrescente. Empates usam dia de abertura crescente e depois o código numérico crescente. Concluídos não participam da fila. Não há teto na pontuação, embora a prioridade pública tenha quatro nomes.

O tempo usa dias inteiros da simulação. No painel da equipe, “Avançar dias da simulação” permite avançar de 1 a 365 dias, com confirmação e opção de voltar. O calendário real não participa. Reabrir o programa conserva o dia salvo.

## Persistência e dados anteriores

O CSV guarda `urgencia` como nível inicial, `dia_abertura` e `solicitacoes` como total acumulado. A pontuação é derivada; não é regravada a cada consulta, evitando somar duas vezes o mesmo dia ou reforço.

Registros antigos sem contador recebem 1. Sem abertura, recebem dia 1 por convenção. Os IDs, descrições e datas já existentes são preservados. Registros antigos independentes não são fundidos automaticamente. A leitura não modifica o arquivo; a próxima alteração confirmada grava os doze campos do formato atual.

O dia atual fica em `dados/dia_simulado.txt`; sua ausência representa dia 1. Abertura futura ou inválida e contador zero, negativo ou não inteiro são rejeitados, preservando o CSV original.

Ao concluir uma ocorrência, ela sai da fila. Se for reaberta, conserva abertura original e solicitações acumuladas. Não há cálculo de tempo separado por períodos de encerramento, pois o histórico ainda será implementado.

## Distinção dos presets e limites

Os 24 tipos têm descrição inicial e complemento opcional; Outro exige descrição. Iluminação danificada refere-se ao equipamento de luz, enquanto Poste danificado trata da estrutura. Banheiro sem acessibilidade e banheiro sem limpeza são demandas diferentes.

Os pontos são critérios acadêmicos de ordenação de relatos fictícios, não uma classificação oficial de risco. A equipe deve revisar os níveis iniciais e explicar sua escolha.
