const ALIAS = {
  perfis: ['profiles', 'perfis', 'nos', 'nodes'],
  conexoes: ['connections', 'conexoes', 'arestas', 'edges'],
  origem: ['from', 'origem', 'source'],
  destino: ['to', 'destino', 'target'],
  afinidade: ['afinidade', 'weight', 'peso'],
  interacoes: ['interacoes', 'interactions']
};

function primeiroValor(objeto, chaves) {
  const chave = chaves.find(c => objeto[c] !== undefined && objeto[c] !== null && objeto[c] !== '');
  return chave === undefined ? undefined : objeto[chave];
}

function interpretarJSON(texto) {
  const dados = JSON.parse(texto);
  const listaPerfis = primeiroValor(dados, ALIAS.perfis) || [];
  const listaConexoes = primeiroValor(dados, ALIAS.conexoes);
  if (!Array.isArray(listaConexoes)) throw new Error('Campo "connections" ausente ou inválido');

  const perfis = listaPerfis.map(p => {
    if (typeof p === 'string') return { nome: p.trim() };
    const nome = primeiroValor(p, ['name', 'nome', 'id']);
    return { nome: typeof nome === 'string' ? nome.trim() : nome, x: p.x, y: p.y };
  });

  const conexoes = listaConexoes.map(c => ({
    origem: primeiroValor(c, ALIAS.origem),
    destino: primeiroValor(c, ALIAS.destino),
    afinidade: Number(primeiroValor(c, ALIAS.afinidade)),
    interacoes: Number(primeiroValor(c, ALIAS.interacoes) ?? 0)
  }));

  return { perfis, conexoes, derivarPerfis: listaPerfis.length === 0 };
}

function interpretarCSV(texto) {
  const linhas = texto.split(/\r?\n/).map(l => l.trim()).filter(l => l.length > 0);
  if (linhas.length < 2) throw new Error('CSV sem linhas de dados');

  const separador = linhas[0].includes(';') ? ';' : ',';
  const cabecalho = linhas[0].split(separador).map(c => c.trim().toLowerCase());
  const coluna = (chaves) => cabecalho.findIndex(c => chaves.includes(c));

  const iOrigem = coluna(ALIAS.origem);
  const iDestino = coluna(ALIAS.destino);
  const iAfinidade = coluna(ALIAS.afinidade);
  const iInteracoes = coluna(ALIAS.interacoes);
  if (iOrigem < 0 || iDestino < 0 || iAfinidade < 0) {
    throw new Error('Cabeçalho do CSV deve conter from, to e weight (ou origem, destino e afinidade)');
  }

  const conexoes = linhas.slice(1).map(linha => {
    const campos = linha.split(separador).map(c => c.trim());
    return {
      origem: campos[iOrigem],
      destino: campos[iDestino],
      afinidade: Number(campos[iAfinidade]),
      interacoes: iInteracoes >= 0 ? Number(campos[iInteracoes] || 0) : 0
    };
  });

  return { perfis: [], conexoes, derivarPerfis: true };
}

function interpretarArquivoRede(texto, nomeArquivo) {
  const eJSON = nomeArquivo.toLowerCase().endsWith('.json');
  const eCSV = nomeArquivo.toLowerCase().endsWith('.csv');
  if (!eJSON && !eCSV) throw new Error('Formato não suportado: use .json ou .csv');

  const dados = eJSON ? interpretarJSON(texto) : interpretarCSV(texto);
  if (dados.derivarPerfis) {
    const nomes = [];
    dados.conexoes.forEach(c => {
      [c.origem, c.destino].forEach(nome => {
        if (nome && !nomes.includes(nome)) nomes.push(nome);
      });
    });
    dados.perfis = nomes.map(nome => ({ nome }));
  }
  return dados;
}

// Cada verificação devolve { ok, mensagem }
function validarRede({ perfis, conexoes }) {
  const nomes = perfis.map(p => p.nome);
  const conhecidos = new Set(nomes);

  const perfisInvalidos = nomes.filter(n => typeof n !== 'string' || n.length === 0);
  const verificarPerfis = perfis.length === 0
    ? { ok: false, mensagem: 'Nenhum perfil encontrado' }
    : perfisInvalidos.length > 0
      ? { ok: false, mensagem: 'Há perfis sem nome' }
      : { ok: true, mensagem: `${perfis.length} perfis` };

  const problemasConexao = [];
  const pares = new Set();
  conexoes.forEach((c, i) => {
    const linha = `conexão ${i + 1}`;
    if (!conhecidos.has(c.origem) || !conhecidos.has(c.destino)) problemasConexao.push(`${linha}: perfil inexistente`);
    else if (c.origem === c.destino) problemasConexao.push(`${linha}: perfil conectado a si mesmo`);
    else if (!(c.afinidade > 0) || !isFinite(c.afinidade)) problemasConexao.push(`${linha}: afinidade deve ser um número maior que 0`);
    else if (!(c.interacoes >= 0) || !isFinite(c.interacoes)) problemasConexao.push(`${linha}: interações inválidas`);
    else if (pares.has(`${c.origem}>${c.destino}`)) problemasConexao.push(`${linha}: ${c.origem} → ${c.destino} duplicada`);
    pares.add(`${c.origem}>${c.destino}`);
  });
  const verificarConexoes = conexoes.length === 0
    ? { ok: false, mensagem: 'Nenhuma conexão encontrada' }
    : problemasConexao.length > 0
      ? { ok: false, mensagem: problemasConexao.slice(0, 3).join('; ') }
      : { ok: true, mensagem: `${conexoes.length} conexões` };

  const comConexao = new Set();
  conexoes.forEach(c => { comConexao.add(c.origem); comConexao.add(c.destino); });
  const orfaos = nomes.filter(n => !comConexao.has(n));
  const verificarOrfaos = orfaos.length > 0
    ? { ok: false, mensagem: `Sem conexões: ${orfaos.join(', ')}` }
    : { ok: true, mensagem: 'Todos os perfis possuem conexões' };

  const normalizados = nomes.filter(n => typeof n === 'string').map(n => n.toLowerCase());
  const duplicados = [...new Set(normalizados.filter((n, i) => normalizados.indexOf(n) !== i))];
  const verificarDuplicados = duplicados.length > 0
    ? { ok: false, mensagem: `Nomes duplicados: ${duplicados.join(', ')}` }
    : { ok: true, mensagem: 'Nenhum nome repetido' };

  return {
    perfis: verificarPerfis,
    conexoes: verificarConexoes,
    orfaos: verificarOrfaos,
    duplicados: verificarDuplicados
  };
}

function construirGrafo({ perfis, conexoes }) {
  const novo = new Grafo();
  perfis.forEach(p => novo.adicionarNo(p.nome, Number.isFinite(p.x) ? p.x : null, Number.isFinite(p.y) ? p.y : null));
  if (novo.nos.some(n => n.x === null || n.y === null)) novo.distribuirEmCirculo();
  conexoes.forEach(c => novo.adicionarAresta(c.origem, c.destino, c.afinidade, c.interacoes));
  return novo;
}
