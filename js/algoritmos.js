// Menor número de saltos (graus de separação)
function executarBFS(noInicio, noObjetivo) {
  const fila = [[noInicio]];
  const visitados = new Set([noInicio]);

  while (fila.length > 0) {
    const caminho = fila.shift();
    const noAtual = caminho[caminho.length - 1];

    if (noAtual === noObjetivo) return caminho;

    for (const aresta of grafo.saidas(noAtual)) {
      if (!visitados.has(aresta.destino)) {
        visitados.add(aresta.destino);
        fila.push([...caminho, aresta.destino]);
      }
    }
  }
  return null;
}

// Maior afinidade acumulada: custo de cada aresta = 1 / afinidade
function executarDijkstra(noInicio, noObjetivo) {
  const distancias = {};
  const anteriores = {};
  const pendentes = new Set();

  grafo.nos.forEach(n => {
    distancias[n.id] = Infinity;
    anteriores[n.id] = null;
    pendentes.add(n.id);
  });
  distancias[noInicio] = 0;

  while (pendentes.size > 0) {
    let menorNo = null;
    pendentes.forEach(n => {
      if (menorNo === null || distancias[n] < distancias[menorNo]) menorNo = n;
    });

    if (distancias[menorNo] === Infinity) break;

    if (menorNo === noObjetivo) {
      const caminho = [];
      for (let atual = noObjetivo; atual; atual = anteriores[atual]) caminho.unshift(atual);
      return caminho.length > 1 ? caminho : null;
    }

    pendentes.delete(menorNo);

    for (const aresta of grafo.saidas(menorNo)) {
      const alternativa = distancias[menorNo] + 1 / aresta.afinidade;
      if (alternativa < distancias[aresta.destino]) {
        distancias[aresta.destino] = alternativa;
        anteriores[aresta.destino] = menorNo;
      }
    }
  }
  return null;
}

function calcularRota(origem, destino, algoritmo) {
  return algoritmo === 'bfs' ? executarBFS(origem, destino) : executarDijkstra(origem, destino);
}

function resumirCaminho(caminho) {
  const passos = [];
  let afinidadeTotal = 0, interacoes = 0, custo = 0;

  for (let i = 0; i < caminho.length - 1; i++) {
    const aresta = grafo.obterAresta(caminho[i], caminho[i + 1]);
    passos.push({ origem: aresta.origem, destino: aresta.destino, afinidade: aresta.afinidade, interacoes: aresta.interacoes });
    afinidadeTotal += aresta.afinidade;
    interacoes += aresta.interacoes;
    custo += 1 / aresta.afinidade;
  }

  const saltos = caminho.length - 1;
  return { saltos, passos, afinidadeTotal, afinidadeMedia: afinidadeTotal / saltos, interacoes, custo };
}

// Caminhos mínimos entre todos os pares. criterio: 'saltos' ou 'custo' (1 / afinidade)
function floydWarshall(criterio) {
  const nomes = grafo.nos.map(n => n.id);
  const indice = new Map(nomes.map((nome, i) => [nome, i]));
  const n = nomes.length;
  const dist = Array.from({ length: n }, (_, i) => Array.from({ length: n }, (_, j) => (i === j ? 0 : Infinity)));
  const prox = Array.from({ length: n }, () => Array(n).fill(null));

  grafo.arestasAtivas.forEach(e => {
    const i = indice.get(e.origem), j = indice.get(e.destino);
    dist[i][j] = criterio === 'saltos' ? 1 : 1 / e.afinidade;
    prox[i][j] = j;
  });

  for (let k = 0; k < n; k++) {
    for (let i = 0; i < n; i++) {
      for (let j = 0; j < n; j++) {
        if (dist[i][k] + dist[k][j] < dist[i][j]) {
          dist[i][j] = dist[i][k] + dist[k][j];
          prox[i][j] = prox[i][k];
        }
      }
    }
  }
  return { nomes, indice, dist, prox };
}

