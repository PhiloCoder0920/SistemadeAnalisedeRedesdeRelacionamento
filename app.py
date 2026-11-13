# Servidor HTTP e renderização da interface de análise de redes sociais.

import csv
import html
import io
import json
import math
from email import policy
from email.parser import BytesParser
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

from rede_relacionamento import GrafoSocial


ROOT = Path(__file__).resolve().parent
ARQUIVO_REDE = ROOT / "dados" / "exemplo-pdf.json"
grafo = None


# Carrega o arquivo JSON de exemplo e o converte em um grafo social.
def carregar_grafo():
    with ARQUIVO_REDE.open(encoding="utf-8") as arquivo:
        dados = json.load(arquivo)

    rede = GrafoSocial()
    for perfil in dados["profiles"]:
        rede.adicionar_usuario(perfil["name"], perfil["name"])
    for conexao in dados["connections"]:
        rede.adicionar_conexao(
            conexao["from"], conexao["to"], conexao["afinidade"]
        )
    return rede


# Gera opções HTML para todos os usuários, marcando o usuário selecionado.
def opcoes_usuarios(selecionado):
    return "".join(
        f'<option value="{html.escape(uid, quote=True)}"'
        f'{" selected" if uid == selecionado else ""}>{html.escape(uid)}</option>'
        for uid in grafo.usuarios
    )


# Gera opções HTML para as conexões atualmente ativas do grafo.
def opcoes_conexoes():
    conexoes = [
        (uid, aresta["destino"])
        for uid, arestas in grafo.adj.items()
        for aresta in arestas
        if aresta["ativa"]
    ]
    return "".join(
        f'<option value="{indice}">{html.escape(origem)} → {html.escape(destino)}</option>'
        for indice, (origem, destino) in enumerate(conexoes)
    )


# Gera linhas HTML para conexões desativadas ou uma mensagem vazia.
def conexoes_bloqueadas():
    linhas = [
        f'<div class="list-row msg-erro">{html.escape(origem)} → {html.escape(aresta["destino"])}</div>'
        for origem, arestas in grafo.adj.items()
        for aresta in arestas
        if not aresta["ativa"]
    ]
    return "".join(linhas) or '<p class="muted">Nenhuma conexão desativada.</p>'


# Renderiza o grafo em SVG, destacando uma rota e filtrando usuários se pedido.
def desenhar_grafo(caminho_destacado=None, usuarios_visiveis=None):
    usuarios = [
        uid for uid in grafo.usuarios
        if usuarios_visiveis is None or uid in usuarios_visiveis
    ]
    if not usuarios:
        return '<p class="muted">Nenhum perfil para exibir.</p>'

    posicoes = {
        uid: (
            450 + 190 * math.cos(2 * math.pi * indice / len(usuarios) - math.pi / 2),
            250 + 175 * math.sin(2 * math.pi * indice / len(usuarios) - math.pi / 2),
        )
        for indice, uid in enumerate(usuarios)
    }
    destacadas = set(zip(caminho_destacado or [], (caminho_destacado or [])[1:]))
    partes = [
        '<svg class="graph-svg" viewBox="0 0 900 500" role="img" aria-label="Grafo da rede">',
        '<defs><marker id="seta" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8 z" fill="#9ca3af"/></marker></defs>',
    ]

    for origem, arestas in grafo.adj.items():
        if origem not in posicoes:
            continue
        for aresta in arestas:
            destino = aresta["destino"]
            if destino not in posicoes:
                continue
            x1, y1 = posicoes[origem]
            x2, y2 = posicoes[destino]
            dx, dy = x2 - x1, y2 - y1
            distancia = math.hypot(dx, dy) or 1
            ux, uy = dx / distancia, dy / distancia
            px, py = -uy, ux
            curva = any(item["destino"] == origem for item in grafo.adj.get(destino, []))
            deslocamento = 10 if curva else 0
            sx, sy = x1 + px * deslocamento + ux * 20, y1 + py * deslocamento + uy * 20
            tx, ty = x2 + px * deslocamento - ux * 20, y2 + py * deslocamento - uy * 20
            ativa = aresta["ativa"]
            cor = "#ef4444" if not ativa else "#10b981" if (origem, destino) in destacadas else "#667085"
            tracejado = ' stroke-dasharray="6 5"' if not ativa else ""
            if curva:
                cx, cy = (sx + tx) / 2 + px * 24, (sy + ty) / 2 + py * 24
                geometria = f"M{sx:.1f},{sy:.1f} Q{cx:.1f},{cy:.1f} {tx:.1f},{ty:.1f}"
                lx, ly = (sx + 2 * cx + tx) / 4, (sy + 2 * cy + ty) / 4
            else:
                geometria = f"M{sx:.1f},{sy:.1f} L{tx:.1f},{ty:.1f}"
                lx, ly = (sx + tx) / 2, (sy + ty) / 2 - 8
            afinidade = 1 / aresta["peso"] if aresta["peso"] else 0
            partes.append(
                f'<path d="{geometria}" fill="none" stroke="{cor}" stroke-width="2"'
                f'{tracejado} marker-end="url(#seta)"/>'
            )
            partes.append(f'<text class="edge-label" x="{lx:.1f}" y="{ly:.1f}">{afinidade:.2f}</text>')

    for uid, (x, y) in posicoes.items():
        partes.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="19" fill="#6366f1"/>')
        partes.append(f'<text class="node-label" x="{x:.1f}" y="{y + 36:.1f}">{html.escape(uid)}</text>')
    partes.append("</svg>")
    return "".join(partes)


