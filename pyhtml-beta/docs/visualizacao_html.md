# Interface funcional — pyHTML Versão Beta

A Beta substitui a escolha de números no terminal por botões e formulários no navegador. O terminal mantém o programa Python em execução. As operações realmente leem e gravam CSV; as tabelas refletem o estado salvo.

## Iniciar

Na raiz do repositório, execute `py pyhtml-beta/src/interface_html.py`. O navegador abre em `http://127.0.0.1:8765`. Mantenha o terminal aberto. Não inicie apenas dando dois cliques no HTML.

## Como os botões executam o Python

1. O navegador envia o formulário para o servidor local do Python.
2. O programa valida os campos e chama as funções de cadastro, reforço ou status.
3. Essas funções salvam o CSV da Beta e a página apresenta o resultado.

O arquivo `src/interface_html.py` usa `http.server` e outras bibliotecas padrão. Essa é a parte adicional responsável pela comunicação com o navegador. As operações reutilizadas estão na cópia de `src/main.py`, e as regras de prioridade e localidades ficam nos respectivos módulos. Não há dependências de pacotes, JavaScript ou framework.

`index.html` contém o menu inicial. `style.css` define cores, espaçamento, botões, campos, foco de teclado e adaptação da largura. O mesmo CSS atende todas as telas.

## Roteiro de demonstração

1. Clique em **Acessar comunidade → Registrar um problema**.
2. Escolha **Liberdade**, clique em **Mostrar bairros deste distrito**, escolha o bairro **Liberdade** e clique em **Continuar**.
3. Selecione **Limpeza → Lixo acumulado** nas etapas seguintes.
4. Confira ou complemente a descrição e clique em **Revisar cadastro**.
5. Use os botões **Corrigir** se necessário. Somente **Salvar ocorrência** grava o registro.
6. Na consulta, clique em **Ver detalhes** ou **Reforçar esta ocorrência**. O reforço exige confirmação e soma uma solicitação ao mesmo código.
7. Acesse **Equipe de acompanhamento → Atualizar status**. Selecione a ocorrência e o novo status, revise e confirme.
8. Em **Avançar dias da simulação**, informe a quantidade, revise o dia de destino e confirme. A fila recalcula a pontuação.
9. Use **Menu inicial → Encerrar aplicação → Confirmar encerramento**. Inicie novamente para conferir que os dados persistiram.

O cadastro permite voltar às etapas e corrigir o rascunho sem salvá-lo. Trocar o tipo de problema renova a descrição sugerida. Cancelar descarta o rascunho. Se houver campo inválido, a mensagem permite voltar pelo navegador para corrigir.

## Gravação e isolamento

Somente os dados de `pyhtml-beta/dados/` são utilizados. Os arquivos da aplicação principal não são importados nem alterados. Na Beta, `ocorrencias.csv` guarda os registros e `dia_simulado.txt` guarda o dia. Ambos são ignorados pelo Git. O carregamento dos 12 exemplos só é permitido com a base vazia e requer confirmação.

A gravação usa arquivo temporário seguido de substituição do CSV. Depois de salvar, o navegador recebe um redirecionamento para consulta, evitando repetir o cadastro ao atualizar a página de resultado. Isso não impede o usuário de reenviar intencionalmente um formulário antigo.

## Inclusão, privacidade e limites

Os campos têm rótulos, as tabelas têm legenda e cabeçalhos, e os botões mostram foco de teclado. A consulta ignora maiúsculas e acentos. A tabela pode ser rolada em telas estreitas.

Não são solicitados nomes, telefone ou documento; evite inserir dados pessoais na descrição. Os perfis não têm autenticação: separar menus não restringe acesso. O servidor é local, para demonstração em uma única instância. Esta Beta é uma cópia experimental independente e não acompanha automaticamente futuras mudanças da versão principal.
