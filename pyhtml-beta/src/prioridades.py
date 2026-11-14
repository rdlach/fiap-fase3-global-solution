"""Regras simples de prioridade e passagem de dias em uma simulação acadêmica."""
from pathlib import Path

ARQUIVO_DIA = Path(__file__).resolve().parents[1] / 'dados' / 'dia_simulado.txt'
PONTOS_INICIAIS = {'Baixa': 0, 'Média': 3, 'Alta': 6}
URGENCIAS_INICIAIS = {
    'Poste apagado': 'Média',
    'Luz piscando': 'Baixa',
    'Iluminação danificada': 'Média',
    'Rampa obstruída': 'Alta',
    'Calçada sem passagem': 'Alta',
    'Piso tátil danificado': 'Média',
    'Lixo acumulado': 'Baixa',
    'Descarte de entulho': 'Média',
    'Bueiro com lixo': 'Média',
    'Buraco na rua': 'Média',
    'Banco danificado': 'Baixa',
    'Brinquedo de praça quebrado': 'Alta',
    'Poste danificado': 'Alta',
    'Fiação elétrica exposta': 'Alta',
    'Iluminação bloqueada por vegetação': 'Média',
    'Escadaria sem corrimão': 'Média',
    'Travessia sem acesso rebaixado': 'Alta',
    'Banheiro público sem acessibilidade': 'Média',
    'Esgoto a céu aberto': 'Alta',
    'Animal morto em espaço público': 'Média',
    'Banheiro público sem limpeza': 'Média',
    'Vazamento de água': 'Média',
    'Árvore caída em espaço público': 'Alta',
    'Sinalização de trânsito danificada': 'Média',
}


def carregar_dia():
    if not ARQUIVO_DIA.exists():
        return 1
    valor = ARQUIVO_DIA.read_text(encoding='utf-8-sig').strip()
    if not valor.isdecimal() or len(valor) > 10 or int(valor) < 1:
        raise ValueError('O dia simulado deve ser um número inteiro positivo.')
    return int(valor)


def salvar_dia(dia):
    ARQUIVO_DIA.parent.mkdir(parents=True, exist_ok=True)
    temporario = ARQUIVO_DIA.with_suffix('.txt.tmp')
    temporario.write_text(str(dia) + '\n', encoding='utf-8')
    temporario.replace(ARQUIVO_DIA)


def calcular_prioridade(item, dia_atual):
    if item['status'] == 'Concluída':
        return None
    dias = dia_atual - int(item['dia_abertura'])
    adicionais = int(item['solicitacoes']) - 1
    pontos_iniciais = PONTOS_INICIAIS[item['urgencia']]
    pontos = pontos_iniciais + dias + adicionais
    if pontos >= 9:
        nivel = 'Crítico'
    elif pontos >= 6:
        nivel = 'Alta'
    elif pontos >= 3:
        nivel = 'Média'
    else:
        nivel = 'Baixa'
    return {
        'nivel': nivel,
        'pontos': pontos,
        'pontos_iniciais': pontos_iniciais,
        'dias': dias,
        'adicionais': adicionais,
        'solicitacoes': int(item['solicitacoes']),
    }