# Calcula e renderiza a matriz de menores distâncias por saltos ou custo.
def matriz_caminhos(criterio):
    usuarios = list(grafo.usuarios)
    distancias = {origem: {destino: math.inf for destino in usuarios} for origem in usuarios}
    for usuario in usuarios:
        distancias[usuario][usuario] = 0
    for origem, arestas in grafo.adj.items():
        for aresta in arestas:
            if aresta["ativa"]:
                custo = aresta["peso"] if criterio == "custo" else 1
                distancias[origem][aresta["destino"]] = min(
                    distancias[origem][aresta["destino"]], custo
                )
    for intermediario in usuarios:
        for origem in usuarios:
            for destino in usuarios:
                alternativa = distancias[origem][intermediario] + distancias[intermediario][destino]
                if alternativa < distancias[origem][destino]:
                    distancias[origem][destino] = alternativa

    cabecalho = "".join(f"<th>{html.escape(uid)}</th>" for uid in usuarios)
    linhas = []
    for origem in usuarios:
        celulas = []
        for destino in usuarios:
            distancia = distancias[origem][destino]
            if math.isinf(distancia):
                valor = "∞"
                classe = "sem-rota"
            else:
                valor = f"{distancia:.2f}" if criterio == "custo" else str(int(distancia))
                classe = "diagonal" if origem == destino else ""
            atributo_classe = f' class="{classe}"' if classe else ""
            celulas.append(f"<td{atributo_classe}>{valor}</td>")
        valores = "".join(celulas)
        linhas.append(f"<tr><th>{html.escape(origem)}</th>{valores}</tr>")
    return (
        f'<table class="matrix-table"><thead><tr><th></th>{cabecalho}</tr></thead>'
        f'<tbody>{"".join(linhas)}</tbody></table>'
    )


# Encontra componentes fortemente conexos usando o algoritmo de Tarjan.
def componentes_fortemente_conexos():
    indice = 0
    indices = {}
    baixos = {}
    pilha = []
    na_pilha = set()
    componentes = []

    # Visita recursivamente os vizinhos ativos e atualiza os índices de Tarjan.
    def visitar(usuario):
        nonlocal indice
        indices[usuario] = baixos[usuario] = indice
        indice += 1
        pilha.append(usuario)
        na_pilha.add(usuario)
        for aresta in grafo.adj.get(usuario, []):
            destino = aresta["destino"]
            if not aresta["ativa"]:
                continue
            if destino not in indices:
                visitar(destino)
                baixos[usuario] = min(baixos[usuario], baixos[destino])
            elif destino in na_pilha:
                baixos[usuario] = min(baixos[usuario], indices[destino])
        if baixos[usuario] == indices[usuario]:
            componente = []
            while True:
                membro = pilha.pop()
                na_pilha.remove(membro)
                componente.append(membro)
                if membro == usuario:
                    break
            componentes.append(sorted(componente))

    for usuario in grafo.usuarios:
        if usuario not in indices:
            visitar(usuario)
    return sorted(componentes, key=lambda grupo: grupo[0])


