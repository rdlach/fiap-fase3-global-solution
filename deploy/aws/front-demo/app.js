const porId = id => document.getElementById(id);
const chave = 'floodguard-demo-v1';
const inicial = {dia: 1, registros: catalogo.exemplos};
const mensagem = texto => { porId('mensagem').textContent = texto; };
let estado = inicial;
try {
  estado = JSON.parse(localStorage.getItem(chave)) ?? inicial;
} catch {
  mensagem('Não foi possível ler os registros locais. Os exemplos foram carregados.');
}
let equipe = false;

function opcoes(id, itens, vazio) {
  const select = porId(id);
  select.replaceChildren();
  if (vazio !== undefined) select.add(new Option(vazio, ''));
  for (const item of itens) {
    select.add(typeof item === 'string' ? new Option(item, item) : new Option(item.bairro, item.id));
  }
}

function salvar(novo, texto, informar = mensagem) {
  try {
    localStorage.setItem(chave, JSON.stringify(novo));
  } catch {
    informar('Não foi possível salvar neste navegador.');
    return false;
  }
  estado = novo;
  renderizar();
  mensagem(texto);
  return true;
}

function prioridade(item) {
  if (item.status === 'Concluída') return null;
  const pontos = catalogo.pontos[item.urgencia] + estado.dia - Number(item.dia_abertura)
    + Number(item.solicitacoes) - 1;
  const nivel = pontos >= 9 ? 'Crítico' : pontos >= 6 ? 'Alta' : pontos >= 3 ? 'Média' : 'Baixa';
  return {pontos, nivel};
}

function atualizarBairros(distritoId, bairroId, vazio) {
  const distrito = porId(distritoId).value;
  opcoes(bairroId, catalogo.bairros.filter(bairro => !distrito || bairro.distrito === distrito), vazio);
}

const ajudaPorCategoria = {
  Inundação: [['Risco de alagamento agora? Defesa Civil 199', '199'], ['Resgate: Bombeiros 193', '193']],
  Incêndio: [['Incêndio em andamento? Bombeiros 193', '193']],
  Acidentes: [['Urgência médica: SAMU 192', '192'], ['Resgate: Bombeiros 193', '193']],
};

function atualizarTipo() {
  const categoria = porId('categoria').value;
  opcoes('tipo', catalogo.tipos[categoria]);
  const orientacao = porId('orientacao');
  const contatos = ajudaPorCategoria[categoria] ?? [];
  orientacao.replaceChildren();
  orientacao.hidden = !contatos.length;
  for (const [texto, numero] of contatos) {
    linha(orientacao, 'a', texto).href = 'tel:' + numero;
  }
  atualizarDescricao();
}

function atualizarDescricao() {
  const tipo = porId('tipo').value;
  porId('descricao').value = catalogo.descricoes[tipo] ?? '';
  const urgencia = catalogo.urgencias[tipo] ?? 'Média';
  porId('previa').textContent = 'Prioridade inicial: ' + urgencia;
}

function alterar(item, campos, texto) {
  salvar({...estado, registros: estado.registros.map(atual => atual.id === item.id ? {...atual, ...campos} : atual)}, texto);
}

function linha(pai, tag, texto) {
  const elemento = document.createElement(tag);
  elemento.textContent = texto;
  pai.append(elemento);
  return elemento;
}

function cartao(item) {
  const li = document.createElement('li');
  const p = prioridade(item);
  li.className = 'ocorrencia';
  const cabecalho = linha(li, 'div', '');
  cabecalho.className = 'cabecalho-card';
  linha(cabecalho, 'h3', item.bairro);
  const status = linha(cabecalho, 'span', item.status);
  status.className = 'etiqueta ' + normalizar(item.status).replaceAll(' ', '-');
  linha(li, 'p', [item.id, item.distrito, item.categoria, item.tipo].join(' · ')).className = 'meta';
  linha(li, 'p', item.descricao);
  linha(li, 'p', item.solicitacoes + ' solicitação(ões)' + (p ? ' · Prioridade ' + p.nivel + ' (' + p.pontos + ' pontos)' : '')).className = 'meta';
  if (equipe || p) {
    const acoes = linha(li, 'div', '');
    acoes.className = 'acoes';
    if (equipe) {
      const select = document.createElement('select');
      select.setAttribute('aria-label', 'Status de ' + item.id);
      for (const status of catalogo.status) select.add(new Option(status, status));
      select.value = item.status;
      acoes.append(select);
      const botao = linha(acoes, 'button', 'Salvar status');
      botao.disabled = true;
      select.onchange = () => { botao.disabled = select.value === item.status; };
      botao.onclick = () => alterar(item, {status: select.value}, 'Status de ' + item.id + ' atualizado.');
    } else {
      linha(acoes, 'button', 'Reforçar ocorrência').onclick = () => {
        if (confirm('É o mesmo problema registrado em ' + item.id + '?')) {
          alterar(item, {solicitacoes: String(Number(item.solicitacoes) + 1)}, 'Sua solicitação foi vinculada a ' + item.id + '.');
        }
      };
    }
  }
  return li;
}

