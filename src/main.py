"""FloodGuard: registro comunitário pelo terminal, com persistência CSV."""
import csv
from pathlib import Path
from localidades import buscar_bairros, carregar_bairros, escolher_bairro, escolher_distrito
from prioridades import URGENCIAS_INICIAIS, calcular_prioridade, carregar_dia, salvar_dia

ARQUIVO = Path(__file__).resolve().parents[1] / 'dados' / 'ocorrencias.csv'
CAMPOS_SEM_TIPO = ['id', 'id_bairro', 'bairro', 'zona', 'distrito', 'categoria', 'descricao', 'urgencia', 'status']
CAMPOS_SEM_DIA = ['id', 'id_bairro', 'bairro', 'zona', 'distrito', 'categoria', 'tipo', 'descricao', 'urgencia', 'status']
CAMPOS_SEM_SOLICITACOES = CAMPOS_SEM_DIA + ['dia_abertura']
CAMPOS = CAMPOS_SEM_SOLICITACOES + ['solicitacoes']
CAMPOS_ANTIGOS = ['id', 'bairro', 'categoria', 'descricao', 'urgencia', 'status']
CATEGORIAS = ['Iluminação', 'Acessibilidade', 'Limpeza', 'Conservação']
TIPOS_PROBLEMA = {'Iluminação': ['Poste apagado',
                'Luz piscando',
                'Iluminação danificada',
                'Poste danificado',
                'Fiação elétrica exposta',
                'Iluminação bloqueada por vegetação',
                'Outro problema de iluminação'],
 'Acessibilidade': ['Rampa obstruída',
                    'Calçada sem passagem',
                    'Piso tátil danificado',
                    'Escadaria sem corrimão',
                    'Travessia sem acesso rebaixado',
                    'Banheiro público sem acessibilidade',
                    'Outro problema de acessibilidade'],
 'Limpeza': ['Lixo acumulado',
             'Descarte de entulho',
             'Bueiro com lixo',
             'Esgoto a céu aberto',
             'Animal morto em espaço público',
             'Banheiro público sem limpeza',
             'Outro problema de limpeza'],
 'Conservação': ['Buraco na rua',
                 'Banco danificado',
                 'Brinquedo de praça quebrado',
                 'Vazamento de água',
                 'Árvore caída em espaço público',
                 'Sinalização de trânsito danificada',
                 'Outro problema de conservação']}
DESCRICOES = {
    'Poste apagado': 'Poste de iluminação apagado.',
    'Luz piscando': 'Luz de iluminação pública piscando.',
    'Iluminação danificada': 'Equipamento de iluminação pública danificado.',
    'Rampa obstruída': 'Rampa de acessibilidade obstruída.',
    'Calçada sem passagem': 'Calçada sem passagem acessível.',
    'Piso tátil danificado': 'Piso tátil danificado.',
    'Lixo acumulado': 'Lixo acumulado em espaço coletivo.',
    'Descarte de entulho': 'Entulho descartado em espaço coletivo.',
    'Bueiro com lixo': 'Bueiro obstruído por lixo.',
    'Buraco na rua': 'Buraco na rua.',
    'Banco danificado': 'Banco de espaço coletivo danificado.',
    'Brinquedo de praça quebrado': 'Brinquedo de praça quebrado.',
    'Poste danificado': 'Poste com dano na estrutura, como inclinação, rachadura ou quebra.',
    'Fiação elétrica exposta': 'Fiação elétrica exposta ou solta em espaço público.',
    'Iluminação bloqueada por vegetação': 'Vegetação bloqueando a luz da iluminação pública.',
    'Escadaria sem corrimão': 'Escadaria de uso público sem corrimão adequado.',
    'Travessia sem acesso rebaixado': 'Travessia de pedestres sem acesso rebaixado adequado.',
    'Banheiro público sem acessibilidade': 'Banheiro público sem condições de acesso e uso acessíveis.',
    'Esgoto a céu aberto': 'Esgoto exposto em espaço público.',
    'Animal morto em espaço público': 'Animal morto aguardando remoção em espaço público.',
    'Banheiro público sem limpeza': 'Banheiro público com falta de limpeza.',
    'Vazamento de água': 'Vazamento de água em espaço público.',
    'Árvore caída em espaço público': 'Árvore caída em espaço público.',
    'Sinalização de trânsito danificada': 'Placa ou pintura de sinalização de trânsito danificada ou ilegível.',
}
URGENCIAS = ['Baixa', 'Média', 'Alta']
STATUS = ['Aberta', 'Em análise', 'Concluída']


