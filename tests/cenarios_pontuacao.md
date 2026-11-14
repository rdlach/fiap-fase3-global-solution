# Roteiro atual — pontuação e visões de uso

Executar em uma cópia de teste. Resultados automatizados: `resultado_revisao.json`. Código reproduzível: `test_sistema.py`. Para executar, usar `python -m unittest discover -s tests -v`.

1. Abrir a aplicação e entrar na Comunidade. Cadastrar lixo acumulado na Liberdade e salvar. Deve começar em Baixa, sem mostrar pontos.
2. Consultar a ocorrência. Deve exibir código, localização, problema, status e prioridade, sem fórmula nem pontuação.
3. Reforçar a ocorrência pelo código três vezes. Cada confirmação deve conservar o mesmo ID; cancelar não altera nada. Ao fim, há quatro solicitações e uma ocorrência.
4. Tentar reforçar um código inexistente e voltar. Tentar uma ocorrência concluída. Não deve gravar alterações.
5. Voltar ao menu principal e entrar na Equipe. A fila deve exibir três pontos de reforços na ocorrência inicialmente Baixa.
6. Avançar três dias na Equipe. A fila deve mostrar seis pontos: base 0 + três dias + três adicionais, prioridade Alta.
7. Voltar à Comunidade e consultar. Deve mostrar Alta, sem os seis pontos nem suas parcelas.
8. Reabrir o programa. O dia atual e os quatro pedidos vinculados devem permanecer.
9. Acrescentar outros dias ou reforços em cópia de teste. A pontuação deve continuar aumentando depois de Crítico. Conferir faixas: 0–2, 3–5, 6–8 e 9+.
10. Criar dois problemas independentes no mesmo bairro e tipo. Eles não devem somar solicitações automaticamente.
11. Na fila da equipe, comparar críticos com pontuações diferentes. O maior vem primeiro. Empates usam abertura e código mais antigos.
12. Concluir uma ocorrência. Ela deve sair da fila; o contador das demais deve permanecer igual.
13. Testar retorno e cancelamento nos dois menus e na revisão do cadastro.
14. Em cópia de teste, usar contador inválido ou abertura futura. O arquivo deve ser rejeitado com mensagem e preservado.
15. Em cópia de teste, carregar os formatos anteriores. Deve acrescentar contador inicial 1 e conservar IDs, descrição e abertura já existentes.

A separação de menus é uma simulação de perfis e não representa controle de acesso real.
