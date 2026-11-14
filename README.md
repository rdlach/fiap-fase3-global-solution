# FloodGuard

Global Solution 2026.2 da FIAP, entrega na Fase 4. Case Neighborhood Action Dashboard.

O FloodGuard ajuda a registrar e acompanhar problemas de iluminação, acessibilidade, limpeza e conservação na região central de São Paulo. A entrega principal roda no terminal com Python e guarda as ocorrências em CSV.

## Integrantes do Grupo 9

* <a href="https://github.com/rdlach">Ronei Davi Lach</a> (RM575354)
* <a href="https://github.com/Obleynixx">Gabriel Hampel Meireles</a> (RM574600)
* <a href="https://github.com/jrzendron">José Roberto Zendron</a> (RM575414)
* <a href="https://github.com/robertoiuvata">Roberto Kenji Iuvata</a> (RM574361)
* <a href="https://github.com/David-Silva2004">David Silva</a> (RM575885)

## Professores

### Tutor(a)

* <a href="https://br.linkedin.com/in/andretritiack">André Tritiack</a>

### Coordenador(a)

* <a href="https://www.linkedin.com/in/valtersrf/">Valter Santiago Rosa Filho</a>

## Como executar

Use Python 3.10 ou mais recente. Na pasta do projeto, rode:

```sh
python3 src/sistema.py
```

Para começar com 12 ocorrências fictícias e 10 mudanças de status:

```sh
python3 src/sistema.py --demo
```

A demonstração usa uma base temporária. Pode cadastrar, testar uma mudança de status e avançar o dia sem mexer na base do uso normal. No modo normal, as ocorrências e o histórico ficam em `dados/ocorrencias.csv`. O dia simulado fica em `dados/dia_simulado.txt`.

## O que mostrar no terminal

- Em **Comunidade**, cadastre uma ocorrência, consulte pelo bairro e reforce um problema que já existe.
- Em **Explorar por bairro e categoria**, veja os três níveis: bairro, categoria e ocorrência.
- Em **Equipe**, compare a fila por ordem de registro com a fila por pontuação. A primeira mostra apenas as ocorrências abertas e ainda sem análise, em ordem de código. A segunda atende primeiro os casos com mais pontos.
- Atualize o status e confira o histórico. A pilha de últimas atualizações mostra primeiro o evento que acabou de entrar.
- Em **Ver resumo**, confira a matriz com categorias nas linhas e status nas colunas. Veja também o percentual por categoria e por status e a média de solicitações por ocorrência.

Cada percentual divide a quantidade daquele grupo pelo total de ocorrências. A média divide todas as solicitações, incluindo os reforços, pelo número de ocorrências. Na base de exemplo, quatro de 12 ocorrências estão em análise, o que representa 33,3%.

## Como os dados são organizados

| Estrutura | Uso |
| --- | --- |
| Lista | Guarda as ocorrências e permite percorrer a base. |
| Fila FIFO | Retira a ocorrência aberta mais antiga primeiro. Em análise e concluídas ficam fora dessa fila. |
| Pilha | Mostra a última mudança de status antes das anteriores. |
| Dicionário | Usa o código como chave na busca direta. Também agrupa bairro, categoria e ocorrências. |
| Matriz | Cruza as quatro categorias com os três status. |

Aberta significa que a demanda foi registrada e aguarda análise. Em análise significa que a equipe começou a avaliar o caso. Concluída significa que o acompanhamento simulado terminou.

## Regras e exemplo

O CSV exige código, localidade genérica, categoria, tipo, descrição, urgência, status, dia de abertura e total de solicitações. O cadastro gera o código e começa com status Aberta. O histórico pode ficar vazio até a primeira alteração.

A consulta usa `campo is None or item[campo] == valor`. Sem filtro, mostra toda a base. Com filtro, só mostra os registros com o valor escolhido. Se nenhum corresponder, informa que a consulta ficou vazia. A validação usa `not valor.strip()` para recusar campos preenchidos apenas com espaços. Uma mudança de status só acrescenta um evento depois da confirmação e quando o novo status é diferente do atual.

Na demo, cadastre um poste apagado em um bairro do catálogo. O registro recebe o código FG-013 e começa como Aberta. Escolha Por código e informe FG-013 para conferir o cadastro. Em Equipe, mude a situação para Em análise. O histórico passa a mostrar `Dia 1 | FG-013 | De Aberta para Em análise`.

O arquivo `dados/ocorrencia_invalida.csv` tem uma descrição vazia. O teste `test_base_invalida_preservada` verifica que a leitura aponta esse campo e preserva o arquivo. A base válida da demo fica em outro CSV.

## O que a base de exemplo mostra

No início há 5 abertas, 4 em análise e 3 concluídas. Isso dá 9 pendências em 12 registros, ou 75%. As quatro categorias têm três registros cada porque a amostra foi montada para cobrir os quatro casos. A média é de 2,0 solicitações por ocorrência, contando os reforços. O tempo médio em aberto soma, para cada pendência, o dia atual menos o dia de abertura e divide pela quantidade de pendências. Todos começam no dia 1, então a média inicial é zero.

A simulação ajuda a separar demandas novas das que já estão sendo avaliadas. Os números vêm de uma amostra fictícia e servem para explicar os indicadores. Durante o projeto, aprendemos que um mesmo conjunto de registros pode produzir visões diferentes: a fila ajuda a começar a análise, o histórico preserva as decisões e a matriz mostra como os casos se distribuem.

## Cuidados no uso

Use dados fictícios na apresentação. O cadastro precisa do bairro e da descrição do problema, sem nome, telefone ou documento. O menu funciona pelo teclado, informa as opções em texto e permite voltar antes de confirmar. O dia é simulado, e o ranking mostra a quantidade de pendências por bairro.

## Arquivos do projeto

- `src/`: aplicação de terminal e relatórios.
- `dados/`: catálogos, base de exemplo e arquivos da execução.
- `docs/`: regras, escolhas do projeto e registro de uso de IA.
- `tests/`: testes da aplicação de terminal.
- `pyhtml-beta/`: versão web em Python, disponível como demonstração extra.

Para rodar os testes:

```sh
python3 -m unittest discover -s tests -v
```

[Abrir a demonstração web](https://d1o47fa2nugvwl.cloudfront.net/)

## 📋 Licença

<img style="height:22px!important;margin-left:3px;vertical-align:text-bottom;" src="https://mirrors.creativecommons.org/presskit/icons/cc.svg?ref=chooser-v1"><img style="height:22px!important;margin-left:3px;vertical-align:text-bottom;" src="https://mirrors.creativecommons.org/presskit/icons/by.svg?ref=chooser-v1"><p xmlns:cc="http://creativecommons.org/ns#" xmlns:dct="http://purl.org/dc/terms/"><a property="dct:title" rel="cc:attributionURL" href="https://github.com/fiap-tutoria/FIAP-PORTFOLIO-AI">TEMPLATE FIAP PORTFÓLIO AI</a> por <a rel="cc:attributionURL dct:creator" property="cc:attributionName" href="https://fiap.com.br">FIAP</a> está licenciado sobre <a href="http://creativecommons.org/licenses/by/4.0/?ref=chooser-v1" target="\_blank" rel="license noopener noreferrer" style="display:inline-block;">Attribution 4.0 International</a>.</p>

