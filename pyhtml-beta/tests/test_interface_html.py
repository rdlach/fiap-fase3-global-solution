"""Fluxos HTTP reais com CSV temporário, sem alterar os dados da equipe."""
from html.parser import HTMLParser
from http.client import HTTPConnection
from http.server import HTTPServer
from pathlib import Path
import sys
import tempfile
from threading import Thread
import unittest
from unittest.mock import patch
from urllib.parse import urlencode

RAIZ = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(RAIZ / 'src'))
import interface_html as tela
import localidades
import main as sistema
import prioridades


class Formularios(HTMLParser):
    """Lê os campos enviados pelos formulários produzidos pela aplicação."""
    def __init__(self, html):
        super().__init__()
        self.formularios = []
        self.atual = None
        self.feed(html)

    def handle_starttag(self, tag, atributos):
        atributos = dict(atributos)
        if tag == 'form':
            self.atual = {'acao': atributos.get('action'), 'campos': {}}
            self.formularios.append(self.atual)
        elif tag == 'input' and self.atual is not None and atributos.get('name'):
            nome = atributos['name']
            if nome in self.atual['campos']:
                raise AssertionError('Campo repetido no formulário: ' + nome)
            self.atual['campos'][nome] = atributos.get('value', '')

    def handle_endtag(self, tag):
        if tag == 'form':
            self.atual = None


class BaseInterface(unittest.TestCase):
    def setUp(self):
        self.temporario = tempfile.TemporaryDirectory(prefix='floodguard-html-')
        self.addCleanup(self.temporario.cleanup)
        pasta = Path(self.temporario.name)
        self.csv = pasta / 'ocorrencias.csv'
        self.dia = pasta / 'dia_simulado.txt'
        for modulo, nome, valor in [(sistema, 'ARQUIVO', self.csv), (prioridades, 'ARQUIVO_DIA', self.dia)]:
            alteracao = patch.object(modulo, nome, valor)
            alteracao.start()
            self.addCleanup(alteracao.stop)
        self.bairros = localidades.carregar_bairros()
        self.bairro = localidades.buscar_bairros(self.bairros, 'Liberdade', exato=True)[0]
        silencioso = patch.object(tela.InterfaceHTML, 'log_message')
        silencioso.start()
        self.addCleanup(silencioso.stop)
        self.servidor = HTTPServer(('127.0.0.1', 0), tela.InterfaceHTML)
        self.servidor.encerrar = False
        self.thread = Thread(target=self.servidor.serve_forever, kwargs={'poll_interval': 0.01}, daemon=True)
        self.thread.start()
        self.addCleanup(self.fechar_servidor)

    def fechar_servidor(self):
        self.servidor.shutdown()
        self.servidor.server_close()
        self.thread.join(timeout=2)

    def requisicao(self, caminho, dados=None, token=True, cookie=None):
        conexao = HTTPConnection('127.0.0.1', self.servidor.server_port, timeout=5)
        self.addCleanup(conexao.close)
        cabecalhos = {'Cookie': cookie} if cookie else {}
        if dados is None:
            conexao.request('GET', caminho, headers=cabecalhos)
        else:
            campos = dict(dados)
            if token:
                campos['token'] = tela.TOKEN
            cabecalhos['Content-Type'] = 'application/x-www-form-urlencoded'
            conexao.request('POST', caminho, urlencode(campos), cabecalhos)
        resposta = conexao.getresponse()
        return resposta.status, resposta.read().decode('utf-8'), dict(resposta.getheaders())

    def campos(self, html, acao='/cadastro'):
        formas = Formularios(html).formularios
        return next(forma['campos'] for forma in formas if forma['acao'] == acao)

    def cadastrar(self, descricao='Lixo acumulado na praça.'):
        dados = {'distrito': self.bairro['distrito'], 'id_bairro': self.bairro['id'], 'categoria': 'Limpeza', 'tipo': 'Lixo acumulado', 'descricao': descricao}
        resposta = self.requisicao('/salvar', dados)
        self.assertEqual(resposta[0], 303)
        return sistema.carregar(self.bairros)[-1]


