"""Indicadores e atalhos da versão web."""
from html import escape

AJUDA = """
<p>Em caso de risco imediato, ligue para o serviço responsável. Registros no FloodGuard são simulados.</p>
<div class="contatos">
<section><h3>Corpo de Bombeiros</h3><a class="atalho" href="tel:193">Ligar 193</a>
<a href="https://www.ssp.sp.gov.br/servicos/coordenacao-sistema-estadual-atendimento-emergencias">Página oficial</a>
<p>Também atende cobras e animais silvestres em local de circulação.</p></section>
<section><h3>Polícia Militar</h3><a class="atalho" href="tel:190">Ligar 190</a>
<a href="https://policiamilitar.sp.gov.br/">Portal oficial</a></section>
<section><h3>Defesa Civil</h3><a class="atalho" href="tel:199">Ligar 199</a>
<a href="https://prefeitura.sp.gov.br/web/defesa_civil">Portal oficial</a></section>
<section><h3>SAMU</h3><a class="atalho" href="tel:192">Ligar 192</a>
<p>Urgências médicas</p></section>
</div>
<p><a href="https://wa.me/556120344611">Receber alertas da Defesa Civil pelo WhatsApp</a>. Para atendimento imediato, ligue para um dos números acima.</p>
"""


def indicadores(registros, categorias, situacoes, dia):
    total = len(registros)
    matriz = {categoria: dict.fromkeys(situacoes, 0) for categoria in categorias}
    for item in registros:
        matriz[item['categoria']][item['status']] += 1

    def proporcao(quantidade):
        return f'{quantidade} ({quantidade * 100 / total if total else 0:.1f}%)'

    totais = {status: sum(linha[status] for linha in matriz.values()) for status in situacoes}
    html = '<div class="indicadores">'
    for rotulo, valor in [('Total', total), *totais.items()]:
        html += f'<div><strong>{valor}</strong>{escape(rotulo)}</div>'
    html += '</div><div class="tabela-rolavel"><table><caption>Ocorrências por categoria e status</caption><thead><tr>'
    for rotulo in ['Categoria', *situacoes, 'Proporção']:
        html += f'<th scope="col">{escape(rotulo)}</th>'
    html += '</tr></thead><tbody>'
    for categoria, contagens in matriz.items():
        html += f'<tr><th scope="row">{escape(categoria)}</th>'
        html += ''.join(f'<td>{valor}</td>' for valor in contagens.values())
        html += f'<td>{proporcao(sum(contagens.values()))}</td></tr>'
    html += '<tr><th scope="row">Por status</th>'
    html += ''.join(f'<td>{proporcao(totais[status])}</td>' for status in situacoes)
    html += '<td></td></tr></tbody></table></div>'
    pendentes = [item for item in registros if item['status'] != 'Concluída']
    html += f'<p>Pendências: <strong>{len(pendentes)}</strong></p>'
    if pendentes:
        media = sum(dia - int(item['dia_abertura']) for item in pendentes) / len(pendentes)
        html += f'<p>Tempo médio em aberto: <strong>{media:.1f} dia(s)</strong></p>'
    if total:
        media = sum(int(item['solicitacoes']) for item in registros) / total
        html += f'<p>Média de solicitações por ocorrência: <strong>{media:.1f}</strong></p>'
    return html


def historico(registros, recentes):
    eventos = sorted((evento for item in registros for evento in item.get('historico', [])),
                     key=lambda evento: evento['ordem'], reverse=recentes)
    if not eventos:
        return '<p>Ainda não há mudanças de status registradas.</p>'
    linhas = []
    for evento in eventos:
        linhas.append(f"<li>Dia {evento['dia']} · {escape(evento['id'])}: "
                      f"{escape(evento['antes'])} → {escape(evento['depois'])}</li>")
    return '<ol>' + ''.join(linhas) + '</ol>'


CLASSES_STATUS = ['s-aberta', 's-analise', 's-concluida']


def _svg(identificador, titulo, altura, partes):
    return (f'<figure class="grafico"><figcaption>{escape(titulo)}</figcaption>'
            f'<svg viewBox="0 0 720 {altura}" role="img" aria-labelledby="{identificador}">'
            f'<title id="{identificador}">{escape(titulo)}</title>{partes}</svg></figure>')


