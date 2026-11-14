# Guia rápido de uso e demonstração

Requer Python 3. O projeto não exige instalar pacotes.

## Iniciar

Na raiz do projeto:

```bash
python src/sistema.py
```

No Windows: `py src/sistema.py`. O caminho dos dados é calculado a partir dos arquivos do programa, por isso também funciona executando o script a partir de outra pasta.

Uma cópia recém-obtida do Git inicia sem ocorrências, com os catálogos centrais disponíveis e dia simulado 1. Os registros são criados em `dados/ocorrencias.csv` ao confirmar o primeiro cadastro. O dia é salvo em `dados/dia_simulado.txt` no primeiro avanço confirmado.

## Base fictícia opcional

O arquivo `dados/ocorrencias_exemplo.csv` contém 12 ocorrências fictícias: três de cada categoria, distribuídas entre os três status. Ele não substitui automaticamente seus registros.

Para demonstrar com essa base, use uma **outra cópia limpa do projeto**, sem seus arquivos locais de ocorrências e dia simulado. Nessa cópia, faça uma cópia de `dados/ocorrencias_exemplo.csv` com o nome `dados/ocorrencias.csv`. Mantenha o dia inicial 1. Não substitua seus registros de uso por exemplos.

## Comunidade

Escolher 1 no menu principal. Para cadastrar, escolher distrito, bairro, categoria, tipo e descrição. Enter aceita a descrição predefinida, com complemento opcional. Em Outro, a descrição é obrigatória. Usar 0 para voltar e a revisão para corrigir ou cancelar.

Na consulta, filtrar por distrito, bairro, categoria ou status. Anotar o código, por exemplo FG-001. Para adicionar uma solicitação ao mesmo problema, escolher Reforçar uma ocorrência existente, informar esse código, conferir a descrição e confirmar com s. Não cadastrar outro problema apenas para aumentar a pontuação de um já existente.

## Equipe

Voltar ao menu principal e escolher 2. A fila mostra a pontuação detalhada e a ordem de atendimento. Atualizar status pelo código e confirmar a alteração. Concluídas saem da fila.

Para demonstrar o efeito do tempo, escolher Avançar dias da simulação, informar a quantidade e confirmar. Ao voltar à comunidade, a prioridade apresentada já considera esse novo dia. O tempo não passa pelo calendário real do computador.

Os dois menus representam perfis de demonstração e não têm login. Usar uma instância do programa por vez.

## Conferir o funcionamento

```bash
python -m unittest discover -s tests -v
```

Os testes usam cópias temporárias. Resultado da revisão: 31 testes aprovados. Para a demonstração manual, seguir `tests/cenarios_pontuacao.md`.

Se o programa informar inconsistência no CSV, preservar o arquivo e conferir o cabeçalho e o campo indicado. As regras e os formatos aceitos estão em [mudancas.md](mudancas.md).
