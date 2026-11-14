# Guia rápido de uso e demonstração

Requer Python 3.10 ou mais recente. O projeto não exige instalar pacotes.

## Iniciar

Na raiz do projeto:

```bash
python src/sistema.py
```

No Windows: `py src/sistema.py`. O caminho dos dados é calculado a partir dos arquivos do programa, por isso também funciona executando o script a partir de outra pasta.

Uma cópia recém-obtida do Git inicia sem ocorrências, com os catálogos centrais disponíveis e dia simulado 1. Os registros são criados em `dados/ocorrencias.csv` ao confirmar o primeiro cadastro. O dia é salvo em `dados/dia_simulado.txt` no primeiro avanço confirmado.

## Base fictícia opcional

Rode `python3 src/sistema.py --demo` para abrir uma sessão com 12 ocorrências fictícias e 10 mudanças de status. A sessão começa no dia 1 e usa arquivos temporários. Ao sair, as mudanças dessa sessão são descartadas.

## Comunidade

Escolher 1 no menu principal. Para cadastrar, escolher distrito, bairro, categoria, tipo e descrição. Enter aceita a descrição predefinida, com complemento opcional. Em Outro, a descrição é obrigatória. Usar 0 para voltar e a revisão para corrigir ou cancelar.

Na consulta, filtrar por distrito, bairro, categoria, status ou código. Anotar o código, por exemplo FG-001. Para adicionar uma solicitação ao mesmo problema, escolher Reforçar uma ocorrência existente, informar esse código, conferir a descrição e confirmar com s. Para ver o agrupamento completo, escolha Explorar por bairro e categoria.

## Equipe

Voltar ao menu principal e escolher 2. Compare a fila por pontuação com a fila por ordem de registro, que mostra apenas as abertas. Atualize um status pelo código e confira o novo evento em Ver histórico de status e em Ver últimas atualizações. As ocorrências concluídas saem das filas. Em Ver resumo, confira a matriz, os percentuais, as pendências e as médias de solicitações e de tempo em aberto.

Para demonstrar o efeito do tempo, escolher Avançar dias da simulação, informar a quantidade e confirmar. Ao voltar à comunidade, a prioridade apresentada já considera esse novo dia. O tempo não passa pelo calendário real do computador.

Os dois menus representam perfis de demonstração e não têm login. Usar uma instância do programa por vez.

## Conferir o funcionamento

```bash
python -m unittest discover -s tests -v
```

Os testes usam cópias temporárias. O roteiro de pontuação está em `tests/cenarios_pontuacao.md`. Para demonstrar as demais funções, use a sequência do README.

Se o programa informar inconsistência no CSV, preservar o arquivo e conferir o cabeçalho e o campo indicado. As regras e os formatos aceitos estão em [mudancas.md](mudancas.md).