# Enumera ciclos simples do grafo até o limite e informa se houve truncamento.
def listar_ciclos(limite=100):
    usuarios = list(grafo.usuarios)
    ordem = {usuario: indice for indice, usuario in enumerate(usuarios)}
    ciclos = []
    truncado = False

    # Explora ciclos sem repetir vértices e elimina duplicatas por ordenação.
    def buscar(inicio, atual, caminho):
        nonlocal truncado
        for aresta in grafo.adj.get(atual, []):
            destino = aresta["destino"]
            if not aresta["ativa"] or ordem[destino] < ordem[inicio]:
                continue
            if destino == inicio:
                ciclos.append(caminho + [inicio])
                if len(ciclos) >= limite:
                    truncado = True
                    return
            elif destino not in caminho:
                buscar(inicio, destino, caminho + [destino])
                if truncado:
                    return

    for inicio in usuarios:
        buscar(inicio, inicio, [inicio])
        if truncado:
            break
    return ciclos, truncado


# Busca caminhos simples entre dois usuários e os ordena pelo custo total.
def buscar_cadeias(origem, destino, limite=100):
    caminhos = []
    ordem_visita = []
    visitados = set()
    truncado = False

    # Percorre conexões ativas em profundidade e registra caminhos até o destino.
    def buscar(atual, caminho, custo):
        nonlocal truncado
        if atual not in visitados:
            visitados.add(atual)
            ordem_visita.append(atual)
        if atual == destino:
            caminhos.append((custo, caminho))
            if len(caminhos) >= limite:
                truncado = True
            return
        for aresta in grafo.adj.get(atual, []):
            proximo = aresta["destino"]
            if not aresta["ativa"] or proximo in caminho:
                continue
            buscar(proximo, caminho + [proximo], custo + aresta["peso"])
            if truncado:
                return

    if origem in grafo.usuarios and destino in grafo.usuarios:
        buscar(origem, [origem], 0)
    caminhos.sort(key=lambda item: item[0])
    return caminhos, ordem_visita, truncado


# Prepara os valores HTML da página de análises estruturais da rede.
def renderizar_analise(criterio="saltos", acao="", origem="", destino=""):
    selecionado = criterio if criterio in ("saltos", "custo") else "saltos"
    opcoes = {
        "{{ criterio_saltos }}": " checked" if selecionado == "saltos" else "",
        "{{ criterio_custo }}": " checked" if selecionado == "custo" else "",
        "{{ opcoes_analise_origem }}": opcoes_usuarios(origem or next(iter(grafo.usuarios), "")),
        "{{ opcoes_analise_destino }}": opcoes_usuarios(destino or list(grafo.usuarios)[-1]),
        "{{ matriz_caminhos }}": matriz_caminhos(selecionado),
        "{{ componentes_scc }}": "".join(
            f'<div class="list-row"><span>{", ".join(html.escape(uid) for uid in grupo)}</span>'
            f'<span class="badge">{len(grupo)} perfil{"s" if len(grupo) != 1 else ""}</span></div>'
            for grupo in componentes_fortemente_conexos()
        ) or '<p class="muted">Nenhum perfil na rede.</p>',
    }
    ciclos, ciclos_truncados = listar_ciclos()
    opcoes["{{ resumo_ciclos }}"] = (
        f'{len(ciclos)} ciclo(s) encontrado(s)'
        f'{" (exibição limitada a 100)." if ciclos_truncados else "."}'
    )
    opcoes["{{ lista_ciclos }}"] = "".join(
        f'<div class="list-row">{" → ".join(html.escape(uid) for uid in ciclo)}</div>'
        for ciclo in ciclos
    ) or '<p class="muted">Nenhum ciclo encontrado.</p>'
    opcoes["{{ resultado_cadeias }}"] = (
        '<p class="muted">Selecione origem e destino e escolha uma busca.</p>'
    )
    if acao in ("cadeias", "dfs"):
        caminhos, ordem_visita, truncado = buscar_cadeias(origem, destino, 100)
        if acao == "dfs":
            opcoes["{{ resultado_cadeias }}"] = (
                f'<p>Ordem de visita DFS: {" → ".join(html.escape(uid) for uid in ordem_visita) or "nenhum perfil"}</p>'
            )
        elif caminhos:
            linhas = "".join(
                f'<div class="list-row"><span>{" → ".join(html.escape(uid) for uid in caminho)}</span>'
                f'<span class="badge">distância {custo:.2f}</span></div>'
                for custo, caminho in caminhos
            )
            aviso = '<p class="muted">Exibindo os primeiros 100 caminhos.</p>' if truncado else ""
            opcoes["{{ resultado_cadeias }}"] = aviso + linhas
        else:
            opcoes["{{ resultado_cadeias }}"] = '<p class="muted">Nenhuma cadeia encontrada entre esses perfis.</p>'
    return opcoes


