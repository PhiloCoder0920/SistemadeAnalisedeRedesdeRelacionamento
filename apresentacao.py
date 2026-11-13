# Funções que montam os fragmentos HTML e preenchem os templates da interface.

import html
import math
from pathlib import Path
from urllib.parse import urlsplit

from analises import (
    buscar_cadeias,
    componentes_fortemente_conexos,
    listar_ciclos,
    matriz_caminhos,
)


ROOT = Path(__file__).resolve().parent


# Gera opções HTML para todos os usuários, marcando o usuário selecionado.
def opcoes_usuarios(grafo, selecionado):
    return "".join(
        f'<option value="{html.escape(uid, quote=True)}"'
        f'{" selected" if uid == selecionado else ""}>{html.escape(uid)}</option>'
        for uid in grafo.usuarios
    )


# Gera opções HTML para as conexões atualmente ativas do grafo.
def opcoes_conexoes(grafo):
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
def conexoes_bloqueadas(grafo):
    linhas = [
        f'<div class="list-row msg-erro">{html.escape(origem)} → {html.escape(aresta["destino"])}</div>'
        for origem, arestas in grafo.adj.items()
        for aresta in arestas
        if not aresta["ativa"]
    ]
    return "".join(linhas) or '<p class="muted">Nenhuma conexão desativada.</p>'


# Renderiza o grafo em SVG, destacando uma rota e filtrando usuários se pedido.
def desenhar_grafo(grafo, caminho_destacado=None, usuarios_visiveis=None):
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


# Prepara os valores HTML da página de análises estruturais da rede.
def renderizar_analise(grafo, criterio="saltos", acao="", origem="", destino=""):
    selecionado = criterio if criterio in ("saltos", "custo") else "saltos"
    opcoes = {
        "{{ criterio_saltos }}": " checked" if selecionado == "saltos" else "",
        "{{ criterio_custo }}": " checked" if selecionado == "custo" else "",
        "{{ opcoes_analise_origem }}": opcoes_usuarios(grafo, origem or next(iter(grafo.usuarios), "")),
        "{{ opcoes_analise_destino }}": opcoes_usuarios(grafo, destino or list(grafo.usuarios)[-1]),
        "{{ matriz_caminhos }}": matriz_caminhos(grafo, selecionado),
        "{{ componentes_scc }}": "".join(
            f'<div class="list-row"><span>{", ".join(html.escape(uid) for uid in grupo)}</span>'
            f'<span class="badge">{len(grupo)} perfil{"s" if len(grupo) != 1 else ""}</span></div>'
            for grupo in componentes_fortemente_conexos(grafo)
        ) or '<p class="muted">Nenhum perfil na rede.</p>',
    }
    ciclos, ciclos_truncados = listar_ciclos(grafo)
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
        caminhos, ordem_visita, truncado = buscar_cadeias(grafo, origem, destino, 100)
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
    grafo,
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
        "{{ opcoes_origem }}": opcoes_usuarios(grafo, origem or next(iter(grafo.usuarios), "")),
        "{{ opcoes_destino }}": opcoes_usuarios(grafo, destino or list(grafo.usuarios)[-1]),
        "{{ opcoes_conexao }}": opcoes_conexoes(grafo),
        "{{ conexoes_bloqueadas }}": conexoes_bloqueadas(grafo),
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
        "{{ grafo_svg }}": desenhar_grafo(grafo, caminho_destacado),
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
        "{{ opcoes_perfil }}": opcoes_usuarios(grafo, usuario_selecionado),
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
        "{{ grafo_perfil }}": desenhar_grafo(grafo, usuarios_visiveis=vizinhanca),
    }
    if urlsplit(caminho).path == "/html/analise.html":
        substituicoes.update(
            renderizar_analise(grafo, criterio_analise, acao_analise, origem, destino)
        )
    for marcador, valor in substituicoes.items():
        pagina = pagina.replace(marcador, valor)
    return pagina.encode("utf-8")
