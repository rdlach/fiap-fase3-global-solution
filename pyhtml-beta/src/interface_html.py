"""pyHTML Versão Beta. Para iniciar rode python pyhtml-beta/src/interface_html.py."""
import csv
from html import escape
from http.cookies import SimpleCookie
from http.server import BaseHTTPRequestHandler, HTTPServer
import hashlib
import hmac
from pathlib import Path
import secrets
import sys
import time
from urllib.parse import parse_qs, urlencode, urlsplit
import webbrowser

import main as sistema
import painel
from localidades import carregar_bairros, listar_distritos, normalizar
from prioridades import calcular_prioridade, carregar_dia, salvar_dia

ENDERECO = '127.0.0.1'
PORTA = 8765
TOKEN = secrets.token_urlsafe(24)
RAIZ = Path(__file__).resolve().parents[1]

# Travas do site publicado. No uso local, sem CODIGO_EQUIPE, nada muda.
CODIGO_EQUIPE = None        # quem define é a Lambda, com ele a área da equipe pede o código
SEGREDO_COOKIE = ''         # chave que assina o cookie da equipe
MODO_PUBLICO = False        # no site publicado o cookie é Secure e cada pessoa reforça uma vez
VALIDADE_EQUIPE = 2 * 60 * 60
LIMITE_REGISTROS = 500
LIMITE_DESCRICAO = 300
LIMITE_SOLICITACOES = 999
LIMITE_FORMULARIO = 4096
ACOES_DA_EQUIPE = {'/confirmar-status', '/atualizar', '/confirmar-dias', '/avancar', '/carregar-exemplos'}


def exige_equipe(caminho):
    if CODIGO_EQUIPE is None:
        return False
    area = caminho.startswith('/equipe') and caminho not in ('/equipe/entrar', '/equipe/sair')
    return area or caminho == '/exemplos' or caminho in ACOES_DA_EQUIPE


def assinar(valor):
    return hmac.new(SEGREDO_COOKIE.encode(), valor.encode(), hashlib.sha256).hexdigest()


def cookie_http(nome, valor, validade):
    partes = [f'{nome}={valor}', 'Path=/', f'Max-Age={validade}', 'HttpOnly', 'SameSite=Strict']
    if MODO_PUBLICO:
        partes.append('Secure')
    return '; '.join(partes)


def texto(valor):
    return escape(str(valor), quote=True)


def ocultos(dados):
    campos = ''
    for nome, valor in dados.items():
        campos += f'<input type="hidden" name="{texto(nome)}" value="{texto(valor)}">\n'
    return campos


def botao(rotulo, destino, dados=None):
    if dados is None:
        dados = {}
    return f'<form method="get" action="{texto(destino)}">{ocultos(dados)}<button>{texto(rotulo)}</button></form>\n'


def formulario(destino, conteudo, dados=None):
    if dados is None:
        dados = {}
    return f'<form method="post" action="{texto(destino)}">{ocultos({"token": TOKEN})}{ocultos(dados)}{conteudo}</form>\n'


def selecao(nome, rotulo, opcoes, atual=''):
    resultado = f'<p><label for="{nome}">{texto(rotulo)}</label><br><select id="{nome}" name="{nome}">'
    resultado += '<option value="">Selecione uma opção</option>'
    for valor, legenda in opcoes:
        marcado = ' selected' if valor == atual else ''
        resultado += f'<option value="{texto(valor)}"{marcado}>{texto(legenda)}</option>'
    return resultado + '</select></p>\n'


def opcoes_texto(valores):
    opcoes = []
    for valor in valores:
        opcoes.append((valor, valor))
    return opcoes


# Em qual aba do menu cada tela se encaixa. Quem não está aqui não marca nenhuma.
SECAO_DO_MENU = {
    **dict.fromkeys(['Comunidade', 'Cadastrar ocorrência', 'Consultar ocorrências', 'Detalhes da ocorrência',
                     'Reforçar ocorrência', 'Pendências por bairro', 'Ocorrências por bairro e categoria',
                     'Carregar exemplos'], '/comunidade'),
    **dict.fromkeys(['Área da equipe', 'Equipe de acompanhamento', 'Fila por ordem de registro', 'Últimas atualizações',
                     'Histórico de status', 'Fila de atendimento', 'Escolher ocorrência para atualizar',
                     'Alterar status', 'Avançar dias', 'Confirmar novo status', 'Confirmar avanço de dias'], '/equipe'),
}


