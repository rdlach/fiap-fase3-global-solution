# FloodGuard

Global Solution da FIAP, Fase 3. Case Neighborhood Action Dashboard.

O FloodGuard ajuda a registrar e acompanhar problemas de iluminação, acessibilidade, limpeza e conservação na região central de São Paulo. A entrega principal roda no terminal com Python e guarda as ocorrências em CSV.

## 👨‍🎓 Integrantes:

* <a href="https://github.com/rdlach">Ronei Davi Lach</a>
* <a href="https://github.com/Obleynixx">Gabriel Hampel Meireles</a>
* <a href="https://github.com/jrzendron">José Roberto Zendron</a>
* <a href="https://github.com/robertoiuvata">Roberto Kenji Iuvata</a>
* <a href="https://github.com/David-Silva2004">David Silva</a>

## 👩‍🏫 Professores:

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
- Em **Equipe**, compare a fila por ordem de registro com a fila por pontuação. A primeira mostra os pendentes mais antigos pelo código. A segunda atende primeiro os casos com mais pontos.
- Atualize o status e confira o histórico. A pilha de últimas atualizações mostra primeiro o evento que acabou de entrar.
- Em **Ver resumo**, confira a matriz com categorias nas linhas e status nas colunas. Veja também o percentual por categoria e por status e a média de solicitações por ocorrência.

Cada percentual divide a quantidade daquele grupo pelo total de ocorrências. A média divide todas as solicitações, incluindo os reforços, pelo número de ocorrências. Na base de exemplo, quatro de 12 ocorrências estão em análise, o que representa 33,3%.

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

