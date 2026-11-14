# Catálogo de localidades da região central de São Paulo

Preparado em 14/11/2026 para permitir a seleção de bairros no terminal. O recorte atual é a região Centro da Fundação Seade: oito distritos e 18 nomes de bairros de referência dentro do município de São Paulo.

## Organização dos arquivos

| Arquivo | Registros | Campos |
| --- | --- | --- |
| `dados/distritos_sp.csv` | 8 | `id,zona,distrito,subprefeitura` |
| `dados/bairros_sp.csv` | 18 | `id,zona,distrito,bairro,variacoes` |

| Zona | Distritos | Bairros no catálogo |
| --- | --- | --- |
| Centro | 8 | 18 |
| Total do recorte | 8 | 18 |

O programa lê os presets localmente, sem APIs ou serviços externos durante o uso. Não foram incluídos mapas, coordenadas, endereços individuais ou dados pessoais. As ocorrências permanecem em um arquivo separado, `dados/ocorrencias.csv`.

## Distritos e zonas

Fonte: Fundação Sistema Estadual de Análise de Dados — Seade, conjunto [Distritos do município de SP](https://dadosabertos.homologacao.sp.gov.br/dataset/codigos-nomes-dos-distritos-do-municipio-de-sao-paulo).

Recurso consultado: [CSV de códigos e nomes dos distritos](https://repositorio.seade.gov.br/dataset/23e85e6c-f584-4bb3-a270-811d386f891b/resource/c25069e9-49c4-4b59-844a-3609cb223adf/download/codigos_distritos_msp.csv).

Foram mantidos somente os oito distritos cuja coluna `regioes` tem valor Centro. O cadastro e as consultas iniciam no distrito, sem escolha de zona. A linha “Sem especificação de distrito” foi excluída. O código foi copiado da coluna `cod_ibge`, com dois dígitos; a zona veio de `regioes`. A grafia “Cidade Lider” foi ajustada para “Cidade Líder”.

## Bairros de referência

Fonte: projeto [Bairros de São Paulo, de vmvaz1935](https://github.com/vmvaz1935/bairros-sp), versão fixa `44dba1025c7dafaeaddd3e8e0a3de80b2c4ee936`.

Arquivo de origem: [bairros_sp.geojson nessa versão](https://raw.githubusercontent.com/vmvaz1935/bairros-sp/44dba1025c7dafaeaddd3e8e0a3de80b2c4ee936/dados/bairros_sp.geojson).

Foram extraídos somente os nomes de bairro e distrito. Os nomes dos distritos foram associados aos da Seade, desconsiderando acentos e maiúsculas para a correspondência. A preparação original conferiu a correspondência dos 96 distritos da cidade. O catálogo usado agora pela aplicação mantém somente os oito distritos e os 18 bairros associados à região Centro. As zonas foram obtidas da base da Seade.

Na preparação original da capital, os bairros foram ordenados por nome, desconsiderando acentos, e receberam códigos internos de `B0001` a `B1854`. O recorte central preserva os códigos originais dos seus 18 bairros, sem renumerar. Esses códigos foram atribuídos uma vez: ao acrescentar bairros futuramente, preservar os códigos existentes e usar um código novo. Não renumerar o catálogo, pois as ocorrências salvas usam esses identificadores.

A coluna `variacoes` aceita alternativas separadas por `|`. A preparação original acrescentou variantes Teresinha/Terezinha; esses bairros estão fora do recorte central atual. A coluna permanece disponível para alternativas verificadas dos nomes incluídos. A alternativa participa da busca; o nome e o código salvos são os do preset escolhido. Outros erros de digitação não são corrigidos automaticamente.

## Limites de cobertura

A Prefeitura explica que os bairros populares não têm uma nomenclatura e fronteiras únicas oficiais: [explicação da administração municipal](https://legislacao.prefeitura.sp.gov.br/razoes-do-veto-ao-projeto-de-lei-208-de-19-de-maio-de-2016). Os 18 nomes selecionados são a cobertura deste recorte da base de referência. Não representam uma lista oficial de bairros ou limites e não equivalem ao Centro Expandido.

O projeto de origem associa nomes postais aos endereços do CNEFE 2022 usando uma base de CEPs de 2018. Nomes populares, loteamentos recentes ou variações não presentes na fonte podem estar ausentes. A associação bairro → distrito usa o distrito de maior sobreposição no levantamento de origem; bairros podem atravessar mais de um distrito. Não se trata de validação cadastral ou delimitação oficial dos bairros.

Ao faltar um nome, a equipe deve conferir a fonte, a localização e possíveis duplicidades antes de acrescentar um preset. O usuário do protótipo escolhe dentre as opções disponíveis. O nome digitado na busca não cria um bairro novo.

## Atribuição e licença da base derivada

O catálogo de bairros foi extraído de dados que o projeto de origem distribui sob a [Open Database License — ODbL 1.0](https://opendatacommons.org/licenses/odbl/1-0/). O arquivo derivado `dados/bairros_sp.csv` é disponibilizado sob essa mesma licença, com esta atribuição:

- Projeto Bairros de São Paulo, de vmvaz1935, na versão indicada acima.
- © colaboradores do [OpenStreetMap](https://www.openstreetmap.org/copyright), para os limites usados na base de origem.
- IBGE, [CNEFE — Censo Demográfico 2022](https://www.ibge.gov.br/estatisticas/sociais/populacao/38734-cadastro-nacional-de-enderecos-para-fins-estatisticos.html).
- Zimmermann, I. (2019), [Códigos de CEP do Brasil por UF, cidade, bairro e logradouro](https://doi.org/10.17632/g97jb8fp57.1), Mendeley Data, v1, CC BY 4.0.

A organização dos distritos por zona foi obtida da Fundação Seade, conforme a fonte identificada nesta documentação. A extração dos nomes para CSV não exige executar os algoritmos geográficos do projeto de origem. O protótipo utiliza leitura simples de arquivos, funções, condicionais, laços, listas e dicionários.
