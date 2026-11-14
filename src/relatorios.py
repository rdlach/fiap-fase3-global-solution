"""Consultas e indicadores do painel de terminal."""
from collections import deque


def fila_fifo(registros, mostrar):
    fila = deque(sorted(
        (item for item in registros if item['status'] != 'Concluída'),
        key=lambda item: int(item['id'][3:]),
    ))
    print('\nFila por ordem de registro')
    if not fila:
        print('Não há ocorrências pendentes.')
    while fila:
        mostrar(fila.popleft())


def eventos(registros):
    return sorted(
        (evento for item in registros for evento in item.get('historico', [])),
        key=lambda evento: evento['ordem'],
    )


def mostrar_historico(registros, recentes=False):
    pilha = eventos(registros)
    print('\nÚltimas atualizações' if recentes else '\nHistórico de status')
    if not pilha:
        print('Ainda não há mudanças de status registradas.')
    if recentes:
        # O último evento adicionado é o primeiro a aparecer.
        while pilha:
            mostrar_evento(pilha.pop())
    else:
        for evento in pilha:
            mostrar_evento(evento)


def mostrar_evento(evento):
    print(f"Dia {evento['dia']} | {evento['id']} | De {evento['antes']} para {evento['depois']}")


def mostrar_por_bairro(registros):
    grupos = {}
    for item in registros:
        categorias = grupos.setdefault(item['bairro'], {})
        categorias.setdefault(item['categoria'], []).append(item)
    print('\nOcorrências por bairro e categoria')
    if not grupos:
        print('Ainda não há ocorrências.')
    for bairro, categorias in sorted(grupos.items()):
        print(bairro)
        for categoria, itens in sorted(categorias.items()):
            print(f'  {categoria}')
            for item in itens:
                print(f"    {item['id']} | {item['status']} | {item['tipo']}")


def indicadores(registros, categorias, status):
    matriz = [[0 for _ in status] for _ in categorias]
    for item in registros:
        matriz[categorias.index(item['categoria'])][status.index(item['status'])] += 1
    total = len(registros)

    def proporcao(quantidade):
        percentual = quantidade / total * 100 if total else 0
        return f'{quantidade} ({percentual:.1f}%)'

    print(f'\nHá {total} ocorrências cadastradas.')
    print(f"{'Categoria':<18}" + ''.join(f'{nome:>12}' for nome in status) + '  Total da categoria')
    for categoria, linha in zip(categorias, matriz):
        print(f'{categoria:<18}' + ''.join(f'{valor:>12}' for valor in linha) + f'  {proporcao(sum(linha))}')
    for coluna, nome in enumerate(status):
        print(f'{nome}: {proporcao(sum(linha[coluna] for linha in matriz))}')
    if total:
        pedidos = sum(int(item['solicitacoes']) for item in registros)
        print(f'Média de solicitações por ocorrência: {pedidos / total:.1f}')
    else:
        print('Média de solicitações por ocorrência: sem dados.')