# Preenche o template solicitado com métricas e dados atuais do grafo.
def renderizar(
    caminho,
    origem="",
    destino="",
    resultado="",
    status_importacao="",
    caminho_destacado=None,
    usuario_perfil="",
    criterio_analise="saltos",
    acao_analise="",
):
    arquivos = {
        "/": ROOT / "index.html",
        "/index.html": ROOT / "index.html",
        "/html/consultas.html": ROOT / "html" / "consultas.html",
        "/html/analise.html": ROOT / "html" / "analise.html",
        "/html/falhas.html": ROOT / "html" / "falhas.html",
        "/html/perfil.html": ROOT / "html" / "perfil.html",
        "/html/dados.html": ROOT / "html" / "dados.html",
    }
    arquivo = arquivos.get(urlsplit(caminho).path)
    if arquivo is None:
        return None

    pagina = arquivo.read_text(encoding="utf-8")
    usuario_selecionado = (
        usuario_perfil if usuario_perfil in grafo.usuarios else next(iter(grafo.usuarios), "")
    )
    saidas = [
        (uid, aresta)
        for uid, arestas in grafo.adj.items()
        for aresta in arestas
        if uid == usuario_selecionado and aresta["ativa"]
    ]
    entradas = [
        (uid, aresta)
        for uid, arestas in grafo.adj.items()
        for aresta in arestas
        if aresta["destino"] == usuario_selecionado and aresta["ativa"]
    ]
    vizinhanca = {usuario_selecionado}
    vizinhanca.update(uid for uid, _ in saidas)
    vizinhanca.update(uid for uid, _ in entradas)
    graus = {
        uid: sum(aresta["ativa"] for aresta in arestas)
        + sum(
            aresta["ativa"]
            for conexoes in grafo.adj.values()
            for aresta in conexoes
            if aresta["destino"] == uid
        )
        for uid, arestas in grafo.adj.items()
    }
    ranking = sorted(graus.items(), key=lambda item: item[1], reverse=True)
    lider = ranking[0] if ranking else ("—", 0)
    substituicoes = {
        "{{ opcoes_origem }}": opcoes_usuarios(origem or next(iter(grafo.usuarios), "")),
        "{{ opcoes_destino }}": opcoes_usuarios(destino or list(grafo.usuarios)[-1]),
        "{{ opcoes_conexao }}": opcoes_conexoes(),
        "{{ conexoes_bloqueadas }}": conexoes_bloqueadas(),
        "{{ resultado }}": resultado or '<p class="muted">Execute uma consulta para ver o resultado.</p>',
        "{{ origem }}": html.escape(origem or next(iter(grafo.usuarios), ""), quote=True),
        "{{ destino }}": html.escape(destino or list(grafo.usuarios)[-1], quote=True),
        "{{ total_usuarios }}": str(len(grafo.usuarios)),
        "{{ conexoes_ativas }}": str(sum(len(arestas) for arestas in grafo.adj.values()) - sum(
            not aresta["ativa"] for arestas in grafo.adj.values() for aresta in arestas
        )),
        "{{ mais_conectado }}": (
            f'{html.escape(lider[0])} <small>({lider[1]} conexões)</small>'
        ),
        "{{ ranking }}": "".join(
            f'<div class="list-row"><span>{html.escape(uid)}</span>'
            f'<span class="badge">{grau}</span></div>'
            for uid, grau in ranking
        ),
        "{{ grafo_svg }}": desenhar_grafo(caminho_destacado),
        "{{ conexoes_desativadas }}": str(sum(
            not aresta["ativa"]
            for arestas in grafo.adj.values()
            for aresta in arestas
        )),
        "{{ status_importacao }}": status_importacao,
        "{{ perfis_rede }}": "".join(
            f'<span class="chip">{html.escape(uid)}</span>' for uid in grafo.usuarios
        ),
        "{{ conexoes_rede }}": "".join(
            f'<div class="list-row"><span>{html.escape(uid)} → {html.escape(aresta["destino"])}</span>'
            f'<span class="badge">afinidade {1 / aresta["peso"]:.2f}</span></div>'
            for uid, arestas in grafo.adj.items() for aresta in arestas
        ),
        "{{ opcoes_perfil }}": opcoes_usuarios(usuario_selecionado),
        "{{ metric_segue }}": str(len(saidas)),
        "{{ metric_seguidores }}": str(len(entradas)),
        "{{ metric_grau }}": str(len(saidas) + len(entradas)),
        "{{ titulo_segue }}": f"Conexões de {html.escape(usuario_selecionado)}",
        "{{ titulo_seguidores }}": f"Seguidores de {html.escape(usuario_selecionado)}",
        "{{ lista_segue }}": "".join(
            f'<div class="list-row"><span>{html.escape(aresta["destino"])}</span>'
            f'<span class="badge">afinidade {1 / aresta["peso"]:.2f}</span></div>'
            for _, aresta in saidas
        ) or '<p class="muted">Não segue nenhum perfil.</p>',
        "{{ lista_seguidores }}": "".join(
            f'<div class="list-row"><span>{html.escape(uid)}</span>'
            f'<span class="badge">afinidade {1 / aresta["peso"]:.2f}</span></div>'
            for uid, aresta in entradas
        ) or '<p class="muted">Não possui seguidores.</p>',
        "{{ grafo_perfil }}": desenhar_grafo(usuarios_visiveis=vizinhanca),
    }
    if urlsplit(caminho).path == "/html/analise.html":
        substituicoes.update(
            renderizar_analise(criterio_analise, acao_analise, origem, destino)
        )
    for marcador, valor in substituicoes.items():
        pagina = pagina.replace(marcador, valor)
    return pagina.encode("utf-8")


