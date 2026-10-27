const CHAVE_ARMAZENAMENTO = 'redeSocial.grafo';
const RAIO_NO = 16;

class Grafo {
  constructor() {
    this.nos = [];
    this.arestas = [];
  }

  temNo(id) {
    return this.nos.some(n => n.id === id);
  }

  adicionarNo(id, x = null, y = null) {
    if (this.temNo(id)) throw new Error(`Perfil duplicado: ${id}`);
    this.nos.push({ id, x, y });
  }

  removerNo(id) {
    this.nos = this.nos.filter(n => n.id !== id);
    this.arestas = this.arestas.filter(e => e.origem !== id && e.destino !== id);
  }

  obterAresta(origem, destino) {
    return this.arestas.find(e => e.origem === origem && e.destino === destino) || null;
  }

  adicionarAresta(origem, destino, afinidade, interacoes = 0) {
    if (!this.temNo(origem) || !this.temNo(destino)) throw new Error(`Perfil inexistente na conexão ${origem} → ${destino}`);
    if (origem === destino) throw new Error(`Conexão para si mesmo: ${origem}`);
    if (!(afinidade > 0) || !isFinite(afinidade)) throw new Error(`Afinidade inválida em ${origem} → ${destino}`);
    if (this.obterAresta(origem, destino)) throw new Error(`Conexão duplicada: ${origem} → ${destino}`);
    this.arestas.push({ origem, destino, afinidade, interacoes, ativa: true });
  }

  definirAtiva(origem, destino, ativa) {
    const aresta = this.obterAresta(origem, destino);
    if (aresta) aresta.ativa = ativa;
  }

  desativarAresta(origem, destino) {
    this.definirAtiva(origem, destino, false);
  }

  reativarAresta(origem, destino) {
    this.definirAtiva(origem, destino, true);
  }

  reativarTodas() {
    this.arestas.forEach(e => { e.ativa = true; });
  }

  get arestasAtivas() {
    return this.arestas.filter(e => e.ativa);
  }

  get arestasDesativadas() {
    return this.arestas.filter(e => !e.ativa);
  }

  saidas(id) {
    return this.arestasAtivas.filter(e => e.origem === id);
  }

  entradas(id) {
    return this.arestasAtivas.filter(e => e.destino === id);
  }

  grau(id) {
    return this.saidas(id).length + this.entradas(id).length;
  }

  comTodasAtivas(funcao) {
    const estados = this.arestas.map(e => e.ativa);
    this.arestas.forEach(e => { e.ativa = true; });
    try {
      return funcao();
    } finally {
      this.arestas.forEach((e, i) => { e.ativa = estados[i]; });
    }
  }

  distribuirEmCirculo() {
    const total = this.nos.length;
    this.nos.forEach((no, i) => {
      const angulo = (2 * Math.PI * i) / total - Math.PI / 2;
      no.x = 225 + 170 * Math.cos(angulo);
      no.y = 225 + 170 * Math.sin(angulo);
    });
  }

  serializar() {
    return {
      nos: this.nos.map(n => ({ id: n.id, x: n.x, y: n.y })),
      arestas: this.arestas.map(e => ({ ...e }))
    };
  }

  static desserializar(dados) {
    const grafo = new Grafo();
    dados.nos.forEach(n => grafo.adicionarNo(n.id, n.x, n.y));
    dados.arestas.forEach(e => {
      grafo.adicionarAresta(e.origem, e.destino, e.afinidade, e.interacoes);
      grafo.definirAtiva(e.origem, e.destino, e.ativa !== false);
    });
    return grafo;
  }
}