def carregar(bairros, dia_atual=1):
    if not ARQUIVO.exists():
        return []
    with ARQUIVO.open(encoding='utf-8-sig', newline='') as arquivo:
        leitor = csv.DictReader(arquivo, strict=True)
        campos_lidos = leitor.fieldnames
        if campos_lidos not in [CAMPOS, CAMPOS_SEM_SOLICITACOES, CAMPOS_SEM_DIA, CAMPOS_SEM_TIPO, CAMPOS_ANTIGOS]:
            raise ValueError('O cabeçalho do CSV não corresponde aos campos esperados.')
        registros = list(leitor)
    ids = []
    bairros_por_id = {}
    for bairro in bairros:
        bairros_por_id[bairro['id']] = bairro
    for item in registros:
        if None in item:
            raise ValueError('Há uma coluna excedente no CSV de ocorrências.')
        for campo in campos_lidos:
            valor = item.get(campo)
            if valor is None or not valor.strip():
                raise ValueError(f'O campo {campo} está ausente ou vazio em uma ocorrência.')
        codigo = item.get('id', '')
        if (not codigo.startswith('FG-') or not codigo[3:]
                or codigo in ids or item['categoria'] not in CATEGORIAS
                or item['urgencia'] not in URGENCIAS or item['status'] not in STATUS):
            raise ValueError('Há um registro inválido ou repetido no CSV.')
        for caractere in codigo[3:]:
            if caractere not in '0123456789':
                raise ValueError('O identificador da ocorrência deve usar números após FG-.')
        numero = int(codigo[3:])
        if numero < 1 or codigo != f'FG-{numero:03}':
            raise ValueError('O identificador deve seguir o padrão FG-001, com numeração positiva.')
        ids.append(codigo)
        if campos_lidos in [CAMPOS_SEM_TIPO, CAMPOS_ANTIGOS]:
            item['tipo'] = TIPOS_PROBLEMA[item['categoria']][-1]
        if item['tipo'] not in TIPOS_PROBLEMA[item['categoria']]:
            raise ValueError(f'O tipo de problema de {codigo} não pertence à categoria informada.')
        if campos_lidos not in [CAMPOS, CAMPOS_SEM_SOLICITACOES]:
            item['dia_abertura'] = '1'
        if campos_lidos != CAMPOS:
            item['solicitacoes'] = '1'
        quantidade = item['solicitacoes']
        if not quantidade.isdecimal() or int(quantidade) < 1:
            raise ValueError(f'A quantidade de solicitações de {codigo} deve ser um inteiro positivo.')
        dia = item['dia_abertura']
        if not dia.isdecimal() or len(dia) > 10 or not 1 <= int(dia) <= dia_atual:
            raise ValueError(f'O dia de abertura de {codigo} é inválido ou posterior ao dia atual.')
        if campos_lidos == CAMPOS_ANTIGOS:
            encontrados = buscar_bairros(bairros, item['bairro'], exato=True)
            if len(encontrados) != 1:
                raise ValueError(f"O bairro antigo de {codigo} precisa ser conferido no catálogo. O arquivo foi preservado.")
            bairro = encontrados[0]
            item['id_bairro'] = bairro['id']
            item['bairro'] = bairro['bairro']
            item['zona'] = bairro['zona']
            item['distrito'] = bairro['distrito']
        else:
            bairro = bairros_por_id.get(item['id_bairro'])
            if bairro is None:
                raise ValueError(f'O bairro de {codigo} não está no catálogo da região central de São Paulo.')
            for campo in ['bairro', 'zona', 'distrito']:
                if item[campo] != bairro[campo]:
                    raise ValueError(f'O campo {campo} de {codigo} não corresponde ao bairro selecionado.')
    return registros


def salvar(registros):
    ARQUIVO.parent.mkdir(parents=True, exist_ok=True)
    temporario = ARQUIVO.with_suffix('.csv.tmp')
    with temporario.open('w', encoding='utf-8', newline='') as arquivo:
        escritor = csv.DictWriter(arquivo, fieldnames=CAMPOS)
        escritor.writeheader()
        escritor.writerows(registros)
    temporario.replace(ARQUIVO)


