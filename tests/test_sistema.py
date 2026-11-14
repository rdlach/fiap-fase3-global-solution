"""Verificações com biblioteca padrão e arquivos temporários, sem alterar dados de uso."""
import contextlib
import csv
import io
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

RAIZ = Path(__file__).resolve().parents[1]
sys.dont_write_bytecode = True
sys.path.insert(0, str(RAIZ / 'src'))
import localidades
import main as sistema
import prioridades


class TestSistema(unittest.TestCase):
    def setUp(self):
        self.temporario = tempfile.TemporaryDirectory(prefix='floodguard-teste-')
        self.addCleanup(self.temporario.cleanup)
        self.pasta = Path(self.temporario.name)
        self.csv = self.pasta / 'ocorrencias.csv'
        for nome in ['bairros_sp.csv', 'distritos_sp.csv']:
            shutil.copy2(RAIZ / 'dados' / nome, self.pasta / nome)
        caminhos = [
            (sistema, 'ARQUIVO', self.csv),
            (localidades, 'ARQUIVO_BAIRROS', self.pasta / 'bairros_sp.csv'),
            (localidades, 'ARQUIVO_DISTRITOS', self.pasta / 'distritos_sp.csv'),
            (prioridades, 'ARQUIVO_DIA', self.pasta / 'dia_simulado.txt'),
        ]
        for modulo, nome, valor in caminhos:
            alteracao = patch.object(modulo, nome, valor)
            alteracao.start()
            self.addCleanup(alteracao.stop)
        self.bairros = localidades.carregar_bairros()
        self.liberdade = localidades.buscar_bairros(self.bairros, 'Liberdade', exato=True)[0]

    def interagir(self, funcao, entradas, *argumentos):
        saida = io.StringIO()
        with patch('builtins.input', side_effect=entradas), contextlib.redirect_stdout(saida):
            retorno = funcao(*argumentos)
        return retorno, saida.getvalue()

    def registro(self, numero=1, **alteracoes):
        item = {
            'id': f'FG-{numero:03}', 'id_bairro': self.liberdade['id'],
            'bairro': 'Liberdade', 'zona': 'Centro', 'distrito': 'Liberdade',
            'categoria': 'Limpeza', 'tipo': 'Lixo acumulado',
            'descricao': 'Lixo acumulado em espaço coletivo.', 'urgencia': 'Baixa',
            'status': 'Aberta', 'dia_abertura': '1', 'solicitacoes': '1',
        }
        item.update(alteracoes)
        return item

    def gravar(self, registros, campos=None, caminho=None, bom=False):
        if campos is None:
            campos = sistema.CAMPOS
        if caminho is None:
            caminho = self.csv
        codificacao = 'utf-8-sig' if bom else 'utf-8'
        with caminho.open('w', encoding=codificacao, newline='') as arquivo:
            escritor = csv.DictWriter(arquivo, fieldnames=campos, extrasaction='ignore')
            escritor.writeheader()
            escritor.writerows(registros)

    def rota(self, bairro):
        distritos = localidades.listar_distritos(self.bairros)
        nomes = []
        for item in self.bairros:
            if item['distrito'] == bairro['distrito']:
                nomes.append(item['id'])
        return [str(distritos.index(bairro['distrito']) + 1), str(nomes.index(bairro['id']) + 1)]

    def test_catalogos_completos_e_selecao_dos_18_bairros(self):
        self.assertEqual(len(localidades.carregar_distritos()), 8)
        self.assertEqual(len(self.bairros), 18)
        for bairro in self.bairros:
            with self.subTest(bairro=bairro['bairro']):
                escolhido, _ = self.interagir(localidades.escolher_bairro, self.rota(bairro), self.bairros)
                self.assertEqual(escolhido, bairro)

    def test_busca_sem_acentos_e_fora_do_recorte(self):
        self.assertEqual(localidades.buscar_bairros(self.bairros, 'HIGIENOPOLIS')[0]['bairro'], 'Higienópolis')
        self.assertEqual(localidades.buscar_bairros(self.bairros, 'Santa Teresinha'), [])
        self.assertEqual(localidades.buscar_bairros(self.bairros, '  '), [])

    def test_catalogos_rejeitam_repeticoes_e_cobertura_incompleta(self):
        caminho = localidades.ARQUIVO_BAIRROS
        original = caminho.read_bytes()
        for registros in [self.bairros + [self.bairros[0]], self.bairros[:1]]:
            self.gravar(registros, localidades.CAMPOS_BAIRROS, caminho)
            with self.assertRaises(ValueError):
                localidades.carregar_bairros()
        caminho.write_bytes(original)
        distritos = localidades.carregar_distritos()
        self.gravar(distritos[:-1], localidades.CAMPOS_DISTRITOS, localidades.ARQUIVO_DISTRITOS)
        with self.assertRaises(ValueError):
            localidades.carregar_bairros()

    def test_catalogos_e_ocorrencias_aceitam_utf8_com_bom(self):
        distritos = localidades.carregar_distritos()
        self.gravar(distritos, localidades.CAMPOS_DISTRITOS, localidades.ARQUIVO_DISTRITOS, bom=True)
        self.gravar(self.bairros, localidades.CAMPOS_BAIRROS, localidades.ARQUIVO_BAIRROS, bom=True)
        self.assertEqual(len(localidades.carregar_bairros()), 18)
        self.gravar([self.registro()], bom=True)
        self.assertEqual(len(sistema.carregar(self.bairros)), 1)

    def test_csv_ausente_e_csv_vazio_valido(self):
        self.assertEqual(sistema.carregar(self.bairros), [])
        self.gravar([])
        self.assertEqual(sistema.carregar(self.bairros), [])

    def test_csv_preserva_acentos_virgulas_aspas_e_quebras(self):
        registro = self.registro(descricao='Descrição com vírgula, aspas "Ipê" e\nsegunda linha.')
        sistema.salvar([registro])
        self.assertEqual(sistema.carregar(self.bairros), [registro])

    def test_csv_incompleto_e_cabecalho_errado_sao_preservados(self):
        for conteudo in ['id,bairro\nFG-001,Liberdade\n', ','.join(sistema.CAMPOS) + '\nFG-001\n']:
            self.csv.write_text(conteudo, encoding='utf-8')
            antes = self.csv.read_bytes()
            with self.assertRaises(ValueError):
                sistema.carregar(self.bairros)
            self.assertEqual(self.csv.read_bytes(), antes)

    def test_ids_invalidos_e_repetidos_sao_rejeitados(self):
        for codigo in ['FG-000', 'FG-1', 'FG-0001', 'FG-²', 'XYZ-001']:
            with self.subTest(codigo=codigo):
                self.gravar([self.registro(id=codigo)])
                with self.assertRaises(ValueError):
                    sistema.carregar(self.bairros)
        self.gravar([self.registro(), self.registro()])
        with self.assertRaises(ValueError):
            sistema.carregar(self.bairros)

    def test_contador_data_tipo_e_local_inconsistentes(self):
        alteracoes = [
            {'solicitacoes': '0'}, {'solicitacoes': '-1'}, {'solicitacoes': '1.5'},
            {'dia_abertura': '0'}, {'dia_abertura': '2'}, {'tipo': 'Poste apagado'},
            {'zona': 'Norte'}, {'id_bairro': 'NAO-EXISTE'}, {'urgencia': 'Crítico'},
        ]
        for campos in alteracoes:
            with self.subTest(campos=campos):
                self.gravar([self.registro(**campos)])
                antes = self.csv.read_bytes()
                with self.assertRaises(ValueError):
                    sistema.carregar(self.bairros)
                self.assertEqual(self.csv.read_bytes(), antes)

    def test_quatro_formatos_anteriores_preservam_dados(self):
        formatos = [sistema.CAMPOS_ANTIGOS, sistema.CAMPOS_SEM_TIPO, sistema.CAMPOS_SEM_DIA, sistema.CAMPOS_SEM_SOLICITACOES]
        for campos in formatos:
            with self.subTest(campos=campos):
                self.gravar([self.registro(dia_abertura='4')], campos)
                antes = self.csv.read_bytes()
                registros = sistema.carregar(self.bairros, 7)
                self.assertEqual(registros[0]['solicitacoes'], '1')
                esperado = '4' if campos == sistema.CAMPOS_SEM_SOLICITACOES else '1'
                self.assertEqual(registros[0]['dia_abertura'], esperado)
                self.assertEqual(self.csv.read_bytes(), antes)
                sistema.salvar(registros)
                self.assertEqual(sistema.carregar(self.bairros, 7), registros)

    def test_base_de_exemplo_tem_12_registros_e_quatro_categorias(self):
        shutil.copy2(RAIZ / 'dados' / 'ocorrencias_exemplo.csv', self.csv)
        registros = sistema.carregar(self.bairros, 1)
        self.assertEqual(len(registros), 12)
        for categoria in sistema.CATEGORIAS:
            self.assertTrue(any(item['categoria'] == categoria for item in registros))
        for status in sistema.STATUS:
            self.assertTrue(any(item['status'] == status for item in registros))

    def test_todos_os_24_presets_cadastram_e_recarregam(self):
        for c, categoria in enumerate(sistema.CATEGORIAS, 1):
            for t, tipo in enumerate(sistema.TIPOS_PROBLEMA[categoria][:-1], 1):
                with self.subTest(tipo=tipo):
                    registros = []
                    entradas = self.rota(self.liberdade) + [str(c), str(t), '', '1']
                    self.interagir(sistema.cadastrar, entradas, registros, self.bairros, 4)
                    self.assertEqual(registros[0]['descricao'], sistema.DESCRICOES[tipo])
                    self.assertEqual(registros[0]['urgencia'], prioridades.URGENCIAS_INICIAIS[tipo])
                    self.assertEqual(sistema.carregar(self.bairros, 4), registros)

    def test_outro_exige_descricao_e_cancelamento_nao_grava(self):
        registros = []
        self.interagir(sistema.cadastrar, self.rota(self.liberdade) + ['3', '7', '', 'Descrição válida', '6'], registros, self.bairros, 1)
        self.assertEqual(registros, [])
        self.assertFalse(self.csv.exists())

    def test_revisao_corrige_categoria_e_tipo(self):
        registros = []
        entradas = self.rota(self.liberdade) + ['3', '1', '', '4', '2', '2', '', '1']
        self.interagir(sistema.cadastrar, entradas, registros, self.bairros, 1)
        self.assertEqual(registros[0]['tipo'], 'Calçada sem passagem')
        self.assertEqual(registros[0]['urgencia'], 'Alta')

    def test_voltar_da_revisao_preserva_complemento(self):
        registros = []
        entradas = self.rota(self.liberdade) + ['3', '1', 'Ao lado da praça', '0', '', '1']
        self.interagir(sistema.cadastrar, entradas, registros, self.bairros, 1)
        self.assertIn('Ao lado da praça', registros[0]['descricao'])

    def test_numero_sequencial_apos_reinicio(self):
        registros = [self.registro(9)]
        sistema.salvar(registros)
        registros = sistema.carregar(self.bairros)
        self.interagir(sistema.cadastrar, self.rota(self.liberdade) + ['3', '1', '', '1'], registros, self.bairros, 1)
        self.assertEqual(registros[-1]['id'], 'FG-010')

    def test_entradas_invalidas_continuam_permitindo_voltar(self):
        retorno, _ = self.interagir(sistema.escolher, ['²', 'x', '0'], 'Teste', ['Uma'])
        self.assertIsNone(retorno)
        retorno, _ = self.interagir(sistema.texto, ['', '0'], 'Texto: ')
        self.assertIsNone(retorno)
        retorno, _ = self.interagir(localidades.escolher_bairro, ['5', '0', '0'], self.bairros)
        self.assertIsNone(retorno)

    def test_todos_os_filtros_e_seus_retornos(self):
        registros = [self.registro()]
        for entradas in [['1'], ['2', '5'], ['3'] + self.rota(self.liberdade), ['4', '3'], ['5', '1']]:
            _, saida = self.interagir(sistema.consultar, entradas, registros, self.bairros, 1)
            self.assertIn('FG-001', saida)
        for opcao in ['2', '3', '4', '5']:
            _, saida = self.interagir(sistema.consultar, [opcao, '0', '0'], registros, self.bairros, 1)
            self.assertEqual(saida.count('Como você quer consultar?'), 2)

    def test_reforco_acumula_no_mesmo_id_e_persiste(self):
        registros = [self.registro()]
        sistema.salvar(registros)
        for total in [2, 3, 4]:
            self.interagir(sistema.reforcar, ['fg-001', 's'], registros, 1)
            self.assertEqual(registros[0]['solicitacoes'], str(total))
            self.assertEqual(len(registros), 1)
            self.assertEqual(sistema.carregar(self.bairros), registros)

    def test_reforco_cancelado_fechado_ou_inexistente_nao_altera(self):
        registros = [self.registro(), self.registro(2, status='Concluída')]
        sistema.salvar(registros)
        antes = self.csv.read_bytes()
        for entradas in [['0'], ['FG-001', 'n'], ['FG-001', '0', '0'], ['FG-002', '0'], ['FG-999', '0']]:
            self.interagir(sistema.reforcar, entradas, registros, 1)
        self.assertEqual(self.csv.read_bytes(), antes)

    def test_falha_de_gravacao_preserva_memoria_e_csv(self):
        registros = [self.registro()]
        sistema.salvar(registros)
        antes = self.csv.read_bytes()
        with patch.object(sistema, 'salvar', side_effect=OSError('Falha simulada')):
            with self.assertRaises(OSError):
                self.interagir(sistema.reforcar, ['FG-001', 's'], registros, 1)
        self.assertEqual(registros[0]['solicitacoes'], '1')
        self.assertEqual(self.csv.read_bytes(), antes)

    def test_pontuacao_faixas_sem_teto_e_exemplos_aprovados(self):
        for pontos, nivel in [(0, 'Baixa'), (2, 'Baixa'), (3, 'Média'), (5, 'Média'), (6, 'Alta'), (8, 'Alta'), (9, 'Crítico'), (100000, 'Crítico')]:
            calculo = prioridades.calcular_prioridade(self.registro(solicitacoes=str(pontos + 1)), 1)
            self.assertEqual((calculo['pontos'], calculo['nivel']), (pontos, nivel))
        self.assertEqual(prioridades.calcular_prioridade(self.registro(solicitacoes='4'), 4)['pontos'], 6)
        self.assertEqual(prioridades.calcular_prioridade(self.registro(), 8)['pontos'], 7)

    def test_cada_dia_sobe_e_concluida_sai_da_fila(self):
        registro = self.registro()
        for dia in range(1, 30):
            self.assertEqual(prioridades.calcular_prioridade(registro, dia)['pontos'], dia - 1)
        self.assertIsNone(prioridades.calcular_prioridade(self.registro(status='Concluída'), 30))

    def test_problemas_independentes_nao_somam_solicitacoes(self):
        registros = [self.registro(solicitacoes='5'), self.registro(2)]
        antes = prioridades.calcular_prioridade(registros[0], 4)['pontos']
        self.interagir(sistema.atualizar, ['FG-002', '3', 's'], registros, 4)
        self.assertEqual(prioridades.calcular_prioridade(registros[0], 4)['pontos'], antes)

    def test_comunidade_nao_mostra_pontos_ou_formula(self):
        registros = [self.registro(solicitacoes='50')]
        _, saida = self.interagir(sistema.menu_comunidade, ['2', '1', '', '0'], registros, self.bairros, 10)
        self.assertIn('Prioridade atual: Crítico', saida)
        for proibido in ['Pontuação:', 'Base:', 'Solicitações adicionais:', 'Baixa = 0']:
            self.assertNotIn(proibido, saida)

    def test_equipe_ordena_criticos_por_pontos_e_desempata(self):
        registros = [self.registro(1, solicitacoes='13'), self.registro(2, solicitacoes='31'), self.registro(3, solicitacoes='31', dia_abertura='2'), self.registro(4, status='Concluída')]
        _, saida = self.interagir(sistema.listar_prioridades, [], registros, 3)
        self.assertLess(saida.index('FG-002'), saida.index('FG-003'))
        self.assertLess(saida.index('FG-003'), saida.index('FG-001'))
        self.assertNotIn('FG-004', saida)
        _, empate = self.interagir(sistema.listar_prioridades, [], [self.registro(2), self.registro(1)], 1)
        self.assertLess(empate.index('FG-001'), empate.index('FG-002'))

    def test_status_pode_voltar_na_confirmacao(self):
        registros = [self.registro()]
        self.interagir(sistema.atualizar, ['FG-001', '2', '0', '3', 's'], registros, 1)
        self.assertEqual(registros[0]['status'], 'Concluída')
        self.assertEqual(sistema.carregar(self.bairros), registros)

    def test_base_invalida_preservada(self):
        shutil.copy2(RAIZ / 'dados' / 'ocorrencia_invalida.csv', self.csv)
        original = self.csv.read_bytes()
        with self.assertRaisesRegex(ValueError, 'descricao'):
            sistema.carregar(self.bairros)
        self.assertEqual(self.csv.read_bytes(), original)

    def test_consulta_por_codigo(self):
        registros = [self.registro(), self.registro(2)]
        _, saida = self.interagir(sistema.consultar, ['6', 'fg-002'], registros, self.bairros, 1)
        self.assertIn('FG-002', saida)
        self.assertNotIn('FG-001', saida)
        _, saida = self.interagir(sistema.consultar, ['6', 'FG-099'], registros, self.bairros, 1)
        self.assertIn('Não encontrei esse código.', saida)

    def test_historico_persiste_e_pilha_mostra_o_mais_recente(self):
        registros = [self.registro(), self.registro(2)]
        self.interagir(sistema.atualizar, ['FG-002', '2', 's'], registros, 2)
        self.interagir(sistema.atualizar, ['FG-001', '3', 's'], registros, 2)
        self.interagir(sistema.atualizar, ['FG-001', '3', 's'], registros, 2)
        self.interagir(sistema.atualizar, ['FG-002', '3', 'n'], registros, 2)
        carregados = sistema.carregar(self.bairros, 2)
        self.assertEqual(carregados, registros)
        eventos = sistema.relatorios.eventos(carregados)
        self.assertEqual([e['id'] for e in eventos], ['FG-002', 'FG-001'])
        self.assertEqual(eventos[-1]['depois'], 'Concluída')
        _, pilha = self.interagir(sistema.relatorios.mostrar_historico, [], carregados, True)
        self.assertLess(pilha.index('FG-001'), pilha.index('FG-002'))

    def test_fifo_independe_da_pontuacao_e_omite_concluidas(self):
        registros = [self.registro(3, solicitacoes='40'), self.registro(1),
                     self.registro(2, status='Concluída'), self.registro(4, status='Em análise')]
        codigos = []
        sistema.relatorios.fila_fifo(registros, lambda item: codigos.append(item['id']))
        self.assertEqual(codigos, ['FG-001', 'FG-003'])

    def test_dia_simulado_persiste_e_cancelamento_preserva(self):
        self.assertEqual(prioridades.carregar_dia(), 1)
        novo, _ = self.interagir(sistema.avancar_dia, ['3', 's'], 1)
        self.assertEqual(novo, 4)
        self.assertEqual(prioridades.carregar_dia(), 4)
        antes = prioridades.ARQUIVO_DIA.read_bytes()
        self.interagir(sistema.avancar_dia, ['-1', '²', '366', '3', 'n'], 4)
        self.assertEqual(prioridades.ARQUIVO_DIA.read_bytes(), antes)

    def test_dia_invalido_e_falha_ao_salvar_relogio(self):
        prioridades.ARQUIVO_DIA.write_text('inválido', encoding='utf-8')
        with self.assertRaises(ValueError):
            prioridades.carregar_dia()
        prioridades.salvar_dia(1)
        antes = prioridades.ARQUIVO_DIA.read_bytes()
        with patch.object(sistema, 'salvar_dia', side_effect=OSError('Falha simulada')):
            with self.assertRaises(OSError):
                self.interagir(sistema.avancar_dia, ['3', 's'], 1)
        self.assertEqual(prioridades.ARQUIVO_DIA.read_bytes(), antes)

    def test_programa_trata_csv_invalido_sem_traceback(self):
        self.csv.write_text('id,bairro\nFG-001,Liberdade\n', encoding='utf-8')
        _, saida = self.interagir(sistema.main, [])
        self.assertIn('Não foi possível abrir os dados', saida)
        self.assertNotIn('Traceback', saida)

    def test_fluxo_real_em_copia_limpa_e_reinicio(self):
        pasta = self.pasta / 'programa'
        shutil.copytree(RAIZ / 'src', pasta / 'src', ignore=shutil.ignore_patterns('__pycache__'))
        (pasta / 'dados').mkdir()
        for nome in ['bairros_sp.csv', 'distritos_sp.csv']:
            shutil.copy2(RAIZ / 'dados' / nome, pasta / 'dados' / nome)
        entradas = ['1', '1', '5', '2', '3', '1', '', '1', '']
        for _ in range(3):
            entradas += ['3', 'FG-001', 's', '']
        entradas += ['0', '2', '3', '3', 's', '', '1', '', '0', '0']
        processo = subprocess.run([sys.executable, '-X', 'utf8', str(pasta / 'src' / 'sistema.py')], input='\n'.join(entradas) + '\n', text=True, capture_output=True, encoding='utf-8', timeout=15, cwd=self.pasta)
        self.assertEqual(processo.returncode, 0, processo.stderr)
        self.assertEqual(processo.stderr, '')
        self.assertIn('Pontuação: 6', processo.stdout)
        reinicio = subprocess.run([sys.executable, '-X', 'utf8', str(pasta / 'src' / 'sistema.py')], input='2\n1\n\n0\n0\n', text=True, capture_output=True, encoding='utf-8', timeout=15, cwd=self.pasta)
        self.assertEqual(reinicio.returncode, 0, reinicio.stderr)
        self.assertIn('Pontuação: 6', reinicio.stdout)


if __name__ == '__main__':
    unittest.main(verbosity=2)
