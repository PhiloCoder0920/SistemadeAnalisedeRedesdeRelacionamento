# Algoritmos usados para calcular distâncias e estruturas do grafo social.

import html
import math


# Calcula e renderiza a matriz de menores distâncias por saltos ou custo.
def matriz_caminhos(grafo, criterio):
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
def componentes_fortemente_conexos(grafo):
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
def listar_ciclos(grafo, limite=100):
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
def buscar_cadeias(grafo, origem, destino, limite=100):
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