function caminhoFloyd(resultado, origem, destino) {
  let i = resultado.indice.get(origem);
  const j = resultado.indice.get(destino);
  if (resultado.prox[i][j] === null) return i === j ? [origem] : null;
  const caminho = [origem];
  while (i !== j) {
    i = resultado.prox[i][j];
    caminho.push(resultado.nomes[i]);
  }
  return caminho;
}

// Ordem de visita em profundidade a partir de um perfil
function executarDFS(noInicio) {
  const visitados = new Set();
  const ordem = [];

  const visitar = (no) => {
    visitados.add(no);
    ordem.push(no);
    grafo.saidas(no).forEach(e => {
      if (!visitados.has(e.destino)) visitar(e.destino);
    });
  };

  visitar(noInicio);
  return ordem;
}

// Cadeias de influência alternativas (caminhos simples), da maior afinidade para a menor
function encontrarCaminhosAlternativos(origem, destino, limite = 10) {
  const encontrados = [];
  const LIMITE_BUSCA = 5000;

  const explorar = (no, caminho, visitados) => {
    if (encontrados.length >= LIMITE_BUSCA) return;
    if (no === destino) {
      encontrados.push([...caminho]);
      return;
    }
    grafo.saidas(no).forEach(e => {
      if (visitados.has(e.destino)) return;
      visitados.add(e.destino);
      caminho.push(e.destino);
      explorar(e.destino, caminho, visitados);
      caminho.pop();
      visitados.delete(e.destino);
    });
  };

  explorar(origem, [origem], new Set([origem]));
  return encontrados
    .map(caminho => ({ caminho, resumo: resumirCaminho(caminho) }))
    .sort((a, b) => a.resumo.custo - b.resumo.custo)
    .slice(0, limite);
}

// Ciclos simples (círculos fechados de relacionamento), incluindo reciprocidades de 2 perfis
function detectarCiclos(limite = 100) {
  const nomes = grafo.nos.map(n => n.id);
  const ciclos = [];

  nomes.forEach((inicio, posicaoInicio) => {
    const permitidos = new Set(nomes.slice(posicaoInicio));

    const explorar = (no, caminho, visitados) => {
      if (ciclos.length >= limite) return;
      grafo.saidas(no).forEach(e => {
        if (e.destino === inicio) {
          ciclos.push([...caminho, inicio]);
        } else if (permitidos.has(e.destino) && !visitados.has(e.destino)) {
          visitados.add(e.destino);
          caminho.push(e.destino);
          explorar(e.destino, caminho, visitados);
          caminho.pop();
          visitados.delete(e.destino);
        }
      });
    };

    explorar(inicio, [inicio], new Set([inicio]));
  });

  return ciclos.sort((a, b) => a.length - b.length);
}

// Componentes fortemente conexos (Tarjan)
function componentesFortementeConexos() {
  let contador = 0;
  const indices = new Map();
  const baixos = new Map();
  const naPilha = new Set();
  const pilha = [];
  const componentes = [];

  const conectar = (no) => {
    indices.set(no, contador);
    baixos.set(no, contador);
    contador++;
    pilha.push(no);
    naPilha.add(no);

    grafo.saidas(no).forEach(e => {
      if (!indices.has(e.destino)) {
        conectar(e.destino);
        baixos.set(no, Math.min(baixos.get(no), baixos.get(e.destino)));
      } else if (naPilha.has(e.destino)) {
        baixos.set(no, Math.min(baixos.get(no), indices.get(e.destino)));
      }
    });

    if (baixos.get(no) === indices.get(no)) {
      const componente = [];
      let atual;
      do {
        atual = pilha.pop();
        naPilha.delete(atual);
        componente.push(atual);
      } while (atual !== no);
      componentes.push(componente.reverse());
    }
  };

  grafo.nos.forEach(n => {
    if (!indices.has(n.id)) conectar(n.id);
  });

  return componentes.sort((a, b) => b.length - a.length);
}
