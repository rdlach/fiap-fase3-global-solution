# FloodGuard — aplicação em pyHTML · Versão Beta

Versão experimental local do FloodGuard com menus, formulários e botões no navegador. O Python executa as operações e grava os arquivos CSV. HTML estrutura as páginas e um CSS pequeno cuida da aparência. Não usa JavaScript, frameworks, APIs ou serviços externos.

## Separação da versão principal

- Publicada exclusivamente na branch `pyhtml-beta`, sem merge na `main`.
- Todos os arquivos desta experiência ficam em `pyhtml-beta/`.
- O código, os testes e os dados da aplicação de terminal na raiz do repositório permanecem iguais.
- A Beta contém uma cópia independente do código Python e dos catálogos do projeto, baseada na revisão `488762f`. Melhorias futuras do terminal não se propagam automaticamente para essa cópia.
- Ocorrências e dias da Beta são salvos somente em `pyhtml-beta/dados/`. Ela não importa nem altera os dados locais da aplicação principal.

## Como executar

Requer Python 3.10 ou superior. Não é necessário instalar pacotes.

Na raiz do repositório, execute:

```text
py pyhtml-beta/src/interface_html.py
```

Em sistemas que usam o comando `python`:

```text
python pyhtml-beta/src/interface_html.py
```

O navegador abre em **http://127.0.0.1:8765**. Mantenha o terminal aberto enquanto usa a aplicação. Para encerrar, use **Encerrar aplicação → Confirmar encerramento**, ou pressione `Ctrl+C` no terminal. Para iniciar sem abrir o navegador automaticamente, acrescente `--sem-navegador` ao comando.

Inicie pelo Python. Abrir `index.html` diretamente como arquivo não inicia as operações.

## O que funciona

| Menu | Operações |
| --- | --- |
| Comunidade | Cadastrar em etapas, revisar e corrigir antes de salvar; consultar, buscar e filtrar; ver detalhes; reforçar uma ocorrência; consultar resumo e pendências por bairro. |
| Equipe de acompanhamento | Ver fila ordenada por pontuação; revisar e confirmar novo status; revisar e confirmar avanço dos dias simulados; consultar resumo. |
| Menu inicial | Escolher perfil simulado e encerrar a aplicação. |

Na primeira execução, a base começa vazia. O botão **Carregar 12 exemplos fictícios** permite iniciar a demonstração. Essa operação exige confirmação e só funciona se a base estiver vazia.

Os presets mantêm os 8 distritos, os 18 bairros de referência da região central e as 4 categorias do projeto. A pontuação segue a regra existente: base **0/3/6 + dias decorridos + solicitações adicionais**. A partir de 9 pontos, a prioridade é Crítico; os pontos continuam aumentando. Apenas o menu da equipe exibe a pontuação numérica.

## Arquivos

```text
pyhtml-beta/
├── README.md
├── .gitignore
├── index.html                   # Menu inicial
├── style.css                    # Aparência simples das telas
├── src/
│   ├── interface_html.py         # Formulários e servidor local
│   ├── main.py                   # Regras e operações em Python
│   ├── localidades.py            # Validação dos catálogos
│   ├── prioridades.py            # Pontuação e relógio simulado
│   └── sistema.py                # Entrada de terminal da cópia Beta
├── dados/
│   ├── bairros_sp.csv
│   ├── distritos_sp.csv
│   └── ocorrencias_exemplo.csv
├── docs/
│   ├── visualizacao_html.md
│   ├── catalogo_sao_paulo.md
│   └── uso_ia.md
└── tests/
    ├── test_sistema.py
    └── test_interface_html.py
```

Os arquivos `dados/ocorrencias.csv` e `dados/dia_simulado.txt` são gerados dentro desta pasta durante o uso e ignorados pelo Git. Os exemplos e catálogos são versionados.

## Verificação

Na raiz do repositório:

```text
py -m unittest discover -s pyhtml-beta/tests -v
```

Os testes usam CSVs e relógios temporários. Cobrem as regras existentes e os fluxos HTTP: cadastro com retorno entre etapas, persistência, reforço, status, avanço dos dias, pontuação, importação segura dos exemplos, validação e encerramento. A documentação detalhada está em [docs/visualizacao_html.md](docs/visualizacao_html.md).

## Limites da Beta

Os perfis são simulados, sem login; qualquer pessoa usando a aplicação local pode entrar no menu da equipe. O servidor escuta apenas no computador local e deve ser usado em uma única instância. Não foi desenvolvido para publicação na internet nem para acesso simultâneo por vários usuários.

O relógio é simulado, não acompanha automaticamente a data real. Não há envio a órgãos públicos. Use registros fictícios ou consentidos e evite dados pessoais na descrição. A parte HTTP é infraestrutura adicional da experiência; as regras do problema continuam em funções, listas e dicionários. A equipe precisa compreender e justificar essa extensão antes de incluí-la em uma entrega acadêmica.