class TestInterfaceHTML(BaseInterface):
    def test_menu_e_consultas_nao_gravam_dados(self):
        for caminho in ['/', '/comunidade', '/equipe', '/consulta', '/resumo', '/pendencias', '/bairros', '/ajuda', '/equipe/fifo', '/equipe/historico', '/equipe/recentes', '/equipe/fila', '/equipe/status', '/equipe/dias', '/encerrar']:
            with self.subTest(caminho=caminho):
                status, html, _ = self.requisicao(caminho)
                self.assertEqual(status, 200)
                self.assertNotIn('<script', html)
                self.assertNotIn('disabled', html)
        self.assertFalse(self.csv.exists())
        self.assertFalse(self.dia.exists())
        self.assertFalse(self.servidor.encerrar)

    def test_css_e_fontes_da_beta_permanecem_isolados(self):
        status, html, _ = self.requisicao('/')
        self.assertEqual(status, 200)
        self.assertIn('Cuide do seu bairro', html)
        self.assertIn('href="/style.css"', html)
        status, css, cabecalhos = self.requisicao('/style.css')
        self.assertEqual(status, 200)
        self.assertEqual(cabecalhos['Content-Type'], 'text/css; charset=utf-8')
        self.assertIn('button:focus-visible', css)
        self.assertEqual(Path(sistema.__file__).resolve().parent, RAIZ / 'src')
        self.assertEqual(tela.RAIZ, RAIZ)
        self.assertEqual(localidades.ARQUIVO_BAIRROS.parent, RAIZ / 'dados')

    def test_cadastro_por_etapas_com_volta_e_persistencia(self):
        _, html, _ = self.requisicao('/cadastro')
        dados = self.campos(html)
        dados.update(distrito='Liberdade', etapa='local')
        _, html, _ = self.requisicao('/cadastro', dados)
        self.assertIn('Bairro', html)
        dados = self.campos(html)
        dados.update(distrito='Liberdade', id_bairro=self.bairro['id'], etapa='categoria')
        _, html, _ = self.requisicao('/cadastro', dados)
        dados = self.campos(html)
        dados.update(categoria='Limpeza', etapa='tipo')
        _, html, _ = self.requisicao('/cadastro', dados)
        self.assertIn('Lixo acumulado', html)
        self.assertNotIn('Poste apagado', html)
        dados = self.campos(html)
        dados.update(tipo='Lixo acumulado', etapa='descricao')
        _, html, _ = self.requisicao('/cadastro', dados)
        self.assertIn(sistema.DESCRICOES['Lixo acumulado'], html)
        dados = self.campos(html)
        dados.update(descricao='Lixo na praça, com "aspas" e acentuação.', etapa='revisao')
        _, html, _ = self.requisicao('/cadastro', dados)
        self.assertFalse(self.csv.exists())
        revisao = self.campos(html)
        voltar = dict(revisao, etapa='local')
        status, html, _ = self.requisicao('/cadastro', voltar)
        self.assertEqual(status, 200)
        self.assertEqual(self.campos(html)['descricao'], dados['descricao'])
        status, _, cabecalhos = self.requisicao('/salvar', revisao)
        self.assertEqual(status, 303)
        self.requisicao(cabecalhos['Location'])
        self.requisicao(cabecalhos['Location'])
        registros = sistema.carregar(self.bairros)
        self.assertEqual(len(registros), 1)
        self.assertEqual(registros[0]['descricao'], dados['descricao'])
        self.assertEqual(registros[0]['urgencia'], 'Baixa')

    def test_trocar_tipo_renova_descricao_e_local_incompativel_e_rejeitado(self):
        dados = dict(distrito='Liberdade', id_bairro=self.bairro['id'], categoria='Limpeza', tipo='Descarte de entulho', tipo_anterior='Lixo acumulado', descricao='Descrição antiga', etapa='descricao')
        status, html, _ = self.requisicao('/cadastro', dados)
        self.assertEqual(status, 200)
        self.assertIn(sistema.DESCRICOES['Descarte de entulho'], html)
        self.assertNotIn('Descrição antiga', html)
        dados['distrito'] = 'Sé'
        self.assertEqual(self.requisicao('/salvar', dados)[0], 400)
        self.assertFalse(self.csv.exists())

    def test_reforco_e_status_compartilham_csv_e_exigem_confirmacao(self):
        item = self.cadastrar()
        codigo = item['id']
        self.requisicao('/reforco?' + urlencode({'codigo': codigo}))
        self.assertEqual(sistema.carregar(self.bairros)[0]['solicitacoes'], '1')
        self.assertEqual(self.requisicao('/reforcar', {'codigo': codigo})[0], 303)
        self.assertEqual(sistema.carregar(self.bairros)[0]['solicitacoes'], '2')
        status, html, _ = self.requisicao('/confirmar-status', {'codigo': codigo, 'status': 'Concluída'})
        self.assertEqual(status, 200)
        self.assertEqual(sistema.carregar(self.bairros)[0]['status'], 'Aberta')
        self.assertEqual(self.requisicao('/atualizar', self.campos(html, '/atualizar'))[0], 303)
        self.assertEqual(sistema.carregar(self.bairros)[0]['status'], 'Concluída')
        status, html, _ = self.requisicao('/ocorrencia?codigo=' + codigo)
        self.assertEqual(status, 200)
        self.assertIn(item['descricao'], html)
        self.assertNotIn('Também tenho esse problema', html)
        self.assertEqual(self.requisicao('/reforcar', {'codigo': codigo})[0], 400)
        self.assertEqual(sistema.carregar(self.bairros)[0]['solicitacoes'], '2')

    def test_cadastro_de_animais(self):
        base = {'distrito': self.bairro['distrito'], 'id_bairro': self.bairro['id'], 'categoria': 'Animais'}
        for tipo, urgencia in [('Cães latindo sem parar', 'Baixa'), ('Animal atropelado', 'Alta'),
                               ('Retirada de ninho ou animal silvestre', 'Média')]:
            with self.subTest(tipo=tipo):
                self.assertEqual(self.requisicao('/salvar', dict(base, tipo=tipo, descricao=sistema.DESCRICOES[tipo]))[0], 303)
                item = sistema.carregar(self.bairros)[-1]
                self.assertEqual((item['categoria'], item['tipo'], item['urgencia']), ('Animais', tipo, urgencia))
        _, html, _ = self.requisicao('/resumo')
        self.assertIn('Animais', html)
        _, html, _ = self.requisicao('/cadastro', dict(base, etapa='tipo'))
        self.assertIn('Cães latindo sem parar', html)

    def test_cadastro_de_incendio_e_historico(self):
        dados = {'distrito': self.bairro['distrito'], 'id_bairro': self.bairro['id'],
                 'categoria': 'Incêndio', 'tipo': 'Incêndio em imóvel',
                 'descricao': 'Ocorrência fictícia para teste.'}
        self.assertEqual(self.requisicao('/salvar', dados)[0], 303)
        self.assertEqual(self.requisicao('/atualizar', {'codigo': 'FG-001', 'status': 'Em análise'})[0], 303)
        _, html, _ = self.requisicao('/equipe/historico')
        self.assertIn('FG-001: Aberta → Em análise', html)
        _, html, _ = self.requisicao('/equipe/fifo')
        self.assertNotIn('FG-001', html)
        _, html, _ = self.requisicao('/resumo')
        self.assertIn('Incêndio', html)
        self.assertIn('1 (100.0%)', html)

    def test_ajuda_fica_disponivel_com_csv_invalido(self):
        self.csv.write_text('invalido', encoding='utf-8')
        status, html, _ = self.requisicao('/ajuda')
        self.assertEqual(status, 200)
        for numero in ('190', '192', '193', '199'):
            self.assertIn('href="tel:' + numero + '"', html)
        self.assertIn('Receber alertas', html)

    def test_dias_confirmacao_e_prioridade_sem_pontos_na_comunidade(self):
        self.cadastrar()
        status, html, _ = self.requisicao('/confirmar-dias', {'dias': '9'})
        self.assertEqual(status, 200)
        self.assertEqual(prioridades.carregar_dia(), 1)
        dados = self.campos(html, '/avancar')
        self.assertEqual(self.requisicao('/avancar', dados)[0], 303)
        self.assertEqual(prioridades.carregar_dia(), 10)
        self.assertEqual(self.requisicao('/avancar', dados)[0], 400)
        self.assertEqual(prioridades.carregar_dia(), 10)
        _, html, _ = self.requisicao('/consulta')
        self.assertIn('Crítico', html)
        self.assertNotIn('Pontos', html)
        _, html, _ = self.requisicao('/equipe/fila')
        self.assertIn('Pontos', html)
        self.assertIn('<td>9</td>', html)

    def test_exemplos_e_fila_ordenada_sem_substituir_base(self):
        self.assertEqual(self.requisicao('/carregar-exemplos', {})[0], 303)
        registros = sistema.carregar(self.bairros)
        self.assertEqual(len(registros), 12)
        antes = self.csv.read_bytes()
        self.assertEqual(self.requisicao('/carregar-exemplos', {})[0], 400)
        self.assertEqual(self.csv.read_bytes(), antes)
        _, html, _ = self.requisicao('/equipe/fila')
        fila = [{'item': item, 'prioridade': prioridades.calcular_prioridade(item, 1)} for item in registros if item['status'] != 'Concluída']
        posicoes = [html.index('<td>' + elemento['item']['id'] + '</td>') for elemento in sorted(fila, key=sistema.chave_da_fila)]
        self.assertEqual(posicoes, sorted(posicoes))
        _, html, _ = self.requisicao('/consulta?' + urlencode({'busca': 'higienopolis'}))
        self.assertIn('Higienópolis', html)

    def test_validacoes_nao_alteram_csv_e_html_escapa_texto(self):
        self.cadastrar('<script>alert("teste")</script> & dados fictícios')
        antes = self.csv.read_bytes()
        self.assertEqual(self.requisicao('/reforcar', {'codigo': 'FG-001'}, token=False)[0], 403)
        self.assertEqual(self.requisicao('/atualizar', {'codigo': 'FG-001', 'status': 'Inexistente'})[0], 400)
        self.assertEqual(self.requisicao('/reforcar', {'codigo': 'FG-999'})[0], 400)
        for dias in ['0', '-1', '366', 'abc']:
            self.assertEqual(self.requisicao('/confirmar-dias', {'dias': dias})[0], 400)
        self.assertEqual(self.csv.read_bytes(), antes)
        _, html, _ = self.requisicao('/reforco?codigo=FG-001')
        self.assertNotIn('<script>', html)
        self.assertIn('&lt;script&gt;', html)

    def test_encerramento_por_botao(self):
        _, html, _ = self.requisicao('/encerrar')
        self.assertFalse(self.servidor.encerrar)
        self.assertEqual(self.requisicao('/encerrar', self.campos(html, '/encerrar'))[0], 200)
        self.assertTrue(self.servidor.encerrar)


