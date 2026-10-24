// Algoritmo BFS (Menor Número de Saltos / Graus de Separação)
function executarBFS(noInicio, noObjetivo) {
  const fila = [[noInicio]];
  const visitados = new Set([noInicio]);

  while (fila.length > 0) {
    const caminho = fila.shift();
    const noAtual = caminho[caminho.length - 1];

    if (noAtual === noObjetivo) return caminho;

    const vizinhos = dadosGrafo.arestas
      .filter(e => e.origem === noAtual && !dadosGrafo.arestasDesativadas.some(d => d.origem === e.origem && d.destino === e.destino))
      .map(e => e.destino);

    for (const vizinho of vizinhos) {
      if (!visitados.has(vizinho)) {
        visitados.add(vizinho);
        fila.push([...caminho, vizinho]);
      }
    }
  }
  return null;
}

// Algoritmo Dijkstra (Maior Afinidade / Menor Distância Social)
function executarDijkstra(noInicio, noObjetivo) {
  const distancias = {};
  const anteriores = {};
  const nosNaoVisitados = new Set();

  dadosGrafo.nos.forEach(n => {
    distancias[n.id] = Infinity;
    anteriores[n.id] = null;
    nosNaoVisitados.add(n.id);
  });

  distancias[noInicio] = 0;

  while (nosNaoVisitados.size > 0) {
    let menorNo = null;
    nosNaoVisitados.forEach(n => {
      if (menorNo === null || distancias[n] < distancias[menorNo]) {
        menorNo = n;
      }
    });

    if (menorNo === noObjetivo) {
      const caminho = [];
      let atual = noObjetivo;
      while (atual) {
        caminho.unshift(atual);
        atual = anteriores[atual];
      }
      return caminho.length > 1 ? caminho : null;
    }

    if (menorNo === null || distancias[menorNo] === Infinity) break;

    nosNaoVisitados.delete(menorNo);

    const arestasAtivas = dadosGrafo.arestas.filter(e => 
      e.origem === menorNo && !dadosGrafo.arestasDesativadas.some(d => d.origem === e.origem && d.destino === e.destino)
    );

    for (const aresta of arestasAtivas) {
      // Usa o inverso do peso (1 / peso) para que maior peso signifique maior afinidade
      const distanciaAlt = distancias[menorNo] + (1 / aresta.peso);
      if (distanciaAlt < distancias[aresta.destino]) {
        distancias[aresta.destino] = distanciaAlt;
        anteriores[aresta.destino] = menorNo;
      }
    }
  }

  return null;
}