function normalizar(texto) {
  return texto.toLowerCase().normalize('NFD').replace(/\p{Diacritic}/gu, '');
}

function renderizar() {
  porId('cadastro').hidden = equipe;
  porId('avancar').hidden = !equipe;
  porId('dia-atual').textContent = estado.dia;
  porId('chamada').textContent = equipe ? 'Organize o atendimento.' : 'Cuide do seu bairro.';
  porId('subtitulo').textContent = equipe ? 'Acompanhe as prioridades e atualize cada ocorrência.' : 'Conte o que aconteceu e acompanhe as ocorrências da comunidade.';
  porId('comunidade').setAttribute('aria-pressed', String(!equipe));
  porId('equipe').setAttribute('aria-pressed', String(equipe));
  porId('titulo').textContent = equipe ? 'Fila de atendimento · Dia ' + estado.dia : 'Consultar ocorrências';
  const filtros = {'f-distrito': 'distrito', 'f-bairro': 'id_bairro', 'f-categoria': 'categoria', 'f-status': 'status'};
  const busca = normalizar(porId('busca').value.trim());
  const encontrados = estado.registros.filter(item =>
    Object.entries(filtros).every(([id, campo]) => !porId(id).value || porId(id).value === item[campo])
    && normalizar([item.id, item.bairro, item.descricao, item.tipo].join(' ')).includes(busca));
  if (equipe) {
    encontrados.sort((a, b) => (prioridade(b)?.pontos ?? -1) - (prioridade(a)?.pontos ?? -1)
      || a.dia_abertura - b.dia_abertura || a.id.slice(3) - b.id.slice(3));
  } else {
    encontrados.reverse();
  }
  porId('registros').replaceChildren(...encontrados.map(cartao));
  porId('total').textContent = encontrados.length ? encontrados.length + ' ocorrência(s)' : 'Nenhuma ocorrência encontrada.';
  porId('limpar').hidden = !busca && Object.keys(filtros).every(id => !porId(id).value);
  const contagem = new Map();
  for (const item of estado.registros) {
    if (item.status === 'Concluída') continue;
    const grupo = contagem.get(item.id_bairro) ?? {bairro: item.bairro, quantidade: 0};
    grupo.quantidade++;
    contagem.set(item.id_bairro, grupo);
  }
  const resumo = porId('resumo');
  resumo.replaceChildren();
  for (const [rotulo, total] of [['Total', estado.registros.length], ...catalogo.status.map(status =>
    [status, estado.registros.filter(item => item.status === status).length])]) {
    const quadro = linha(resumo, 'div', '');
    quadro.className = 'indicador';
    linha(quadro, 'strong', total);
    linha(quadro, 'span', rotulo);
  }
  const ranking = porId('ranking');
  ranking.replaceChildren();
  for (const [id, grupo] of [...contagem].sort((a, b) =>
    b[1].quantidade - a[1].quantidade || a[1].bairro.localeCompare(b[1].bairro, 'pt-BR'))) {
    const botao = linha(linha(ranking, 'li', ''), 'button', '');
    linha(botao, 'span', grupo.bairro);
    linha(botao, 'strong', grupo.quantidade);
    botao.onclick = () => {
      limparFiltros();
      porId('f-bairro').value = id;
      renderizar();
      porId('busca').focus();
    };
  }
  if (!contagem.size) linha(ranking, 'li', 'Nenhuma pendência registrada.');
}