# Valida o arquivo enviado e encaminha a importação para o leitor apropriado.
def importar_arquivo(arquivo):
    if not arquivo:
        return '<p class="msg-erro">Selecione um arquivo CSV ou JSON.</p>'
    nome, conteudo = arquivo
    if Path(nome).suffix.lower() != ".json":
        return importar_csv(arquivo)
    try:
        dados = json.loads(conteudo.decode("utf-8-sig"))
    except (UnicodeDecodeError, json.JSONDecodeError):
        return '<p class="msg-erro">O arquivo JSON é inválido ou não está em UTF-8.</p>'
    if not isinstance(dados, dict):
        return '<p class="msg-erro">O arquivo JSON deve conter um objeto.</p>'
    conexoes = next(
        (dados[chave] for chave in ("connections", "conexoes", "arestas", "edges") if chave in dados),
        None,
    )
    if not isinstance(conexoes, list):
        return '<p class="msg-erro">O JSON precisa conter uma lista de connections.</p>'

    linhas = io.StringIO()
    escritor = csv.writer(linhas)
    escritor.writerow(("from", "to", "afinidade", "interacoes"))
    for conexao in conexoes:
        if not isinstance(conexao, dict):
            return '<p class="msg-erro">Há conexões com formato inválido no JSON.</p>'
        origem = next((conexao[chave] for chave in ("from", "origem", "source") if chave in conexao), "")
        destino = next((conexao[chave] for chave in ("to", "destino", "target") if chave in conexao), "")
        afinidade = next((conexao[chave] for chave in ("afinidade", "weight", "peso") if chave in conexao), "")
        interacoes = next((conexao[chave] for chave in ("interacoes", "interactions") if chave in conexao), 0)
        escritor.writerow((origem, destino, afinidade, interacoes))
    resposta = importar_csv((nome + ".csv", linhas.getvalue().encode("utf-8")))
    return resposta.replace(html.escape(nome + ".csv"), html.escape(nome))