def pagina(titulo, conteudo, mensagem=''):
    if titulo == 'Cadastrar ocorrência':
        conteudo = ('<p>Risco imediato? <a href="/ajuda">Veja os contatos de emergência.</a></p>'
                    + conteudo)
    aviso = f'<p role="status"><strong>{texto(mensagem)}</strong></p>' if mensagem else ''
    secao = SECAO_DO_MENU.get(titulo)

    def item_do_menu(rotulo, destino):
        html = botao(rotulo, destino)
        if secao == destino:
            html = html.replace('<button>', '<button aria-current="page">')
        return html

    return f'''<!DOCTYPE html>
<html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>FloodGuard | {texto(titulo)}</title><link rel="stylesheet" href="/style.css"></head><body>
<header><h1><a href="/">FloodGuard</a></h1><p>Demandas comunitárias da região central de São Paulo.</p></header>
<nav aria-label="Menu principal">{item_do_menu('Menu inicial', '/')}{item_do_menu('Comunidade', '/comunidade')}{item_do_menu('Equipe', '/equipe')}<a class="atalho" href="/ajuda">Ajuda de emergência</a></nav>
<main><h2>{texto(titulo)}</h2>{aviso}{conteudo}</main>
<footer><p>Protótipo acadêmico · Perfis simulados e registros fictícios ou consentidos.</p></footer>
</body></html>'''


def detalhes(item, dia, equipe=False):
    prioridade = calcular_prioridade(item, dia)
    nivel = prioridade['nivel'] if prioridade else 'Encerrada'
    html = f'''<h3>{texto(item['id'])} — {texto(item['tipo'])}</h3>
<p>{texto(item['bairro'])} — Distrito: {texto(item['distrito'])}</p>
<p>{texto(item['descricao'])}</p><p>Status: {texto(item['status'])} | Prioridade: {texto(nivel)}</p>
<p>Dia de abertura: {texto(item['dia_abertura'])} | Solicitações: {texto(item['solicitacoes'])}</p>'''
    if equipe and prioridade:
        html += f'''<p>Pontuação: <strong>{prioridade['pontos']}</strong> | Base: {prioridade['pontos_iniciais']}
| Dias: {prioridade['dias']} | Solicitações adicionais: {prioridade['adicionais']}</p>'''
    return html


def tabela(registros, dia, equipe=False):
    if not registros:
        return '<p>Nenhuma ocorrência encontrada.</p>'
    html = '<div class="tabela-rolavel"><table><caption>Ocorrências registradas</caption><thead><tr>'
    colunas = ['Código', 'Bairro', 'Distrito', 'Categoria', 'Problema', 'Status', 'Prioridade']
    if equipe:
        colunas.append('Pontos')
    colunas.append('Ação')
    for coluna in colunas:
        html += f'<th scope="col">{texto(coluna)}</th>'
    html += '</tr></thead><tbody>'
    for item in registros:
        prioridade = calcular_prioridade(item, dia)
        nivel = prioridade['nivel'] if prioridade else 'Encerrada'
        html += '<tr>'
        for campo in ['id', 'bairro', 'distrito', 'categoria', 'tipo', 'status']:
            html += f'<td>{texto(item[campo])}</td>'
        html += f'<td>{texto(nivel)}</td>'
        if equipe:
            pontos = prioridade['pontos'] if prioridade else '—'
            html += f'<td>{pontos}</td>'
        if equipe:
            acao = botao('Alterar status', '/equipe/status', {'codigo': item['id']})
        else:
            acao = botao('Ver detalhes', '/ocorrencia', {'codigo': item['id']})
            if item['status'] != 'Concluída':
                acao += botao('Também tenho esse problema', '/reforco', {'codigo': item['id']})
        html += f'<td>{acao}</td></tr>'
    return html + '</tbody></table></div>'


