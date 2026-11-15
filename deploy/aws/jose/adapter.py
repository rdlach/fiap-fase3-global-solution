"""Adapta o servidor pyHTML a eventos HTTP da Lambda."""
import base64
from io import BytesIO
import json
import hashlib
import os
from pathlib import Path
from secrets import compare_digest
import sys
from urllib.parse import urlencode

import boto3
from botocore.exceptions import ClientError

sys.path.insert(0, str(Path(__file__).parent / 'src'))
import interface_html as tela
import prioridades

s3 = boto3.client('s3')
BUCKET = os.environ['STATE_BUCKET']
ORIGIN_KEY = os.environ['ORIGIN_KEY']
STATE_KEY = 'simulacao.json'
tela.TOKEN = hashlib.sha256(ORIGIN_KEY.encode()).hexdigest()
tela.MODO_PUBLICO = True
tela.CODIGO_EQUIPE = os.environ.get('CODIGO_EQUIPE') or None
tela.SEGREDO_COOKIE = hashlib.sha256(('cookie|' + ORIGIN_KEY).encode()).hexdigest()
if tela.CODIGO_EQUIPE is None:
    raise RuntimeError('CODIGO_EQUIPE não definido: a área da equipe ficaria aberta ao público.')
LIMITE_CORPO = tela.LIMITE_FORMULARIO
tela.sistema.ARQUIVO = Path('/tmp/ocorrencias.csv')
prioridades.ARQUIVO_DIA = Path('/tmp/dia_simulado.txt')
ARQUIVOS = [tela.sistema.ARQUIVO, prioridades.ARQUIVO_DIA]


def resposta(status, body='', cookies=(), **headers):
    resultado = {'statusCode': status, 'headers': {'Cache-Control': 'no-store', **headers}, 'body': body}
    if cookies:
        resultado['cookies'] = list(cookies)
    return resultado


class Requisicao(tela.InterfaceHTML):
    def __init__(self, path, body, cookie=''):
        self.path = path
        self.headers = {'Content-Length': str(len(body)), 'Cookie': cookie}
        self.rfile = BytesIO(body)

    def responder(self, html, status=200, tipo='text/html'):
        self.resultado = resposta(status, html, self.novos_cookies, **{
            'Content-Type': tipo + '; charset=utf-8',
            'Content-Security-Policy': "default-src 'none'; style-src 'self'; form-action 'self'; frame-ancestors 'none'; base-uri 'none'",
        })

    def redirecionar(self, destino, mensagem):
        self.resultado = resposta(303, '', self.novos_cookies, Location=destino + '?' + urlencode({'mensagem': mensagem}))


def carregar_estado():
    try:
        objeto = s3.get_object(Bucket=BUCKET, Key=STATE_KEY)
    except s3.exceptions.NoSuchKey:
        return {}, None
    return json.loads(objeto['Body'].read()), objeto['ETag']


def handler(evento, contexto):
    headers = evento.get('headers') or {}
    if not compare_digest(headers.get('x-floodguard-origin', ''), ORIGIN_KEY):
        return resposta(403)
    caminho = evento['rawPath']
    metodo = evento['requestContext']['http']['method']
    if metodo not in ('GET', 'HEAD', 'POST'):
        return resposta(405, Allow='GET, HEAD, POST')
    if metodo == 'POST' and headers.get('sec-fetch-site') not in (None, 'same-origin'):
        return resposta(403)
    if caminho == '/encerrar':
        return resposta(303, Location='/')
    consulta = evento.get('rawQueryString', '')
    caminho_com_consulta = caminho + ('?' + consulta if consulta else '')
    corpo = evento.get('body') or ''
    corpo = base64.b64decode(corpo) if evento.get('isBase64Encoded') else corpo.encode('utf-8')
    if len(corpo) > LIMITE_CORPO:
        return resposta(413)
    pedido = Requisicao(caminho_com_consulta, corpo, '; '.join(evento.get('cookies') or []))
    if caminho in ('/', '/style.css', '/ajuda') and metodo in ('GET', 'HEAD'):
        if caminho == '/':
            html = (tela.RAIZ / 'index.html').read_text(encoding='utf-8')
            inicio = html.index('        <details>')
            fim = html.index('    </main>', inicio)
            html = html[:inicio] + html[fim:]
            html = html.replace('Protótipo acadêmico local · Perfis simulados, sem autenticação · Dados separados da aplicação principal.', 'Demonstração acadêmica · Use apenas dados fictícios.')
            pedido.responder(html)
        elif caminho == '/ajuda':
            pedido.do_GET()
        else:
            pedido.responder((tela.RAIZ / 'style.css').read_text(encoding='utf-8'), tipo='text/css')
        if caminho in ('/style.css', '/ajuda'):
            # o css e a ajuda mudam pouco, o CloudFront guarda por 5 minutos
            pedido.resultado['headers']['Cache-Control'] = 'public, max-age=300'
    else:
        anterior, etag = carregar_estado()
        for arquivo in ARQUIVOS:
            if arquivo.name in anterior:
                arquivo.write_text(anterior[arquivo.name], encoding='utf-8')
            else:
                arquivo.unlink(missing_ok=True)
        if metodo == 'POST':
            pedido.do_POST()
        else:
            pedido.do_GET()
        if metodo == 'POST' and pedido.resultado['statusCode'] == 303:
            atual = {a.name: a.read_text(encoding='utf-8') for a in ARQUIVOS if a.exists()}
            condicao = {'IfMatch': etag} if etag else {'IfNoneMatch': '*'}
            try:
                s3.put_object(Bucket=BUCKET, Key=STATE_KEY, Body=json.dumps(atual).encode(),
                              ContentType='application/json', **condicao)
            except ClientError as erro:
                if erro.response['ResponseMetadata']['HTTPStatusCode'] in (409, 412):
                    pedido.responder(tela.pagina('A base foi atualizada',
                        '<p>Outra alteração foi salva. Volte e revise o formulário.</p>'), 409)
                else:
                    raise
    if metodo == 'HEAD':
        pedido.resultado['body'] = ''
    return pedido.resultado