# Valida e importa conexões CSV, substituindo o grafo somente se tudo for válido.
def importar_csv(arquivo):
    global grafo

    if not arquivo or Path(arquivo[0]).suffix.lower() != ".csv":
        return '<p class="msg-erro">Selecione um arquivo CSV.</p>'
    nome_arquivo, conteudo = arquivo
    try:
        texto = conteudo.decode("utf-8-sig")
    except UnicodeDecodeError:
        return '<p class="msg-erro">O CSV deve usar codificação UTF-8.</p>'

    primeira_linha = next((linha for linha in texto.splitlines() if linha.strip()), "")
    if not primeira_linha:
        return '<p class="msg-erro">O CSV está vazio.</p>'
    delimitador = ";" if primeira_linha.count(";") > primeira_linha.count(",") else ","
    leitor = csv.DictReader(io.StringIO(texto), delimiter=delimitador)
    cabecalhos = {str(campo).strip().lower(): campo for campo in leitor.fieldnames or []}

    # Localiza o cabeçalho CSV correspondente ao primeiro nome alternativo.
    def coluna(*nomes):
        return next((cabecalhos[nome] for nome in nomes if nome in cabecalhos), None)

    c_origem = coluna("from", "origem", "source")
    c_destino = coluna("to", "destino", "target")
    c_afinidade = coluna("afinidade", "weight", "peso")
    c_interacoes = coluna("interacoes", "interactions")
    if not c_origem or not c_destino or not c_afinidade:
        return '<p class="msg-erro">Cabeçalho CSV deve conter from,to,afinidade (ou origem,destino,peso).</p>'

    conexoes, usuarios, pares = [], {}, set()
    try:
        for numero_linha, linha in enumerate(leitor, start=2):
            if None in linha:
                raise ValueError(f"Linha {numero_linha}: quantidade de colunas inválida.")
            origem = (linha.get(c_origem) or "").strip()
            destino = (linha.get(c_destino) or "").strip()
            if not origem or not destino:
                raise ValueError(f"Linha {numero_linha}: origem e destino são obrigatórios.")

            afinidade_texto = (linha.get(c_afinidade) or "").strip()
            interacoes_texto = (linha.get(c_interacoes) or "0").strip() if c_interacoes else "0"
            if delimitador == ";":
                afinidade_texto = afinidade_texto.replace(",", ".")
                interacoes_texto = interacoes_texto.replace(",", ".")
            afinidade, interacoes = float(afinidade_texto), float(interacoes_texto)
            if not math.isfinite(afinidade) or afinidade <= 0:
                raise ValueError(f"Linha {numero_linha}: afinidade deve ser maior que zero.")
            if not math.isfinite(interacoes) or interacoes < 0:
                raise ValueError(f"Linha {numero_linha}: interações devem ser zero ou maiores.")
            if origem == destino:
                raise ValueError(f"Linha {numero_linha}: conexão de um perfil para si mesmo.")
            par = (origem.casefold(), destino.casefold())
            if par in pares:
                raise ValueError(f"Linha {numero_linha}: conexão duplicada {origem} → {destino}.")
            pares.add(par)
            usuarios.setdefault(origem, None)
            usuarios.setdefault(destino, None)
            conexoes.append((origem, destino, afinidade, interacoes))
    except (ValueError, TypeError) as erro:
        return f'<p class="msg-erro">{html.escape(str(erro))}</p>'

    if not conexoes:
        return '<p class="msg-erro">O CSV não contém conexões para importar.</p>'

    nova_rede = GrafoSocial()
    try:
        for uid in usuarios:
            nova_rede.adicionar_usuario(uid, uid)
        for origem, destino, afinidade, interacoes in conexoes:
            nova_rede.adicionar_conexao(origem, destino, afinidade)
            nova_rede.adj[origem][-1]["interacoes"] = interacoes
    except (KeyError, ValueError, ZeroDivisionError) as erro:
        return f'<p class="msg-erro">{html.escape(str(erro))}</p>'

    grafo = nova_rede
    return (
        f'<p class="msg-ok"><strong>{html.escape(nome_arquivo)}</strong> importado: '
        f'{len(usuarios)} perfis e {len(conexoes)} conexões. '
        'O grafo atualizado está visível na página Início.</p>'
    )