def local_do_cadastro(dados, bairros):
    for bairro in bairros:
        if bairro['id'] == dados.get('id_bairro') and bairro['distrito'] == dados.get('distrito'):
            return bairro
    raise ValueError('Escolha o distrito e um dos bairros correspondentes.')


def tipo_do_cadastro(dados):
    categoria = dados.get('categoria', '')
    tipo = dados.get('tipo', '')
    if categoria not in sistema.CATEGORIAS or tipo not in sistema.TIPOS_PROBLEMA[categoria]:
        raise ValueError('Escolha uma categoria e um tipo de problema compatíveis.')
    return categoria, tipo


def cadastro(dados, bairros, dia):
    rascunho = {}
    for campo in ['distrito', 'id_bairro', 'categoria', 'tipo', 'descricao']:
        rascunho[campo] = dados.get(campo, '')
    etapa = dados.get('etapa', 'local')
    conteudo = '<p>Preencha pelos botões. Os dados só serão gravados ao confirmar Salvar ocorrência.</p>'
    if etapa == 'local':
        campos = selecao('distrito', 'Distrito', opcoes_texto(listar_distritos(bairros)), rascunho['distrito'])
        campos += '<button name="etapa" value="local">Mostrar bairros deste distrito</button>'
        opcoes = []
        for bairro in bairros:
            if bairro['distrito'] == rascunho['distrito']:
                opcoes.append((bairro['id'], bairro['bairro']))
        if opcoes:
            campos += selecao('id_bairro', 'Bairro', opcoes, rascunho['id_bairro'])
            campos += '<button name="etapa" value="categoria">Continuar</button>'
        for campo in ['distrito', 'id_bairro']:
            rascunho.pop(campo)
    elif etapa == 'categoria':
        local_do_cadastro(rascunho, bairros)
        campos = selecao('categoria', 'Categoria', opcoes_texto(sistema.CATEGORIAS), rascunho['categoria'])
        rascunho.pop('categoria')
        campos += '<button name="etapa" value="tipo">Continuar</button> <button name="etapa" value="local">Voltar</button>'
    elif etapa == 'tipo':
        local_do_cadastro(rascunho, bairros)
        if rascunho['categoria'] not in sistema.CATEGORIAS:
            raise ValueError('Escolha uma categoria.')
        if rascunho['tipo'] not in sistema.TIPOS_PROBLEMA[rascunho['categoria']]:
            rascunho['tipo'] = ''
            rascunho['descricao'] = ''
        campos = selecao('tipo', 'Tipo de problema', opcoes_texto(sistema.TIPOS_PROBLEMA[rascunho['categoria']]), rascunho['tipo'])
        rascunho['tipo_anterior'] = rascunho.pop('tipo')
        campos += '<button name="etapa" value="descricao">Continuar</button> <button name="etapa" value="categoria">Voltar</button>'
    elif etapa == 'descricao':
        local_do_cadastro(rascunho, bairros)
        _, tipo = tipo_do_cadastro(rascunho)
        if dados.get('tipo_anterior', tipo) != tipo:
            rascunho['descricao'] = ''
        descricao = rascunho.pop('descricao') or sistema.DESCRICOES.get(tipo, '')
        campos = f'<p><label for="descricao">Descrição (você pode complementar o texto)</label><br><textarea id="descricao" name="descricao" rows="4" cols="50" maxlength="300" required>{texto(descricao)}</textarea></p>'
        campos += '<button name="etapa" value="revisao">Revisar cadastro</button> <button name="etapa" value="tipo" formnovalidate>Voltar</button>'
    elif etapa == 'revisao':
        bairro = local_do_cadastro(rascunho, bairros)
        categoria, tipo = tipo_do_cadastro(rascunho)
        if not rascunho['descricao'].strip():
            raise ValueError('A descrição é obrigatória.')
        conteudo += f'<p><strong>{texto(tipo)}</strong></p><p>{texto(bairro["bairro"])} — {texto(bairro["distrito"])}</p><p>Categoria: {texto(categoria)}</p><p>{texto(rascunho["descricao"])}</p><p>Prioridade inicial: {texto(sistema.URGENCIAS_INICIAIS.get(tipo, "Média"))}</p>'
        campos = '<button formaction="/salvar">Salvar ocorrência</button> <button name="etapa" value="local">Corrigir local</button> <button name="etapa" value="categoria">Corrigir categoria ou tipo</button> <button name="etapa" value="descricao">Corrigir descrição</button>'
    else:
        raise ValueError('Etapa de cadastro inválida.')
    conteudo += formulario('/cadastro', campos, rascunho)
    conteudo += botao('Cancelar e voltar à comunidade', '/comunidade')
    return pagina('Cadastrar ocorrência', conteudo)