function criarGrafoPadrao() {
  const grafo = new Grafo();
  [
    ['Ana', 250, 180], ['Bruno', 340, 250], ['Carla', 260, 310], ['Daniel', 220, 380],
    ['Eduardo', 120, 280], ['Fernanda', 140, 350], ['Gustavo', 160, 190], ['Helena', 180, 100],
    ['Igor', 300, 90], ['Julia', 340, 160]
  ].forEach(([id, x, y]) => grafo.adicionarNo(id, x, y));

  [
    ['Carla', 'Fernanda', 4], ['Julia', 'Bruno', 2], ['Helena', 'Igor', 3], ['Bruno', 'Daniel', 3],
    ['Bruno', 'Carla', 4], ['Gustavo', 'Julia', 4], ['Ana', 'Bruno', 3], ['Bruno', 'Ana', 5],
    ['Carla', 'Ana', 8], ['Daniel', 'Carla', 3], ['Eduardo', 'Fernanda', 2], ['Eduardo', 'Gustavo', 5],
    ['Fernanda', 'Eduardo', 2], ['Gustavo', 'Ana', 4], ['Gustavo', 'Helena', 3], ['Helena', 'Gustavo', 3],
    ['Igor', 'Julia', 6], ['Julia', 'Ana', 2], ['Julia', 'Helena', 1]
  ].forEach(([origem, destino, afinidade]) => grafo.adicionarAresta(origem, destino, afinidade, afinidade * 20));

  return grafo;
}

function carregarGrafo() {
  try {
    const salvo = localStorage.getItem(CHAVE_ARMAZENAMENTO);
    if (salvo) return Grafo.desserializar(JSON.parse(salvo));
  } catch (e) {
    // dados salvos inválidos ou armazenamento indisponível: usa a rede padrão
  }
  return criarGrafoPadrao();
}

function salvarGrafo() {
  try {
    localStorage.setItem(CHAVE_ARMAZENAMENTO, JSON.stringify(grafo.serializar()));
  } catch (e) {
    // armazenamento indisponível: o estado vale apenas para esta página
  }
}

function substituirGrafo(novoGrafo) {
  grafo = novoGrafo;
  salvarGrafo();
}

let grafo = carregarGrafo();

function escapar(texto) {
  return String(texto).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
}

function formatarNumero(valor, casas = 2) {
  return Number.isInteger(valor) ? String(valor) : valor.toFixed(casas);
}

function ajustarAoCanvas(nos, largura, altura) {
  const margem = 50;
  const xs = nos.map(n => n.x);
  const ys = nos.map(n => n.y);
  const minX = Math.min(...xs), maxX = Math.max(...xs);
  const minY = Math.min(...ys), maxY = Math.max(...ys);
  const larguraGrafo = Math.max(maxX - minX, 1);
  const alturaGrafo = Math.max(maxY - minY, 1);
  const escala = Math.min((largura - 2 * margem) / larguraGrafo, (altura - 2 * margem) / alturaGrafo, 2.5);
  const deslocX = (largura - larguraGrafo * escala) / 2 - minX * escala;
  const deslocY = (altura - alturaGrafo * escala) / 2 - minY * escala;
  return (no) => ({ x: no.x * escala + deslocX, y: no.y * escala + deslocY });
}

function posicionarVizinhanca(foco) {
  const vizinhos = new Set();
  grafo.arestas.forEach(e => {
    if (e.origem === foco) vizinhos.add(e.destino);
    if (e.destino === foco) vizinhos.add(e.origem);
  });
  const lista = [...vizinhos];
  const nos = [{ id: foco, x: 225, y: 225 }];
  lista.forEach((id, i) => {
    const angulo = (2 * Math.PI * i) / lista.length - Math.PI / 2;
    nos.push({ id, x: 225 + 140 * Math.cos(angulo), y: 225 + 140 * Math.sin(angulo) });
  });
  return nos;
}

function desenharSeta(ctx, x, y, angulo, tamanho) {
  ctx.beginPath();
  ctx.moveTo(x, y);
  ctx.lineTo(x - tamanho * Math.cos(angulo - Math.PI / 6), y - tamanho * Math.sin(angulo - Math.PI / 6));
  ctx.lineTo(x - tamanho * Math.cos(angulo + Math.PI / 6), y - tamanho * Math.sin(angulo + Math.PI / 6));
  ctx.closePath();
  ctx.fill();
}

