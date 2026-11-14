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


class TestInterfaceHTML(unittest.TestCase):
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

    def requisicao(self, caminho, dados=None, token=True):
        conexao = HTTPConnection('127.0.0.1', self.servidor.server_port, timeout=5)
        self.addCleanup(conexao.close)
        if dados is None:
            conexao.request('GET', caminho)
        else:
            campos = dict(dados)
            if token:
                campos['token'] = tela.TOKEN
            conexao.request('POST', caminho, urlencode(campos), {'Content-Type': 'application/x-www-form-urlencoded'})
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

    def test_menu_e_consultas_nao_gravam_dados(self):
        for caminho in ['/', '/comunidade', '/equipe', '/consulta', '/resumo', '/pendencias', '/equipe/fila', '/equipe/status', '/equipe/dias', '/encerrar']:
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
        self.assertIn('pyHTML', html)
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
        self.assertNotIn('Reforçar esta ocorrência', html)
        self.assertEqual(self.requisicao('/reforcar', {'codigo': codigo})[0], 400)
        self.assertEqual(sistema.carregar(self.bairros)[0]['solicitacoes'], '2')

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


if __name__ == '__main__':
    unittest.main()