def resumo(registros, visao, dia):
    conteudo = painel.indicadores(registros, sistema.CATEGORIAS, sistema.STATUS, dia)
    conteudo += painel.graficos(registros, sistema.CATEGORIAS, sistema.STATUS, dia)
    return pagina('Resumo', conteudo + botao('Voltar', visao))


def consulta(dados, registros, bairros, dia):
    campos = '<p><label for="busca">Buscar por código, bairro ou problema</label><br><input id="busca" name="busca" value="' + texto(dados.get('busca', '')) + '"></p>'
    for campo, rotulo, opcoes in [('distrito', 'Distrito', listar_distritos(bairros)), ('categoria', 'Categoria', sistema.CATEGORIAS), ('status', 'Status', sistema.STATUS)]:
        campos += selecao(campo, rotulo, opcoes_texto(opcoes), dados.get(campo, ''))
    conteudo = '<form method="get" action="/consulta">' + campos + '<button>Aplicar filtros</button></form>'
    conteudo += botao('Limpar filtros', '/consulta')
    encontrados = []
    busca = normalizar(dados.get('busca', ''))
    for item in registros:
        corresponde = True
        for campo in ['distrito', 'categoria', 'status']:
            if dados.get(campo) and dados[campo] != item[campo]:
                corresponde = False
        if busca and busca not in normalizar(item['id'] + ' ' + item['bairro'] + ' ' + item['tipo']):
            corresponde = False
        if corresponde:
            encontrados.append(item)
    conteudo += tabela(encontrados, dia) + botao('Voltar à comunidade', '/comunidade')
    return pagina('Consultar ocorrências', conteudo, dados.get('mensagem', ''))