def barras_horizontais(identificador, titulo, linhas, series):
    """Barras empilhadas em SVG, uma linha para cada rótulo."""
    if not linhas:
        return f'<figure class="grafico"><figcaption>{escape(titulo)}</figcaption><p>Ainda não há dados.</p></figure>'
    maior = max(max(sum(valores) for _, valores in linhas), 1)
    esquerda, direita, passo, topo = 190, 56, 32, 6
    area = 720 - esquerda - direita
    partes = ''
    for indice, (rotulo, valores) in enumerate(linhas):
        y = topo + indice * passo
        partes += f'<text class="g-rotulo" x="{esquerda - 12}" y="{y + 19}" text-anchor="end">{escape(rotulo)}</text>'
        x = esquerda
        for valor, (nome, classe) in zip(valores, series):
            if valor:
                largura = area * valor / maior
                partes += (f'<rect class="{classe}" x="{x:.1f}" y="{y + 4}" width="{max(largura - 2, 2):.1f}" height="22" rx="5">'
                           f'<title>{escape(rotulo)} · {escape(nome)}: {valor}</title></rect>')
                x += largura
        partes += f'<text class="g-valor" x="{x + 8:.1f}" y="{y + 19}">{sum(valores)}</text>'
    y = topo + len(linhas) * passo + 14
    x = esquerda
    for nome, classe in series:
        partes += f'<rect class="{classe}" x="{x}" y="{y}" width="12" height="12" rx="3"/>'
        partes += f'<text class="g-legenda" x="{x + 18}" y="{y + 11}">{escape(nome)}</text>'
        x += 24 + 8 * len(nome) + 16
    return _svg(identificador, titulo, y + 28, partes)


def colunas_por_dia(identificador, titulo, contagens):
    """Colunas em SVG com os registros abertos em cada dia simulado."""
    maior = max([quantidade for _, quantidade in contagens] + [1])
    base, topo, esquerda = 150, 18, 36
    largura = (720 - esquerda - 16) / len(contagens)
    partes = f'<line class="g-eixo" x1="{esquerda}" y1="{base}" x2="704" y2="{base}"/>'
    for nivel in sorted({0, maior}):
        y = base - (base - topo) * nivel / maior
        partes += f'<text class="g-legenda" x="{esquerda - 8}" y="{y + 4:.1f}" text-anchor="end">{nivel}</text>'
    for indice, (dia, quantidade) in enumerate(contagens):
        x = esquerda + indice * largura
        altura = (base - topo) * quantidade / maior
        if quantidade:
            larg = min(max(largura - 8, 3), 56)
            partes += (f'<rect class="s-dia" x="{x + (largura - larg) / 2:.1f}" y="{base - altura:.1f}" width="{larg:.1f}" '
                       f'height="{altura:.1f}" rx="5"><title>Dia {dia}: {quantidade} registro(s)</title></rect>')
        partes += f'<text class="g-legenda" x="{x + largura / 2:.1f}" y="{base + 18}" text-anchor="middle">{dia}</text>'
    partes += f'<text class="g-legenda" x="{(720 + esquerda) / 2}" y="{base + 38}" text-anchor="middle">Dia simulado</text>'
    return _svg(identificador, titulo, base + 46, partes)


def graficos(registros, categorias, situacoes, dia):
    series = list(zip(situacoes, CLASSES_STATUS))
    por_categoria = []
    for categoria in categorias:
        por_categoria.append((categoria, [sum(1 for item in registros
                                              if item['categoria'] == categoria and item['status'] == status)
                                          for status in situacoes]))
    pendentes = {}
    for item in registros:
        if item['status'] != situacoes[-1]:
            linha = pendentes.setdefault(item['bairro'], [0] * (len(situacoes) - 1))
            linha[situacoes.index(item['status'])] += 1
    ranking = sorted(pendentes.items(), key=lambda par: (-sum(par[1]), par[0].casefold()))[:8]
    inicio = max(1, dia - 13)
    abertos = {numero: 0 for numero in range(inicio, dia + 1)}
    for item in registros:
        numero = int(item['dia_abertura'])
        if numero in abertos:
            abertos[numero] += 1
    return ('<h3>Gráficos</h3><div class="graficos">'
            + barras_horizontais('g-categorias', 'Ocorrências por categoria e status', por_categoria, series)
            + barras_horizontais('g-bairros', 'Pendências por bairro (os 8 com mais casos)', ranking, series[:-1])
            + colunas_por_dia('g-dias', 'Registros abertos por dia simulado', list(abertos.items()))
            + '</div>')