def copiar_registros(registros):
    """Cria cópias para só alterar a memória depois de salvar com sucesso."""
    novos = []
    for item in registros:
        novos.append(dict(item))
    return novos


def texto(pergunta, atual=None):
    if atual is not None:
        print(f'Valor atual: {atual} (Enter para manter)')
    print('0. Voltar')
    while True:
        resposta = input(pergunta).strip()
        if resposta == '0':
            return None
        if not resposta and atual is not None:
            return atual
        if resposta:
            return resposta
        print('Pode preencher esse campo antes de continuar?')


def escolher(pergunta, opcoes, atual=None):
    print('\n' + pergunta)
    for numero, opcao in enumerate(opcoes, 1):
        print(f'{numero}. {opcao}')
    if atual is not None:
        print(f'Valor atual: {atual} (Enter para manter)')
    print('0. Voltar')
    while True:
        resposta = input('Sua escolha: ').strip()
        if resposta == '0':
            return None
        if not resposta and atual is not None:
            return atual
        for numero in range(1, len(opcoes) + 1):
            if resposta == str(numero):
                return opcoes[numero - 1]
        print('Digite um dos números da lista.')


def confirmar(pergunta):
    print('0. Voltar')
    while True:
        resposta = input(pergunta + ' (s/n): ').strip().lower()
        if resposta == '0':
            return None
        if resposta in ('s', 'n'):
            return resposta == 's'
        print('Responda com s para sim, n para não ou 0 para voltar.')


def mostrar(item, dia_atual=1, equipe=False):
    print(f"\n{item['id']} · {item['bairro']}")
    print(f"Distrito: {item['distrito']} · Região: {item['zona']} · São Paulo/SP")
    print(f"Tipo de problema: {item['tipo']}")
    print(item['descricao'])
    print(f"{item['categoria']} · {item['status']} · Abertura: dia {item['dia_abertura']}")
    prioridade = calcular_prioridade(item, dia_atual)
    if prioridade is None:
        print('Ocorrência concluída: fora da fila de atendimento.')
    else:
        print(f"Prioridade atual: {prioridade['nivel']}")
        if equipe:
            print(f"Pontuação: {prioridade['pontos']} · Base: {prioridade['pontos_iniciais']} · Dias: {prioridade['dias']} · Solicitações adicionais: {prioridade['adicionais']}")
            print(f"Total de solicitações vinculadas: {prioridade['solicitacoes']}")


def descrever_problema(tipo, atual=None):
    if tipo not in DESCRICOES:
        return texto('Descreva o problema (obrigatório):\n> ', atual=atual)
    inicial = DESCRICOES[tipo]
    print(f'\nDescrição inicial: {inicial}')
    if atual is not None and atual != inicial:
        print(f'Descrição atual: {atual}')
    print('Enter mantém a descrição. Digite um complemento para acrescentar detalhes.')
    print('Um novo complemento substitui o anterior. Use - para remover o complemento.')
    print('0. Voltar')
    resposta = input('Complemento opcional: ').strip()
    if resposta == '0':
        return None
    elif resposta == '-':
        return inicial
    elif not resposta:
        if atual is not None:
            return atual
        return inicial
    return inicial + ' Complemento: ' + resposta


def preencher_problema(categoria=None, tipo=None, descricao=None, etapa=0):
    """Só devolve os novos valores após concluir categoria, tipo e descrição."""
    while True:
        if etapa == 0:
            nova_categoria = escolher('Qual é a categoria?', CATEGORIAS, atual=categoria)
            if nova_categoria is None:
                return None
            if nova_categoria != categoria:
                tipo = None
                descricao = None
            categoria = nova_categoria
            etapa = 1
        elif etapa == 1:
            novo_tipo = escolher('Qual é o problema?', TIPOS_PROBLEMA[categoria], atual=tipo)
            if novo_tipo is None:
                etapa = 0
                continue
            if novo_tipo != tipo:
                descricao = None
            tipo = novo_tipo
            etapa = 2
        else:
            nova_descricao = descrever_problema(tipo, atual=descricao)
            if nova_descricao is None:
                etapa = 1
            else:
                return categoria, tipo, nova_descricao