def renderizar(caminho, dados, registros, bairros, dia):
    if caminho == '/':
        return (RAIZ / 'index.html').read_text(encoding='utf-8')
    if caminho == '/comunidade':
        conteudo = '<div class="menu-opcoes">'
        for rotulo, destino in [('Registrar um problema', '/cadastro'), ('Consultar ocorrências', '/consulta'), ('Reforçar uma ocorrência existente', '/consulta'), ('Ver resumo', '/resumo'), ('Ver pendências por bairro', '/pendencias'), ('Explorar por bairro e categoria', '/bairros')]:
            conteudo += botao(rotulo, destino)
        conteudo += '</div>'
        if not registros:
            conteudo += '<p>A base ainda está vazia.</p>'
            if CODIGO_EQUIPE is None:
                conteudo += botao('Carregar 12 exemplos fictícios', '/exemplos')
        return pagina('Comunidade', conteudo, dados.get('mensagem', ''))
    if caminho == '/cadastro':
        return cadastro(dados, bairros, dia)
    if caminho == '/consulta':
        return consulta(dados, registros, bairros, dia)
    if caminho == '/ocorrencia':
        item = sistema.encontrar_ocorrencia(registros, dados.get('codigo', ''))
        conteudo = detalhes(item, dia)
        if item['status'] != 'Concluída':
            conteudo += botao('Também tenho esse problema', '/reforco', {'codigo': item['id']})
        return pagina('Detalhes da ocorrência', conteudo + botao('Voltar à consulta', '/consulta'))
    if caminho == '/reforco':
        item = sistema.encontrar_ocorrencia(registros, dados.get('codigo', ''))
        if item['status'] == 'Concluída':
            raise ValueError('Essa ocorrência já está concluída.')
        conteudo = detalhes(item, dia) + '<p>Confirme se é o mesmo problema para registrar outra solicitação.</p>'
        conteudo += formulario('/reforcar', '<button>Confirmar solicitação adicional</button>', {'codigo': item['id']})
        return pagina('Reforçar ocorrência', conteudo + botao('Cancelar', '/consulta'))
    if caminho == '/resumo':
        visao = '/equipe' if dados.get('visao') == 'equipe' else '/comunidade'
        return resumo(registros, visao, dia)
    if caminho == '/pendencias':
        quantidades = {}
        for item in registros:
            if item['status'] != 'Concluída':
                nome = item['bairro']
                quantidades[nome] = quantidades.get(nome, 0) + 1
        conteudo = '<ul>'
        for bairro in sorted(quantidades, key=lambda nome: (-quantidades[nome], nome.casefold())):
            conteudo += f'<li>{texto(bairro)}: {quantidades[bairro]} pendência(s)</li>'
        if not quantidades:
            conteudo += '<li>Nenhuma pendência registrada.</li>'
        return pagina('Pendências por bairro', conteudo + '</ul>' + botao('Voltar', '/comunidade'))
    if caminho == '/equipe/entrar':
        if CODIGO_EQUIPE is None:
            return pagina('Área da equipe', '<p>Neste modo local a área da equipe não pede código.</p>' + botao('Abrir a equipe', '/equipe'))
        return pagina('Área da equipe', pedir_codigo())
    if caminho == '/equipe':
        conteudo = f'<p>Dia simulado atual: <strong>{dia}</strong></p><div class="menu-opcoes">'
        for rotulo, destino in [('Ver fila por pontuação', '/equipe/fila'), ('Fila por ordem de registro', '/equipe/fifo'), ('Histórico de status', '/equipe/historico'), ('Últimas atualizações', '/equipe/recentes'), ('Atualizar status', '/equipe/status'), ('Avançar dias da simulação', '/equipe/dias')]:
            conteudo += botao(rotulo, destino)
        conteudo += botao('Ver resumo', '/resumo', {'visao': 'equipe'})
        conteudo += '</div>'
        if CODIGO_EQUIPE is not None:
            conteudo += formulario('/equipe/sair', '<button formnovalidate>Sair da área da equipe</button>')
        return pagina('Equipe de acompanhamento', conteudo, dados.get('mensagem', ''))
    if caminho == '/bairros':
        grupos = {}
        for item in registros:
            grupos.setdefault(item['bairro'], {}).setdefault(item['categoria'], []).append(item)
        conteudo = ''
        for bairro, categorias in sorted(grupos.items()):
            conteudo += f'<details><summary>{texto(bairro)}</summary>'
            for categoria, itens in sorted(categorias.items()):
                conteudo += f'<h3>{texto(categoria)}</h3>' + tabela(itens, dia)
            conteudo += '</details>'
        return pagina('Ocorrências por bairro e categoria', conteudo or '<p>Nenhuma ocorrência registrada.</p>')
    if caminho == '/equipe/fifo':
        fila = sorted((item for item in registros if item['status'] == 'Aberta'),
                      key=lambda item: int(item['id'][3:]))
        return pagina('Fila por ordem de registro', tabela(fila, dia, equipe=True))
    if caminho in ('/equipe/historico', '/equipe/recentes'):
        recentes = caminho.endswith('/recentes')
        return pagina('Últimas atualizações' if recentes else 'Histórico de status',
                      painel.historico(registros, recentes))
    if caminho == '/equipe/fila':
        fila = []
        for item in registros:
            prioridade = calcular_prioridade(item, dia)
            if prioridade is not None:
                fila.append({'item': item, 'prioridade': prioridade})
        ordenados = []
        for elemento in sorted(fila, key=sistema.chave_da_fila):
            ordenados.append(elemento['item'])
        return pagina('Fila de atendimento', tabela(ordenados, dia, equipe=True) + botao('Voltar à equipe', '/equipe'))
    if caminho == '/equipe/status':
        if not dados.get('codigo'):
            return pagina('Escolher ocorrência para atualizar', tabela(registros, dia, equipe=True) + botao('Voltar', '/equipe'))
        item = sistema.encontrar_ocorrencia(registros, dados['codigo'])
        campos = selecao('status', 'Novo status', opcoes_texto(sistema.STATUS), dados.get('status', item['status']))
        campos += '<button>Revisar alteração</button>'
        conteudo = detalhes(item, dia, equipe=True) + formulario('/confirmar-status', campos, {'codigo': item['id']})
        return pagina('Alterar status', conteudo + botao('Voltar sem alterar', '/equipe/status'))
    if caminho == '/equipe/dias':
        campos = '<p><label for="dias">Quantos dias deseja avançar?</label><br><input id="dias" name="dias" type="number" min="1" max="365" required></p><button>Revisar avanço</button>'
        return pagina('Avançar dias', f'<p>Dia simulado atual: {dia}</p>' + formulario('/confirmar-dias', campos) + botao('Cancelar', '/equipe'))
    if caminho == '/exemplos':
        if registros:
            raise ValueError('Os exemplos só podem ser carregados em uma base vazia.')
        conteudo = '<p>Carregar 12 ocorrências fictícias na base atual?</p>'
        return pagina('Carregar exemplos', conteudo + formulario('/carregar-exemplos', '<button>Confirmar carregamento</button>') + botao('Cancelar', '/comunidade'))
    if caminho == '/encerrar':
        return pagina('Encerrar aplicação', '<p>Deseja encerrar o programa Python desta interface?</p>' + formulario('/encerrar', '<button>Confirmar encerramento</button>') + botao('Continuar usando', '/'))
    raise ValueError('Página não encontrada.')


