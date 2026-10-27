// Dados Compartilhados do Grafo (10 Usuários, 20 Conexões)
const dadosGrafo = {
  nos: [
    { id: 'Ana', x: 250, y: 180 },
    { id: 'Bruno', x: 340, y: 250 },
    { id: 'Carla', x: 260, y: 310 },
    { id: 'Daniel', x: 220, y: 380 },
    { id: 'Eduardo', x: 120, y: 280 },
    { id: 'Fernanda', x: 140, y: 350 },
    { id: 'Gustavo', x: 160, y: 190 },
    { id: 'Helena', x: 180, y: 100 },
    { id: 'Igor', x: 300, y: 90 },
    { id: 'Julia', x: 340, y: 160 }
  ],
  arestas: [
    { origem: 'Carla', destino: 'Fernanda', peso: 4 },
    { origem: 'Julia', destino: 'Bruno', peso: 2 },
    { origem: 'Helena', destino: 'Igor', peso: 3 },
    { origem: 'Bruno', destino: 'Daniel', peso: 3 },
    { origem: 'Bruno', destino: 'Carla', peso: 4 },
    { origem: 'Gustavo', destino: 'Julia', peso: 4 },
    { origem: 'Ana', destino: 'Bruno', peso: 3 },
    { origem: 'Bruno', destino: 'Ana', peso: 5 },
    { origem: 'Carla', destino: 'Ana', peso: 8 },
    { origem: 'Daniel', destino: 'Carla', peso: 3 },
    { origem: 'Eduardo', destino: 'Fernanda', peso: 2 },
    { origem: 'Eduardo', destino: 'Gustavo', peso: 5 },
    { origem: 'Fernanda', destino: 'Eduardo', peso: 2 },
    { origem: 'Gustavo', destino: 'Ana', peso: 4 },
    { origem: 'Gustavo', destino: 'Helena', peso: 3 },
    { origem: 'Helena', destino: 'Gustavo', peso: 3 },
    { origem: 'Igor', destino: 'Julia', peso: 6 },
    { origem: 'Julia', destino: 'Ana', peso: 2 },
    { origem: 'Julia', destino: 'Helena', peso: 1 },
    { origem: 'Carla', destino: 'Bruno', peso: 4 }
  ],
  arestasDesativadas: []
};

// Funções de renderização no Canvas
function desenharGrafo(idCanvas, caminhoDestacado = [], noDestacado = null) {
  const canvas = document.getElementById(idCanvas);
  if (!canvas) return;
  const ctx = canvas.getContext('2d');
  
  canvas.width = canvas.parentElement.clientWidth;
  canvas.height = canvas.parentElement.clientHeight;

  ctx.clearRect(0, 0, canvas.width, canvas.height);

  const escalaX = canvas.width / 450;
  const escalaY = canvas.height / 450;

  // Desenhar Arestas (Conexões)
  dadosGrafo.arestas.forEach(aresta => {
    const origemNode = dadosGrafo.nos.find(n => n.id === aresta.origem);
    const destinoNode = dadosGrafo.nos.find(n => n.id === aresta.destino);
    if (!origemNode || !destinoNode) return;

    const sx = origemNode.x * escalaX;
    const sy = origemNode.y * escalaY;
    const tx = destinoNode.x * escalaX;
    const ty = destinoNode.y * escalaY;

    const estaBloqueada = dadosGrafo.arestasDesativadas.some(e => e.origem === aresta.origem && e.destino === aresta.destino);
    const estaDestacada = caminhoDestacado.length > 1 && caminhoDestacado.some((no, i) => 
      i < caminhoDestacado.length - 1 && caminhoDestacado[i] === aresta.origem && caminhoDestacado[i+1] === aresta.destino
    );

    ctx.beginPath();
    ctx.moveTo(sx, sy);
    ctx.lineTo(tx, ty);

    if (estaBloqueada) {
      ctx.setLineDash([5, 5]);
      ctx.strokeStyle = '#ef4444';
      ctx.lineWidth = 2;
    } else if (estaDestacada) {
      ctx.setLineDash([]);
      ctx.strokeStyle = '#10b981';
      ctx.lineWidth = 4;
    } else {
      ctx.setLineDash([]);
      ctx.strokeStyle = '#374151';
      ctx.lineWidth = 1.5;
    }
    ctx.stroke();

    // Rótulo do Peso
    const meioX = (sx + tx) / 2;
    const meioY = (sy + ty) / 2;
    ctx.fillStyle = estaBloqueada ? '#ef4444' : (estaDestacada ? '#10b981' : '#9ca3af');
    ctx.font = '11px sans-serif';
    ctx.fillText(aresta.peso, meioX, meioY - 4);
  });

  // Desenhar Nós (Perfis)
  dadosGrafo.nos.forEach(no => {
    const nx = no.x * escalaX;
    const ny = no.y * escalaY;

    const estaSelecionado = noDestacado === no.id || caminhoDestacado.includes(no.id);

    ctx.beginPath();
    ctx.arc(nx, ny, 16, 0, 2 * Math.PI);
    ctx.fillStyle = estaSelecionado ? '#6366f1' : '#1f2937';
    ctx.fill();
    ctx.strokeStyle = estaSelecionado ? '#818cf8' : '#4b5563';
    ctx.lineWidth = 2;
    ctx.stroke();

    ctx.fillStyle = '#ffffff';
    ctx.font = '12px sans-serif';
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillText(no.id[0], nx, ny);

    ctx.fillStyle = '#9ca3af';
    ctx.font = '11px sans-serif';
    ctx.fillText(no.id, nx, ny + 26);
  });
}