# Atende requisições HTTP da interface e operações sobre o grafo em memória.
class ServidorRede(BaseHTTPRequestHandler):

    # Envia a resposta HTTP com tipo de conteúdo, tamanho e status informados.
    def responder(self, conteudo, tipo="text/html; charset=utf-8", status=200):
        self.send_response(status)
        self.send_header("Content-Type", tipo)
        self.send_header("Content-Length", str(len(conteudo)))
        self.end_headers()
        self.wfile.write(conteudo)

    # Atende páginas, folha de estilos e exportação JSON em requisições GET.
    def do_GET(self):
        caminho = urlsplit(self.path).path
        if caminho == "/css/style.css":
            self.responder((ROOT / "css" / "style.css").read_bytes(), "text/css; charset=utf-8")
            return
        if caminho == "/exportar":
            dados = {
                "profiles": [{"name": uid} for uid in grafo.usuarios],
                "connections": [
                    {
                        "from": origem,
                        "to": aresta["destino"],
                        "afinidade": 1 / aresta["peso"],
                        "interacoes": aresta.get("interacoes", 0),
                    }
                    for origem, arestas in grafo.adj.items() for aresta in arestas
                ],
            }
            conteudo = json.dumps(dados, ensure_ascii=False, indent=2).encode("utf-8")
            self.responder(conteudo, "application/json; charset=utf-8")
            return
        parametros = parse_qs(urlsplit(self.path).query)
        usuario_perfil = parametros.get("usuario", [""])[0]
        conteudo = renderizar(caminho, usuario_perfil=usuario_perfil)
        if conteudo is None:
            self.responder(b"Pagina nao encontrada.", status=404)
            return
        self.responder(conteudo)

    # Processa formulários de consulta, análise, falhas e importação de dados.
    def do_POST(self):
        caminho = urlsplit(self.path).path
        if caminho not in (
            "/html/consultas.html",
            "/html/analise.html",
            "/html/falhas.html",
            "/html/dados.html",
        ):
            self.responder(b"Pagina nao encontrada.", status=404)
            return

        tamanho = int(self.headers.get("Content-Length", "0"))
        corpo = self.rfile.read(tamanho)
        tipo = self.headers.get("Content-Type", "")
        arquivos = {}
        if tipo.startswith("multipart/form-data"):
            mensagem = BytesParser(policy=policy.default).parsebytes(
                f"Content-Type: {tipo}\r\nMIME-Version: 1.0\r\n\r\n".encode("ascii") + corpo
            )
            formulario = {}
            for parte in mensagem.iter_parts():
                nome = parte.get_param("name", header="content-disposition")
                if not nome:
                    continue
                conteudo = parte.get_payload(decode=True) or b""
                if parte.get_filename():
                    arquivos[nome] = (parte.get_filename(), conteudo)
                else:
                    codificacao = parte.get_content_charset() or "utf-8"
                    formulario.setdefault(nome, []).append(conteudo.decode(codificacao))
        else:
            formulario = parse_qs(corpo.decode("utf-8"))
        valor = lambda chave, padrao="": formulario.get(chave, [padrao])[0]
        origem = valor("origem", next(iter(grafo.usuarios), ""))
        destino = valor("destino", list(grafo.usuarios)[-1])
        resultado = ""
        caminho_destacado = None

        if caminho == "/html/analise.html":
            conteudo = renderizar(
                caminho,
                origem,
                destino,
                criterio_analise=valor("criterio", "saltos"),
                acao_analise=valor("acao"),
            )
            self.responder(conteudo)
            return

        if caminho == "/html/dados.html":
            acao = valor("acao")
            if acao == "importar":
                status_importacao = importar_arquivo(arquivos.get("arquivo"))
                self.responder(renderizar(caminho, status_importacao=status_importacao))
                return
            if acao == "padrao":
                rede_padrao = carregar_grafo()
                grafo.usuarios.clear()
                grafo.usuarios.update(rede_padrao.usuarios)
                grafo.adj.clear()
                grafo.adj.update(rede_padrao.adj)
                resultado = '<p class="msg-ok">Rede de exemplo restaurada.</p>'
                self.responder(renderizar(caminho, status_importacao=resultado))
                return
            self.responder(b"Acao invalida.", status=400)
            return

        if valor("acao") == "rota" or valor("acao") == "recalcular":
            if origem not in grafo.usuarios or destino not in grafo.usuarios:
                resultado = '<p class="msg-erro">Selecione usuários existentes na rede.</p>'
            elif origem == destino:
                resultado = '<p class="msg-erro">Escolha origem e destino diferentes.</p>'
            else:
                rota, custo = grafo.dijkstra(origem, destino)
                if rota:
                    caminho_destacado = rota
                    rota_formatada = " → ".join(html.escape(nome) for nome in rota)
                    resultado = (
                        f'<p class="msg-ok"><strong>Rota encontrada:</strong> {rota_formatada}</p>'
                        f"<p><strong>Distância social:</strong> {custo:.2f}</p>"
                    )
                else:
                    resultado = '<p class="msg-erro">Não há rota disponível entre esses usuários.</p>'
        elif valor("acao") == "bloquear":
            conexoes = [
                (uid, aresta["destino"])
                for uid, arestas in grafo.adj.items()
                for aresta in arestas
                if aresta["ativa"]
            ]
            try:
                indice = int(valor("conexao", "-1"))
                if indice < 0:
                    raise IndexError
                corte_u, corte_v = conexoes[indice]
            except (ValueError, IndexError):
                resultado = '<p class="msg-erro">Selecione uma conexão ativa.</p>'
            else:
                grafo.desativar_conexao(corte_u, corte_v)
                rota, custo = grafo.dijkstra(origem, destino)
                mensagem = f"Conexão {html.escape(corte_u)} → {html.escape(corte_v)} desativada."
                if rota:
                    caminho_destacado = rota
                    rota_formatada = " → ".join(html.escape(nome) for nome in rota)
                    resultado = (
                        f'<p class="msg-ok">{mensagem}</p>'
                        f"<p><strong>Rota alternativa:</strong> {rota_formatada}</p>"
                        f"<p><strong>Distância social:</strong> {custo:.2f}</p>"
                    )
                else:
                    resultado = f'<p class="msg-erro">{mensagem} Não há rota alternativa.</p>'
        elif valor("acao") == "restaurar":
            for arestas in grafo.adj.values():
                for aresta in arestas:
                    aresta["ativa"] = True
            resultado = '<p class="msg-ok">Todas as conexões foram restauradas.</p>'
        else:
            self.responder(b"Acao invalida.", status=400)
            return

        self.responder(
            renderizar(
                caminho,
                origem,
                destino,
                resultado,
                caminho_destacado=caminho_destacado,
            )
        )

    # Registra no console cada requisição HTTP tratada pelo servidor.
    def log_message(self, formato, *argumentos):
        print(f"{self.address_string()} - {formato % argumentos}")


import os

if __name__ == "__main__":
    grafo = carregar_grafo()
    porta = int(os.environ.get("PORT", 5500))
    print(f"Servidor rodando na porta {porta}")
    HTTPServer(("0.0.0.0", porta), ServidorRede).serve_forever()
