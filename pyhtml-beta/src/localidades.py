"""Catálogo de referência dos oito distritos da região central de São Paulo."""
import csv
from pathlib import Path

ARQUIVO_BAIRROS = Path(__file__).resolve().parents[1] / 'dados' / 'bairros_sp.csv'
ARQUIVO_DISTRITOS = Path(__file__).resolve().parents[1] / 'dados' / 'distritos_sp.csv'
CAMPOS_BAIRROS = ['id', 'zona', 'distrito', 'bairro', 'variacoes']
CAMPOS_DISTRITOS = ['id', 'zona', 'distrito', 'subprefeitura']
DISTRITOS_CENTRO = ['Bela Vista', 'Bom Retiro', 'Cambuci', 'Consolação', 'Liberdade', 'República', 'Santa Cecília', 'Sé']


def normalizar(texto):
    """Ignora maiúsculas, acentos e espaços excedentes durante a busca."""
    texto = texto.strip().lower()
    letras = [
        ['á', 'a'], ['à', 'a'], ['â', 'a'], ['ã', 'a'], ['ä', 'a'],
        ['é', 'e'], ['è', 'e'], ['ê', 'e'], ['ë', 'e'],
        ['í', 'i'], ['ì', 'i'], ['î', 'i'], ['ï', 'i'],
        ['ó', 'o'], ['ò', 'o'], ['ô', 'o'], ['õ', 'o'], ['ö', 'o'],
        ['ú', 'u'], ['ù', 'u'], ['û', 'u'], ['ü', 'u'], ['ç', 'c'],
    ]
    for letra, substituta in letras:
        texto = texto.replace(letra, substituta)
    return ' '.join(texto.split())


def carregar_distritos():
    with ARQUIVO_DISTRITOS.open(encoding='utf-8-sig', newline='') as arquivo:
        leitor = csv.DictReader(arquivo, strict=True)
        if leitor.fieldnames != CAMPOS_DISTRITOS:
            raise ValueError('O cabeçalho do catálogo de distritos está incorreto.')
        distritos = list(leitor)
    ids = []
    nomes = []
    for distrito in distritos:
        if None in distrito:
            raise ValueError('Há uma coluna excedente no catálogo de distritos.')
        for campo in CAMPOS_DISTRITOS:
            valor = distrito.get(campo)
            if valor is None or not valor.strip():
                raise ValueError('Há um campo obrigatório ausente no catálogo de distritos.')
        if distrito['zona'] != 'Centro' or distrito['distrito'] not in DISTRITOS_CENTRO:
            raise ValueError('Há um distrito fora do recorte central.')
        if distrito['id'] in ids or distrito['distrito'] in nomes:
            raise ValueError('Há código ou nome de distrito repetido.')
        ids.append(distrito['id'])
        nomes.append(distrito['distrito'])
    if len(nomes) != len(DISTRITOS_CENTRO):
        raise ValueError('O catálogo deve conter os oito distritos do recorte central.')
    return distritos


def carregar_bairros():
    distritos = carregar_distritos()
    nomes_distritos = []
    for distrito in distritos:
        nomes_distritos.append(distrito['distrito'])
    with ARQUIVO_BAIRROS.open(encoding='utf-8-sig', newline='') as arquivo:
        leitor = csv.DictReader(arquivo, strict=True)
        if leitor.fieldnames != CAMPOS_BAIRROS:
            raise ValueError('O cabeçalho do catálogo de bairros está incorreto.')
        bairros = list(leitor)
    ids = []
    nomes = []
    distritos_representados = []
    for bairro in bairros:
        if None in bairro:
            raise ValueError('Há uma coluna excedente no catálogo de bairros.')
        for campo in CAMPOS_BAIRROS:
            valor = bairro.get(campo)
            if valor is None or (campo != 'variacoes' and not valor.strip()):
                raise ValueError('Há um campo obrigatório ausente no catálogo de bairros.')
        if bairro['id'] in ids:
            raise ValueError('Há um código repetido no catálogo.')
        if bairro['zona'] != 'Centro' or bairro['distrito'] not in nomes_distritos:
            raise ValueError('O catálogo deve conter somente localidades do recorte central de São Paulo.')
        chave = (bairro['distrito'], normalizar(bairro['bairro']))
        if chave in nomes:
            raise ValueError('Há um bairro repetido no mesmo distrito.')
        nomes.append(chave)
        if bairro['distrito'] not in distritos_representados:
            distritos_representados.append(bairro['distrito'])
        ids.append(bairro['id'])
    if not bairros:
        raise ValueError('O catálogo de bairros está vazio.')
    if len(distritos_representados) != len(nomes_distritos):
        raise ValueError('O catálogo de bairros deve representar os oito distritos.')
    return bairros


