"""FloodGuard: registro comunitário pelo terminal, com persistência CSV."""
import csv
from pathlib import Path

ARQUIVO = Path(__file__).resolve().parents[1] / 'dados' / 'ocorrencias.csv'
CAMPOS = ['id', 'bairro', 'categoria', 'descricao', 'urgencia', 'status']
CATEGORIAS = ['Iluminação', 'Acessibilidade', 'Limpeza', 'Conservação']
URGENCIAS = ['Baixa', 'Média', 'Alta']
STATUS = ['Aberta', 'Em análise', 'Concluída']


def carregar():
    if not ARQUIVO.exists():
        return []
    with ARQUIVO.open(encoding='utf-8', newline='') as arquivo:
        leitor = csv.DictReader(arquivo, strict=True)
        if leitor.fieldnames != CAMPOS:
            raise ValueError('O cabeçalho do CSV não corresponde aos campos esperados.')
        registros = list(leitor)
    ids = set()
    for item in registros:
        codigo = item.get('id', '')
        if (None in item or any(not item.get(campo, '').strip() for campo in CAMPOS)
                or not codigo.startswith('FG-') or not codigo[3:].isdigit()
                or codigo in ids or item['categoria'] not in CATEGORIAS
                or item['urgencia'] not in URGENCIAS or item['status'] not in STATUS):
            raise ValueError('Há um registro inválido ou repetido no CSV.')
        ids.add(codigo)
    return registros


def salvar(registros):
    ARQUIVO.parent.mkdir(parents=True, exist_ok=True)
    temporario = ARQUIVO.with_suffix('.csv.tmp')
    with temporario.open('w', encoding='utf-8', newline='') as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=CAMPOS)
        escritor.writeheader()
        escritor.writerows(registros)
    temporario.replace(ARQUIVO)


def texto(pergunta):
    while True:
        resposta = input(pergunta).strip()
        if resposta:
            return resposta
        print('Pode preencher esse campo antes de continuar?')


def escolher(pergunta, opcoes):
    print('\n' + pergunta)
    for numero, opcao in enumerate(opcoes, 1):
        print(f'{numero}. {opcao}')
    while True:
        resposta = input('Sua escolha: ').strip()
        if resposta.isdigit() and 1 <= int(resposta) <= len(opcoes):
            return opcoes[int(resposta) - 1]
        print('Digite um dos números da lista.')


def confirmar(pergunta):
    while True:
        resposta = input(pergunta + ' (s/n): ').strip().lower()
        if resposta in ('s', 'n'):
            return resposta == 's'
        print('Responda com s para sim ou n para não.')


def mostrar(item):
    print(f"\n{item['id']} · {item['bairro']}")
    print(item['descricao'])
    print(f"{item['categoria']} · Urgência {item['urgencia'].lower()} · {item['status']}")


def cadastrar(registros):
    print('\nVamos registrar o que aconteceu.')
    bairro = texto('Em qual bairro fica o problema? ')
    descricao = texto('Como você descreveria a situação?\n> ')
    categoria = escolher('Qual destas categorias combina melhor?', CATEGORIAS)
    urgencia = escolher('Qual é a urgência?', URGENCIAS)
    print('\nConfira antes de salvar:')
    print(f'{bairro} · {categoria} · Urgência {urgencia.lower()}')
    print(descricao)
    if not confirmar('Podemos guardar esse registro?'):
        print('Tudo bem. Esse registro não foi salvo.')
        return
    numero = max((int(item['id'][3:]) for item in registros), default=0) + 1
    item = dict(zip(CAMPOS, [f'FG-{numero:03}', bairro, categoria, descricao, urgencia, 'Aberta']))
    salvar(registros + [item])
    registros.append(item)
    print(f"\nPronto. O registro {item['id']} foi salvo.")
    print('Ele começa como aberto e você pode atualizar depois.')


def consultar(registros):
    filtro = escolher('Como você quer consultar?', ['Todos', 'Por bairro', 'Por categoria', 'Por status'])
    encontrados = registros
    if filtro == 'Por bairro':
        bairro = texto('Qual bairro você quer consultar? ')
        encontrados = [i for i in registros if i['bairro'].casefold() == bairro.casefold()]
    elif filtro in ('Por categoria', 'Por status'):
        campo = 'categoria' if filtro == 'Por categoria' else 'status'
        valor = escolher('Escolha uma opção:', CATEGORIAS if campo == 'categoria' else STATUS)
        encontrados = [i for i in registros if i[campo] == valor]
    if not encontrados:
        print('\nAinda não há registros para essa consulta.')
    for item in encontrados:
        mostrar(item)


def atualizar(registros):
    codigo = texto('\nQual é o código do registro? (ex.: FG-001) ').upper()
    for indice, item in enumerate(registros):
        if item['id'] == codigo:
            mostrar(item)
            status = escolher('Como está esse atendimento agora?', STATUS)
            if confirmar(f'Podemos mudar o status para {status.lower()}?'):
                novos = [dict(i) for i in registros]
                novos[indice]['status'] = status
                salvar(novos)
                registros[:] = novos
                print('Pronto. O atendimento foi atualizado.')
            return
    print('Não encontrei esse código. Você pode conferir na consulta.')


def resumo(registros):
    print(f'\nHá {len(registros)} ocorrências cadastradas:')
    for status in STATUS:
        print(f"{status}: {sum(i['status'] == status for i in registros)}")


def ranking(registros):
    bairros = {}
    for item in registros:
        if item['status'] != 'Concluída':
            chave = item['bairro'].casefold()
            nome, quantidade = bairros.get(chave, (item['bairro'], 0))
            bairros[chave] = (nome, quantidade + 1)
    print('\nOnde há mais pendências?')
    for nome, quantidade in sorted(bairros.values(), key=lambda b: (-b[1], b[0].casefold())):
        print(f'{nome}: {quantidade} ocorrência(s)')
    if not bairros:
        print('Não há pendências registradas por aqui.')
    print('São apenas os registros desta simulação, não uma medida de risco de alagamento.')


def main():
    try:
        registros = carregar()
    except (OSError, ValueError, csv.Error) as erro:
        print(f'Não foi possível abrir os registros: {erro}')
        print('Confira o arquivo CSV antes de tentar novamente. Ele foi preservado.')
        return
    print('\nOlá! Este é o FloodGuard.')
    print('Um espaço para registrar problemas do bairro e acompanhar o que precisa de atenção.')
    print(f'Você tem {len(registros)} registro(s) por aqui.')
    acoes = {'1': cadastrar, '2': consultar, '3': atualizar, '4': resumo, '5': ranking}
    try:
        while True:
            print('\nO que você gostaria de fazer agora?')
            print('1. Contar sobre um problema\n2. Ver os registros do bairro\n3. Atualizar um atendimento\n4. Ver um resumo\n5. Ver quais bairros têm mais pendências\n0. Encerrar por hoje')
            opcao = input('Digite o número da opção: ').strip()
            if opcao == '0':
                print('Até mais! Seus registros salvos continuam por aqui.')
                break
            if opcao not in acoes:
                print('Escolha um dos números do menu.')
                continue
            try:
                acoes[opcao](registros)
            except OSError as erro:
                print(f'Não foi possível salvar: {erro}. A alteração não foi aplicada.')
            input('\nPressione Enter para continuar...')
    except (EOFError, KeyboardInterrupt):
        print('\nAté mais! As alterações já confirmadas foram salvas.')


if __name__ == '__main__':
    main()