class TestSitePublico(BaseInterface):
    """Com código da equipe e modo público, só a equipe altera o que já foi cadastrado."""
    CODIGO = 'codigo-de-teste-da-equipe'

    def setUp(self):
        super().setUp()
        for nome, valor in [('CODIGO_EQUIPE', self.CODIGO), ('SEGREDO_COOKIE', 'segredo-de-teste'), ('MODO_PUBLICO', True)]:
            alteracao = patch.object(tela, nome, valor)
            alteracao.start()
            self.addCleanup(alteracao.stop)

    def entrar_como_equipe(self):
        status, _, cabecalhos = self.requisicao('/equipe/entrar', {'codigo': self.CODIGO})
        self.assertEqual(status, 303)
        cookie = cabecalhos['Set-Cookie']
        self.assertIn('HttpOnly', cookie)
        self.assertIn('Secure', cookie)
        self.assertIn('SameSite=Strict', cookie)
        return cookie.split(';')[0]

    def test_visitante_nao_altera_nem_ve_a_area_da_equipe(self):
        item = self.cadastrar()
        antes = (self.csv.read_bytes(), self.dia.exists())
        for caminho in ['/equipe', '/equipe/fila', '/equipe/status', '/equipe/dias', '/exemplos']:
            with self.subTest(caminho=caminho):
                status, html, _ = self.requisicao(caminho)
                self.assertEqual(status, 200)
                self.assertIn('Código de acesso', html)
                self.assertNotIn('Alterar status', html)
        acoes = {'/confirmar-status': {'codigo': item['id'], 'status': 'Concluída'},
                 '/atualizar': {'codigo': item['id'], 'status': 'Concluída'},
                 '/confirmar-dias': {'dias': '5'}, '/avancar': {'dias': '5', 'dia_anterior': '1'},
                 '/carregar-exemplos': {}}
        for caminho, dados in acoes.items():
            with self.subTest(caminho=caminho):
                self.assertEqual(self.requisicao(caminho, dados)[0], 403)
        self.assertEqual((self.csv.read_bytes(), self.dia.exists()), antes)

    def test_codigo_errado_e_cookie_falso_sao_recusados(self):
        status, html, cabecalhos = self.requisicao('/equipe/entrar', {'codigo': 'errado'})
        self.assertEqual(status, 403)
        self.assertNotIn('Set-Cookie', cabecalhos)
        for cookie in ['fg_equipe=9999999999.abc', 'fg_equipe=1.' + tela.assinar('equipe|1'), 'fg_equipe=']:
            with self.subTest(cookie=cookie):
                self.assertEqual(self.requisicao('/atualizar', {'codigo': 'FG-001', 'status': 'Concluída'}, cookie=cookie)[0], 403)

    def test_equipe_com_codigo_altera_status_e_sai(self):
        item = self.cadastrar()
        cookie = self.entrar_como_equipe()
        status, html, _ = self.requisicao('/equipe/fila', cookie=cookie)
        self.assertIn('Pontos', html)
        self.assertEqual(self.requisicao('/atualizar', {'codigo': item['id'], 'status': 'Em análise'}, cookie=cookie)[0], 303)
        self.assertEqual(sistema.carregar(self.bairros)[0]['status'], 'Em análise')
        status, _, cabecalhos = self.requisicao('/equipe/sair', {}, cookie=cookie)
        self.assertEqual(status, 303)
        self.assertIn('Max-Age=0', cabecalhos['Set-Cookie'])

    def test_comunidade_nao_oferece_carga_de_exemplos(self):
        _, html, _ = self.requisicao('/comunidade')
        self.assertNotIn('Carregar 12 exemplos', html)

    def test_reforco_uma_vez_por_pessoa(self):
        item = self.cadastrar()
        status, _, cabecalhos = self.requisicao('/reforcar', {'codigo': item['id']})
        self.assertEqual(status, 303)
        cookie = cabecalhos['Set-Cookie'].split(';')[0]
        self.assertEqual(self.requisicao('/reforcar', {'codigo': item['id']}, cookie=cookie)[0], 400)
        self.assertEqual(sistema.carregar(self.bairros)[0]['solicitacoes'], '2')

    def test_limites_de_gravacao(self):
        dados = {'distrito': self.bairro['distrito'], 'id_bairro': self.bairro['id'], 'categoria': 'Limpeza', 'tipo': 'Lixo acumulado'}
        self.assertEqual(self.requisicao('/salvar', dict(dados, descricao='x' * (tela.LIMITE_DESCRICAO + 1)))[0], 400)
        self.assertFalse(self.csv.exists())
        self.assertEqual(self.requisicao('/salvar', dict(dados, descricao='x' * 5000))[0], 400)
        with patch.object(tela, 'LIMITE_REGISTROS', 1):
            self.cadastrar()
            self.assertEqual(self.requisicao('/salvar', dict(dados, descricao='Outro'))[0], 400)
        self.assertEqual(len(sistema.carregar(self.bairros)), 1)

    def test_resumo_publico_traz_graficos_sem_estilo_inline(self):
        self.assertEqual(self.requisicao('/carregar-exemplos', {}, cookie=self.entrar_como_equipe())[0], 303)
        status, html, cabecalhos = self.requisicao('/resumo')
        self.assertEqual(status, 200)
        self.assertEqual(html.count('<svg'), 3)
        self.assertIn('role="img"', html)
        self.assertNotIn('style=', html)
        self.assertNotIn('<script', html)


if __name__ == '__main__':
    unittest.main()