def buscar_bairros(bairros, termo, exato=False):
    termo = normalizar(termo)
    encontrados = []
    if not termo:
        return encontrados
    for bairro in bairros:
        nomes = [bairro['bairro']]
        for variacao in bairro['variacoes'].split('|'):
            if variacao.strip():
                nomes.append(variacao)
        for nome in nomes:
            nome = normalizar(nome)
            if (exato and termo == nome) or (not exato and termo in nome):
                encontrados.append(bairro)
                break
    return encontrados


def listar_distritos(bairros):
    distritos = []
    for bairro in bairros:
        if bairro['distrito'] not in distritos:
            distritos.append(bairro['distrito'])
    return sorted(distritos, key=normalizar)


def escolher_paginado(pergunta, opcoes):
    """Exibe até 15 opções por página e retorna a opção escolhida ou None."""
    pagina = 0
    while True:
        inicio = pagina * 15
        fim = min(inicio + 15, len(opcoes))
        print('\n' + pergunta)
        for indice in range(inicio, fim):
            print(f'{indice + 1}. {opcoes[indice]}')
        if len(opcoes) > 15:
            print(f'Opções {inicio + 1} a {fim} de {len(opcoes)}.')
        if fim < len(opcoes):
            print('P. Próxima página')
        if pagina > 0:
            print('A. Página anterior')
        print('0. Voltar')
        resposta = input('Sua escolha: ').strip().lower()
        if resposta == '0':
            return None
        elif resposta == 'p' and fim < len(opcoes):
            pagina += 1
        elif resposta == 'a' and pagina > 0:
            pagina -= 1
        else:
            for indice in range(inicio, fim):
                if resposta == str(indice + 1):
                    return opcoes[indice]
            print('Escolha um número exibido ou uma opção de navegação.')


def escolher_distrito(bairros):
    return escolher_paginado('Escolha o distrito da região central:', listar_distritos(bairros))


def escolher_bairro_da_lista(bairros):
    rotulos = []
    for bairro in bairros:
        rotulos.append(f"{bairro['bairro']} — {bairro['distrito']}")
    rotulo = escolher_paginado('Escolha o bairro:', rotulos)
    if rotulo is None:
        return None
    for indice in range(len(rotulos)):
        if rotulos[indice] == rotulo:
            return bairros[indice]


def escolher_bairro(bairros):
    while True:
        distrito = escolher_paginado(
            'Escolha o distrito da região central ou busque o bairro pelo nome:',
            listar_distritos(bairros) + ['Buscar bairro pelo nome'],
        )
        if distrito is None:
            return None
        if distrito == 'Buscar bairro pelo nome':
            termo = input('Digite parte do nome do bairro (0 para voltar): ').strip()
            if termo == '0':
                continue
            encontrados = buscar_bairros(bairros, termo)
            if not encontrados:
                print('Nenhum bairro encontrado no recorte central. Tente parte do nome ou escolha um distrito.')
                continue
            bairro = escolher_bairro_da_lista(encontrados)
            if bairro is not None:
                return bairro
        else:
            encontrados = []
            for bairro in bairros:
                if bairro['distrito'] == distrito:
                    encontrados.append(bairro)
            bairro = escolher_bairro_da_lista(encontrados)
            if bairro is not None:
                return bairro
