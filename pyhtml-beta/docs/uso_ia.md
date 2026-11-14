# Uso de inteligência artificial — pyHTML Versão Beta

## Apoio em 14/11/2026

A IA apoiou a criação da interface com botões solicitada pela equipe, a adaptação das operações de Python para formulários HTML, o CSS simples, a separação da experiência em uma pasta própria, a documentação e os testes. Esta declaração complementa a documentação de IA da versão principal, que não foi modificada.

A primeira proposta de página estática foi substituída por uma aplicação local funcional após a equipe esclarecer que os botões deveriam executar as operações do programa. Não há botões ilustrativos desativados. A implementação usa bibliotecas padrão do Python, HTML e CSS, sem JavaScript ou framework.

## Decisões e origem

Foram preservados os presets, os catálogos, a pontuação e os exemplos fictícios do projeto-base na revisão `488762f`. Os arquivos necessários foram copiados para `pyhtml-beta/` para manter código e dados da experiência independentes do terminal principal. Atribuição dos catálogos: [catalogo_sao_paulo.md](catalogo_sao_paulo.md).

O servidor HTTP é infraestrutura adicional da Beta; a equipe deve estudar essa parte e avaliar sua adequação ao escopo acadêmico. As regras de negócio continuam usando funções, condicionais, laços, listas, dicionários e CSV.

## Como verificar

Execute `py -m unittest discover -s pyhtml-beta/tests -v` na raiz do repositório. Os testes usam arquivos temporários e cobrem o código Python, formulários em etapas, leitura e gravação por HTTP, reforço, status, dias simulados, pontuação, retorno, rejeição de campos inválidos, escape de texto HTML, folha de estilo e encerramento.

Também foi executada a suíte original do terminal para verificar a preservação do projeto-base. Os testes com apoio de IA não substituem a revisão e a execução do roteiro manual por todos os integrantes. Não foram implementados login, integração com órgãos públicos ou infraestrutura para publicar o servidor na internet.