def cadastrar(registros, bairros, dia_atual=1):
    """Cadastro com localização, problema e revisão da prioridade calculada."""
    print('\nVamos registrar o que aconteceu.')
    print('Use 0 para voltar uma etapa. Na primeira etapa, 0 cancela o cadastro.')
    bairro = None
    categoria = None
    tipo = None
    descricao = None
    urgencia = None
    etapa = 0
    etapa_problema = 0
    revisando = False
    while True:
        if etapa == 0:
            if bairro is not None:
                print(f"\nBairro atual: {bairro['bairro']} — {bairro['distrito']} ({bairro['zona']})")
            novo_bairro = escolher_bairro(bairros)
            if novo_bairro is None:
                if revisando:
                    etapa = 2
                else:
                    print('Cadastro cancelado. Nenhum registro foi salvo.')
                    return
            else:
                bairro = novo_bairro
                print(f"\nBairro selecionado: {bairro['bairro']} — {bairro['distrito']} ({bairro['zona']})")
                etapa_problema = 0
                if revisando:
                    etapa = 2
                else:
                    etapa = 1
        elif etapa == 1:
            problema = preencher_problema(categoria, tipo, descricao, etapa_problema)
            if problema is None:
                if revisando:
                    etapa = 2
                else:
                    etapa = 0
            else:
                categoria, tipo, descricao = problema
                urgencia = URGENCIAS_INICIAIS.get(tipo, 'Média')
                etapa = 2
        else:
            print('\nConfira antes de salvar:')
            print(f"Bairro: {bairro['bairro']} · Distrito: {bairro['distrito']} · Região: {bairro['zona']}")
            print(f'Categoria: {categoria} · Tipo: {tipo}')
            print(f'Descrição: {descricao}')
            previa = {
                'id_bairro': bairro['id'], 'categoria': categoria, 'tipo': tipo,
                'urgencia': urgencia, 'dia_abertura': str(dia_atual), 'status': 'Aberta', 'solicitacoes': '1',
            }
            prioridade = calcular_prioridade(previa, dia_atual)
            print(f"Prioridade prevista: {prioridade['nivel']}")
            acao = escolher('O que deseja fazer?', [
                'Salvar ocorrência', 'Alterar bairro', 'Alterar descrição',
                'Alterar categoria', 'Sobre a prioridade', 'Cancelar cadastro',
                'Alterar tipo de problema',
            ])
            if acao == 'Salvar ocorrência':
                break
            elif acao == 'Cancelar cadastro':
                print('Cadastro cancelado. Nenhum registro foi salvo.')
                return
            elif acao == 'Sobre a prioridade':
                print('A prioridade considera o tipo do problema, o tempo pendente e as solicitações vinculadas.')
            elif acao is None:
                revisando = False
                etapa_problema = 2
                etapa = 1
            else:
                revisando = True
                if acao == 'Alterar bairro':
                    etapa = 0
                else:
                    etapa = 1
                    if acao == 'Alterar categoria':
                        etapa_problema = 0
                    elif acao == 'Alterar tipo de problema':
                        etapa_problema = 1
                    else:
                        etapa_problema = 2
    maior_numero = 0
    for registro in registros:
        numero_existente = int(registro['id'][3:])
        if numero_existente > maior_numero:
            maior_numero = numero_existente
    numero = maior_numero + 1
    item = {
        'id': f'FG-{numero:03}',
        'id_bairro': bairro['id'],
        'bairro': bairro['bairro'],
        'zona': bairro['zona'],
        'distrito': bairro['distrito'],
        'categoria': categoria,
        'tipo': tipo,
        'descricao': descricao,
        'urgencia': urgencia,
        'status': 'Aberta',
        'dia_abertura': str(dia_atual),
        'solicitacoes': '1',
    }
    salvar(registros + [item])
    registros.append(item)
    print(f"\nPronto. O registro {item['id']} foi salvo.")
    print('Ele começa como aberto e você pode atualizar depois.')


def consultar(registros, bairros, dia_atual=1):
    while True:
        filtro = escolher('Como você quer consultar?', ['Todos', 'Por distrito', 'Por bairro', 'Por categoria', 'Por status'])
        if filtro is None:
            return
        campo = None
        valor = None
        if filtro == 'Por distrito':
            campo = 'distrito'
            valor = escolher_distrito(bairros)
        elif filtro == 'Por bairro':
            bairro = escolher_bairro(bairros)
            if bairro is not None:
                campo = 'id_bairro'
                valor = bairro['id']
            else:
                continue
        elif filtro == 'Por categoria':
            campo = 'categoria'
            valor = escolher('Escolha a categoria:', CATEGORIAS)
        elif filtro == 'Por status':
            campo = 'status'
            valor = escolher('Escolha o status:', STATUS)
        if campo is not None and valor is None:
            continue
        encontrados = []
        for item in registros:
            if campo is None or item[campo] == valor:
                encontrados.append(item)
        if not encontrados:
            print('Ainda não há registros para essa consulta.')
        for item in encontrados:
            mostrar(item, dia_atual)
        return