def pedir_codigo():
    campo = ('<p>Somente a equipe altera status e avança os dias. Informe o código de acesso.</p>'
             '<p><label for="codigo">Código de acesso</label><br>'
             '<input id="codigo" name="codigo" type="password" autocomplete="off" maxlength="64" required></p>'
             '<button>Entrar</button>')
    return formulario('/equipe/entrar', campo) + botao('Voltar ao menu inicial', '/')


def quantidade_dias(valor):
    if not valor.isdecimal() or len(valor) > 3 or not 1 <= int(valor) <= 365:
        raise ValueError('Informe uma quantidade de 1 a 365 dias.')
    return int(valor)


def interpretar_dados(conteudo):
    resultado = {}
    for nome, valores in parse_qs(conteudo, keep_blank_values=True, max_num_fields=30).items():
        if len(valores) != 1:
            raise ValueError('O formulário contém campos repetidos.')
        resultado[nome] = valores[0]
    return resultado


class InterfaceHTML(BaseHTTPRequestHandler):
    """Adaptador HTTP da biblioteca padrão; as regras ficam em funções do programa."""
    novos_cookies = ()

    def cookies(self):
        lido = SimpleCookie()
        try:
            lido.load(self.headers.get('Cookie', ''))
        except Exception:
            return {}
        return {nome: parte.value for nome, parte in lido.items()}

    def equipe_autenticada(self):
        valor = self.cookies().get('fg_equipe', '')
        expira, _, assinatura = valor.partition('.')
        if not expira.isdecimal() or int(expira) < time.time():
            return False
        return hmac.compare_digest(assinatura, assinar('equipe|' + expira))

    def reforcos_da_pessoa(self):
        return [codigo for codigo in self.cookies().get('fg_ja', '').split('.') if codigo]

    def responder(self, html, status=200, tipo='text/html'):
        corpo = html.encode('utf-8')
        self.send_response(status)
        for cookie in self.novos_cookies:
            self.send_header('Set-Cookie', cookie)
        self.send_header('Content-Type', tipo + '; charset=utf-8')
        self.send_header('Content-Length', str(len(corpo)))
        self.send_header('Cache-Control', 'no-store')
        self.send_header('Content-Security-Policy', "default-src 'none'; style-src 'self'; form-action 'self'; frame-ancestors 'none'; base-uri 'none'")
        self.end_headers()
        self.wfile.write(corpo)

    def redirecionar(self, destino, mensagem):
        self.send_response(303)
        for cookie in self.novos_cookies:
            self.send_header('Set-Cookie', cookie)
        self.send_header('Location', destino + '?' + urlencode({'mensagem': mensagem}))
        self.send_header('Content-Length', '0')
        self.end_headers()

    def do_GET(self):
        try:
            url = urlsplit(self.path)
            if url.path == '/style.css':
                self.responder((RAIZ / 'style.css').read_text(encoding='utf-8'), tipo='text/css')
                return
            if url.path == '/ajuda':
                self.responder(pagina('Precisa de ajuda agora?', painel.AJUDA))
                return
            if exige_equipe(url.path) and not self.equipe_autenticada():
                self.responder(pagina('Área da equipe', pedir_codigo()))
                return
            dados = interpretar_dados(url.query)
            bairros = carregar_bairros()
            dia = carregar_dia()
            registros = sistema.carregar(bairros, dia)
            self.responder(renderizar(url.path, dados, registros, bairros, dia))
        except (ValueError, csv.Error) as erro:
            self.responder(pagina('Confira os dados', f'<p>{texto(erro)}</p>' + botao('Voltar ao início', '/')), 400)
        except OSError:
            self.responder(pagina('Não foi possível abrir os dados', '<p>Confira os arquivos da pasta dados. Eles foram preservados.</p>'), 500)

    def do_POST(self):
        try:
            tamanho = int(self.headers.get('Content-Length', '0'))
            if not 0 < tamanho <= LIMITE_FORMULARIO:
                raise ValueError('Formulário vazio ou muito grande.')
            dados = interpretar_dados(self.rfile.read(tamanho).decode('utf-8'))
            if dados.pop('token', '') != TOKEN:
                self.responder(pagina('Reabra o formulário', '<p>Use os botões da aplicação para confirmar a ação.</p>'), 403)
                return
            caminho = urlsplit(self.path).path
            if exige_equipe(caminho) and not self.equipe_autenticada():
                self.responder(pagina('Acesso restrito', '<p>Somente a equipe pode fazer essa ação.</p>' + botao('Entrar como equipe', '/equipe/entrar')), 403)
                return
            if caminho == '/equipe/entrar':
                self.entrar_na_equipe(dados)
                return
            if caminho == '/equipe/sair':
                self.novos_cookies = [cookie_http('fg_equipe', '', 0)]
                self.redirecionar('/', 'Você saiu da área da equipe.')
                return
            bairros = carregar_bairros()
            dia = carregar_dia()
            registros = sistema.carregar(bairros, dia)
            if caminho == '/cadastro':
                self.responder(cadastro(dados, bairros, dia))
            elif caminho == '/salvar':
                local_do_cadastro(dados, bairros)
                if len(registros) >= LIMITE_REGISTROS:
                    raise ValueError('A base da demonstração chegou ao limite de registros.')
                if len(dados.get('descricao', '')) > LIMITE_DESCRICAO:
                    raise ValueError(f'A descrição pode ter até {LIMITE_DESCRICAO} caracteres.')
                item = sistema.registrar_ocorrencia(registros, bairros, dados.get('id_bairro', ''), dados.get('categoria', ''), dados.get('tipo', ''), dados.get('descricao', ''), dia)
                self.redirecionar('/consulta', f"Ocorrência {item['id']} cadastrada.")
            elif caminho == '/reforcar':
                codigo = dados.get('codigo', '')
                ja = self.reforcos_da_pessoa()
                if MODO_PUBLICO and codigo in ja:
                    raise ValueError('Você já registrou que também tem esse problema.')
                if int(sistema.encontrar_ocorrencia(registros, codigo)['solicitacoes']) >= LIMITE_SOLICITACOES:
                    raise ValueError('Essa ocorrência já atingiu o limite de solicitações.')
                sistema.registrar_reforco(registros, codigo)
                if MODO_PUBLICO:
                    self.novos_cookies = [cookie_http('fg_ja', '.'.join((ja + [codigo])[-60:]), 30 * 86400)]
                self.redirecionar('/consulta', 'Sua solicitação foi vinculada à ocorrência.')
            elif caminho == '/confirmar-status':
                item = sistema.encontrar_ocorrencia(registros, dados.get('codigo', ''))
                status = dados.get('status', '')
                if status not in sistema.STATUS:
                    raise ValueError('Escolha um status válido.')
                conteudo = detalhes(item, dia, equipe=True) + f'<p>Alterar o status para <strong>{texto(status)}</strong>?</p>'
                conteudo += formulario('/atualizar', '<button>Confirmar alteração</button>', {'codigo': item['id'], 'status': status})
                conteudo += botao('Voltar sem alterar', '/equipe/status', {'codigo': item['id'], 'status': status})
                self.responder(pagina('Confirmar novo status', conteudo))
            elif caminho == '/atualizar':
                sistema.registrar_status(registros, dados.get('codigo', ''), dados.get('status', ''), dia)
                self.redirecionar('/equipe', 'Status atualizado.')
            elif caminho == '/confirmar-dias':
                dias = quantidade_dias(dados.get('dias', ''))
                conteudo = f'<p>Avançar do dia {dia} para o dia {dia + dias}?</p>'
                conteudo += formulario('/avancar', '<button>Confirmar avanço</button>', {'dias': str(dias), 'dia_anterior': str(dia)})
                self.responder(pagina('Confirmar avanço de dias', conteudo + botao('Cancelar', '/equipe/dias')))
            elif caminho == '/avancar':
                dias = quantidade_dias(dados.get('dias', ''))
                if dados.get('dia_anterior') != str(dia):
                    raise ValueError('O dia atual mudou. Revise o avanço novamente.')
                salvar_dia(dia + dias)
                self.redirecionar('/equipe', 'Dia simulado atualizado.')
            elif caminho == '/carregar-exemplos':
                if registros:
                    raise ValueError('A base já tem registros. Nenhum dado foi substituído.')
                arquivo_exemplo = RAIZ / 'dados' / 'ocorrencias_exemplo.csv'
                if not arquivo_exemplo.exists():
                    raise ValueError('O arquivo de exemplos não foi encontrado.')
                exemplos = sistema.carregar(bairros, dia, arquivo_exemplo)
                sistema.salvar(exemplos)
                self.redirecionar('/consulta', f'{len(exemplos)} exemplos fictícios foram carregados.')
            elif caminho == '/encerrar':
                self.responder(pagina('Aplicação encerrada', '<p>Você já pode fechar esta aba. Para usar novamente, inicie o programa Python.</p>'))
                self.server.encerrar = True
            else:
                raise ValueError('Ação não encontrada.')
        except (ValueError, csv.Error) as erro:
            self.responder(pagina('Confira o formulário', f'<p>{texto(erro)}</p><p>Use o botão Voltar do navegador para corrigir os campos.</p>' + botao('Menu da comunidade', '/comunidade')), 400)
        except OSError:
            self.responder(pagina('Não foi possível salvar', '<p>A alteração não foi aplicada. Confira os arquivos e tente novamente.</p>'), 500)

    def entrar_na_equipe(self, dados):
        informado = dados.get('codigo', '').encode()
        if CODIGO_EQUIPE is None or not hmac.compare_digest(informado, CODIGO_EQUIPE.encode()):
            self.responder(pagina('Área da equipe', '<p>Código incorreto.</p>' + pedir_codigo()), 403)
            return
        expira = str(int(time.time()) + VALIDADE_EQUIPE)
        self.novos_cookies = [cookie_http('fg_equipe', expira + '.' + assinar('equipe|' + expira), VALIDADE_EQUIPE)]
        self.redirecionar('/equipe', 'Acesso liberado.')


def main():
    try:
        servidor = HTTPServer((ENDERECO, PORTA), InterfaceHTML)
    except OSError:
        print(f'A porta {PORTA} já está em uso. Feche outra instância da interface antes de iniciar.')
        return
    url = f'http://{ENDERECO}:{PORTA}'
    print(f'FloodGuard pyHTML - Versão Beta: {url}')
    print('Deixe este terminal aberto. Para encerrar, pressione Ctrl+C.')
    if '--sem-navegador' not in sys.argv:
        webbrowser.open(url)
    try:
        servidor.encerrar = False
        while not servidor.encerrar:
            servidor.handle_request()
    except KeyboardInterrupt:
        print('\nInterface encerrada.')
    finally:
        servidor.server_close()


if __name__ == '__main__':
    main()