const distritos = [...new Set(catalogo.bairros.map(bairro => bairro.distrito))].sort();
opcoes('distrito', distritos, 'Todos os distritos');
opcoes('f-distrito', distritos, 'Todos');
opcoes('categoria', Object.keys(catalogo.tipos));
opcoes('f-categoria', Object.keys(catalogo.tipos), 'Todas');
opcoes('f-status', catalogo.status, 'Todos');
atualizarBairros('distrito', 'local', 'Escolha o bairro');
atualizarBairros('f-distrito', 'f-bairro', 'Todos');
atualizarTipo();
porId('distrito').onchange = () => atualizarBairros('distrito', 'local', 'Escolha o bairro');
porId('categoria').onchange = atualizarTipo;
porId('tipo').onchange = atualizarDescricao;
porId('f-distrito').onchange = () => { atualizarBairros('f-distrito', 'f-bairro', 'Todos'); renderizar(); };
for (const id of ['f-bairro', 'f-categoria', 'f-status', 'busca']) porId(id).oninput = renderizar;
porId('comunidade').onclick = () => { equipe = false; renderizar(); };
porId('equipe').onclick = () => { equipe = true; renderizar(); };
function limparFiltros() {
  for (const id of ['busca', 'f-distrito', 'f-categoria', 'f-status']) porId(id).value = '';
  atualizarBairros('f-distrito', 'f-bairro', 'Todos');
}
porId('limpar').onclick = () => { limparFiltros(); renderizar(); porId('busca').focus(); };

const dialogo = porId('dialogo');
const etapas = ['localizacao', 'problema', 'revisao'];
let etapa = 0;
const informarCadastro = texto => { porId('mensagem-cadastro').textContent = texto; };

function mostrarEtapa(indice) {
  etapa = indice;
  informarCadastro('');
  etapas.forEach((id, posicao) => {
    const secao = porId(id);
    secao.hidden = posicao !== etapa;
    for (const campo of secao.querySelectorAll('select, textarea')) campo.disabled = secao.hidden;
  });
  porId('progresso').textContent = 'Etapa ' + (etapa + 1) + ' de ' + etapas.length;
  porId('voltar').hidden = etapa === 0;
  porId('continuar').textContent = etapa === 2 ? 'Salvar ocorrência' : 'Continuar';
  if (dialogo.open) (porId(etapas[etapa]).querySelector('select') ?? porId('continuar')).focus();
}

function dadosCadastro() {
  const bairro = catalogo.bairros.find(local => local.id === porId('local').value);
  const tipo = porId('tipo').value;
  return {id_bairro: bairro.id, bairro: bairro.bairro, distrito: bairro.distrito, zona: bairro.zona,
    categoria: porId('categoria').value, tipo, descricao: porId('descricao').value.trim(),
    urgencia: catalogo.urgencias[tipo] ?? 'Média', status: 'Aberta',
    dia_abertura: String(estado.dia), solicitacoes: '1'};
}

porId('cadastro').onclick = () => {
  mostrarEtapa(0);
  dialogo.showModal();
};
porId('fechar').onclick = () => dialogo.close();
porId('voltar').onclick = () => mostrarEtapa(etapa - 1);

porId('novo').onsubmit = evento => {
  evento.preventDefault();
  if (etapa === 0) {
    mostrarEtapa(1);
    return;
  }
  const item = dadosCadastro();
  if (!item.descricao) {
    informarCadastro('Descreva o problema antes de continuar.');
    porId('descricao').focus();
    return;
  }
  if (etapa === 1) {
    const detalhes = porId('detalhes');
    detalhes.replaceChildren();
    for (const [nome, valor] of [
      ['Local', item.bairro + ' · ' + item.distrito],
      ['Problema', item.categoria + ' · ' + item.tipo],
      ['Descrição', item.descricao],
      ['Prioridade inicial', item.urgencia],
    ]) {
      linha(detalhes, 'dt', nome);
      linha(detalhes, 'dd', valor);
    }
    mostrarEtapa(2);
    return;
  }
  const numero = estado.registros.reduce((maior, registro) => Math.max(maior, Number(registro.id.slice(3))), 0) + 1;
  const id = 'FG-' + String(numero).padStart(3, '0');
  if (salvar({...estado, registros: [...estado.registros, {...item, id}]},
    'Pronto. O registro ' + id + ' foi salvo neste navegador.', informarCadastro)) {
    limparFiltros();
    renderizar();
    dialogo.close();
    porId('local').value = '';
    atualizarDescricao();
  }
};
porId('avancar').onsubmit = evento => {
  evento.preventDefault();
  const dias = Number(porId('dias').value);
  if (!Number.isInteger(dias) || dias < 1 || dias > 365) return;
  const dia = estado.dia + dias;
  if (confirm('Avançar a simulação para o dia ' + dia + '?')) {
    salvar({...estado, dia}, 'Dia ' + dia + '. As prioridades foram recalculadas.');
  }
};
renderizar();