def atualizar(registros, dia_atual=1):
    while True:
        codigo = texto('Qual é o código do registro? (ex.: FG-001) ')
        if codigo is None:
            return
        codigo = codigo.upper()
        indice_encontrado = None
        for indice, item in enumerate(registros):
            if item['id'] == codigo:
                indice_encontrado = indice
                break
        if indice_encontrado is None:
            print('Não encontrei esse código. Confira na consulta ou use 0 para voltar.')
            continue
        item = registros[indice_encontrado]
        while True:
            mostrar(item, dia_atual, equipe=True)
            status = escolher('Como está esse atendimento agora?', STATUS)
            if status is None:
                break
            resposta = confirmar(f'Podemos mudar o status para {status.lower()}?')
            if resposta is None:
                continue
            if resposta:
                novos = copiar_registros(registros)
                novos[indice_encontrado]['status'] = status
                salvar(novos)
                registros[:] = novos
                print('Pronto. O atendimento foi atualizado.')
            else:
                print('Atualização cancelada. O status foi mantido.')
            return


def resumo(registros):
    print(f'\nHá {len(registros)} ocorrências cadastradas:')
    for status in STATUS:
        quantidade = 0
        for item in registros:
            if item['status'] == status:
                quantidade += 1
        print(f'{status}: {quantidade}')


def chave_do_ranking(bairro):
    return (-bairro['quantidade'], bairro['nome'].casefold())


def ranking(registros):
    bairros = {}
    for item in registros:
        if item['status'] != 'Concluída':
            chave = item['bairro'].casefold()
            if chave not in bairros:
                bairros[chave] = {'nome': item['bairro'], 'quantidade': 0}
            bairros[chave]['quantidade'] += 1
    print('\nOnde há mais pendências?')
    for bairro in sorted(bairros.values(), key=chave_do_ranking):
        print(f"{bairro['nome']}: {bairro['quantidade']} ocorrência(s)")
    if not bairros:
        print('Não há pendências registradas por aqui.')
    print('São apenas os registros desta simulação, não uma medida de risco de alagamento.')


def explicar_prioridade():
    print('\nRegra de pontuação da equipe:')
    print('Base: Baixa = 0; Média = 3; Alta = 6.')
    print('Somar 1 por dia desde a abertura e 1 por solicitação adicional vinculada.')
    print('Baixa: 0–2; Média: 3–5; Alta: 6–8; Crítico: 9 ou mais.')
    print('A pontuação não tem teto. As solicitações vinculadas são acumuladas.')
    print('Ocorrências concluídas ficam fora da fila. Critérios da simulação acadêmica.')


def avancar_dia(dia_atual):
    while True:
        resposta = texto('Quantos dias deseja avançar? (1 a 365) ')
        if resposta is None:
            return dia_atual
        if not resposta.isdecimal() or len(resposta) > 3 or not 1 <= int(resposta) <= 365:
            print('Informe um número de 1 a 365 ou 0 para voltar.')
            continue
        novo_dia = dia_atual + int(resposta)
        confirmado = confirmar(f'Avançar do dia {dia_atual} para o dia {novo_dia}?')
        if confirmado is None:
            continue
        if not confirmado:
            print('Avanço cancelado.')
            return dia_atual
        salvar_dia(novo_dia)
        print(f'Dia simulado atualizado para {novo_dia}. As prioridades foram recalculadas.')
        return novo_dia


def chave_da_fila(elemento):
    return (-elemento['prioridade']['pontos'], int(elemento['item']['dia_abertura']), int(elemento['item']['id'][3:]))


def listar_prioridades(registros, dia_atual):
    explicar_prioridade()
    fila = []
    for item in registros:
        prioridade = calcular_prioridade(item, dia_atual)
        if prioridade is not None:
            fila.append({'item': item, 'prioridade': prioridade})
    if not fila:
        print('Não há ocorrências pendentes para atender.')
    for posicao, elemento in enumerate(sorted(fila, key=chave_da_fila), 1):
        print(f'\nPosição na fila: {posicao}')
        mostrar(elemento['item'], dia_atual, equipe=True)