function desenharGrafo(idCanvas, caminhoDestacado = [], noDestacado = null, foco = null) {
  const canvas = document.getElementById(idCanvas);
  if (!canvas) return;
  const ctx = canvas.getContext('2d');

  canvas.width = canvas.parentElement.clientWidth;
  canvas.height = canvas.parentElement.clientHeight;
  ctx.clearRect(0, 0, canvas.width, canvas.height);
  if (grafo.nos.length === 0) return;

  const nosBase = foco ? posicionarVizinhanca(foco) : grafo.nos;
  const idsVisiveis = new Set(nosBase.map(n => n.id));
  const projetar = ajustarAoCanvas(nosBase, canvas.width, canvas.height);
  const posicoes = new Map(nosBase.map(n => [n.id, projetar(n)]));

  grafo.arestas.forEach(aresta => {
    if (foco && aresta.origem !== foco && aresta.destino !== foco) return;
    const origem = posicoes.get(aresta.origem);
    const destino = posicoes.get(aresta.destino);
    if (!origem || !destino) return;

    const dx = destino.x - origem.x;
    const dy = destino.y - origem.y;
    const comprimento = Math.hypot(dx, dy) || 1;
    const ux = dx / comprimento, uy = dy / comprimento;
    const px = -uy, py = ux;
    const temVolta = grafo.obterAresta(aresta.destino, aresta.origem) !== null;
    const deslocamento = temVolta ? 6 : 0;

    const sx = origem.x + px * deslocamento + ux * RAIO_NO;
    const sy = origem.y + py * deslocamento + uy * RAIO_NO;
    const tx = destino.x + px * deslocamento - ux * RAIO_NO;
    const ty = destino.y + py * deslocamento - uy * RAIO_NO;

    const estaBloqueada = !aresta.ativa;
    const estaDestacada = caminhoDestacado.some((no, i) =>
      i < caminhoDestacado.length - 1 && no === aresta.origem && caminhoDestacado[i + 1] === aresta.destino
    );

    let cor = '#4b5563', largura = 1.5, tracejado = [];
    if (estaBloqueada) { cor = '#ef4444'; largura = 2; tracejado = [5, 5]; }
    else if (estaDestacada) { cor = '#10b981'; largura = 4; }

    ctx.setLineDash(tracejado);
    ctx.strokeStyle = cor;
    ctx.fillStyle = cor;
    ctx.lineWidth = largura;
    ctx.beginPath();
    ctx.moveTo(sx, sy);
    ctx.lineTo(tx, ty);
    ctx.stroke();
    ctx.setLineDash([]);
    desenharSeta(ctx, tx, ty, Math.atan2(dy, dx), estaDestacada ? 11 : 8);

    ctx.fillStyle = estaBloqueada ? '#ef4444' : (estaDestacada ? '#10b981' : '#9ca3af');
    ctx.font = '11px sans-serif';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillText(aresta.afinidade, (sx + tx) / 2 + px * 9, (sy + ty) / 2 + py * 9);
  });

  grafo.nos.forEach(no => {
    if (!idsVisiveis.has(no.id)) return;
    const { x, y } = posicoes.get(no.id);
    const estaSelecionado = noDestacado === no.id || caminhoDestacado.includes(no.id);

    ctx.beginPath();
    ctx.arc(x, y, RAIO_NO, 0, 2 * Math.PI);
    ctx.fillStyle = estaSelecionado ? '#6366f1' : '#1f2937';
    ctx.fill();
    ctx.strokeStyle = estaSelecionado ? '#818cf8' : '#4b5563';
    ctx.lineWidth = 2;
    ctx.stroke();

    ctx.fillStyle = '#ffffff';
    ctx.font = '12px sans-serif';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillText(no.id[0], x, y);

    ctx.fillStyle = '#9ca3af';
    ctx.font = '11px sans-serif';
    ctx.fillText(no.id, x, y + RAIO_NO + 10);
  });
}