def reforcar(registros, dia_atual):
    while True:
        codigo = texto('Informe o código da ocorrência que deseja reforçar: ')
        if codigo is None:
            return
        indice_encontrado = None
        for indice, item in enumerate(registros):
            if item['id'] == codigo.upper():
                indice_encontrado = indice
                break
        if indice_encontrado is None:
            print('Ocorrência não encontrada. Confira o código na consulta ou use 0 para voltar.')
            continue
        item = registros[indice_encontrado]
        if item['status'] == 'Concluída':
            print('Essa ocorrência já foi concluída. Escolha uma pendente ou cadastre um novo problema.')
            continue
        mostrar(item, dia_atual)
        confirmado = confirmar('É este o mesmo problema para o qual deseja registrar outra solicitação?')
        if confirmado is None:
            continue
        if not confirmado:
            print('Solicitação cancelada.')
            return
        novos = copiar_registros(registros)
        novos[indice_encontrado]['solicitacoes'] = str(int(item['solicitacoes']) + 1)
        salvar(novos)
        registros[:] = novos
        print('Sua solicitação foi vinculada à ocorrência.')
        mostrar(registros[indice_encontrado], dia_atual)
        return


def menu_comunidade(registros, bairros, dia_atual):
    while True:
        opcao = escolher('Comunidade — o que deseja fazer?', [
            'Registrar um novo problema', 'Consultar ocorrências',
            'Reforçar uma ocorrência existente', 'Ver resumo', 'Ver pendências por bairro',
        ])
        if opcao is None:
            return
        try:
            if opcao == 'Registrar um novo problema':
                cadastrar(registros, bairros, dia_atual)
            elif opcao == 'Consultar ocorrências':
                consultar(registros, bairros, dia_atual)
            elif opcao == 'Reforçar uma ocorrência existente':
                reforcar(registros, dia_atual)
            elif opcao == 'Ver resumo':
                resumo(registros)
            else:
                ranking(registros)
        except OSError as erro:
            print(f'Não foi possível salvar: {erro}. A alteração não foi aplicada.')
        input('\nPressione Enter para continuar...')


def menu_equipe(registros, dia_atual):
    while True:
        print(f'\nDia simulado atual: {dia_atual}')
        opcao = escolher('Equipe — painel de acompanhamento', [
            'Ver fila por pontuação', 'Atualizar status', 'Avançar dias da simulação', 'Ver resumo',
        ])
        if opcao is None:
            return dia_atual
        try:
            if opcao == 'Ver fila por pontuação':
                listar_prioridades(registros, dia_atual)
            elif opcao == 'Atualizar status':
                atualizar(registros, dia_atual)
            elif opcao == 'Avançar dias da simulação':
                dia_atual = avancar_dia(dia_atual)
            else:
                resumo(registros)
        except OSError as erro:
            print(f'Não foi possível salvar: {erro}. A alteração não foi aplicada.')
        input('\nPressione Enter para continuar...')


def main():
    try:
        bairros = carregar_bairros()
        dia_atual = carregar_dia()
        registros = carregar(bairros, dia_atual)
    except (OSError, ValueError, csv.Error) as erro:
        print(f'Não foi possível abrir os dados: {erro}')
        print('Confira os arquivos da pasta dados antes de tentar novamente. Eles foram preservados.')
        return
    print('\nOlá! Este é o FloodGuard.')
    print('Painel de demandas comunitárias da região central de São Paulo.')
    print('Escolha um dos oito distritos e um bairro, ou busque o bairro pelo nome.')
    print(f'Você tem {len(registros)} registro(s) por aqui.')
    try:
        while True:
            print('\n1. Comunidade\n2. Equipe de acompanhamento\n0. Encerrar')
            opcao = input('Escolha a visão: ').strip()
            if opcao == '0':
                print('Até mais! Seus registros salvos continuam por aqui.')
                break
            elif opcao == '1':
                menu_comunidade(registros, bairros, dia_atual)
            elif opcao == '2':
                dia_atual = menu_equipe(registros, dia_atual)
            else:
                print('Escolha uma das opções exibidas.')
    except (EOFError, KeyboardInterrupt):
        print('\nAté mais! As alterações já confirmadas foram salvas.')


if __name__ == '__main__':
    main()
