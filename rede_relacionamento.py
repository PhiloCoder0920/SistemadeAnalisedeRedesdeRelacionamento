import json
import heapq
import sys

# Garante suporte a acentos no console Windows
if sys.stdout.encoding and sys.stdout.encoding.lower() != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

class GrafoSocial:
    """Modelo: Digrafo Ponderado com o Algoritmo de Dijkstra."""
    def __init__(self):
        self.usuarios = {}  # id -> nome
        self.adj = {}       # id -> lista de arestas {'destino', 'peso', 'ativa'}

    def adicionar_usuario(self, uid, nome):
        self.usuarios[uid] = nome
        self.adj.setdefault(uid, [])

    def adicionar_conexao(self, u, v, afinidade):
        # Aresta direcionada u -> v.
        # Peso da aresta = Distância Social (1 / afinidade). Menor peso = maior afinidade.
        peso = round(1.0 / afinidade, 2) if afinidade > 0 else float("inf")
        self.adj[u].append({"destino": v, "peso": peso, "ativa": True})

    @classmethod
    def carregar_json(cls, caminho):
        grafo = cls()
        with open(caminho, "r", encoding="utf-8") as f:
            dados = json.load(f)
        for u in dados["usuarios"]:
            grafo.adicionar_usuario(u["id"], u["nome"])
        for c in dados["conexoes"]:
            grafo.adicionar_conexao(c["origem"], c["destino"], c["afinidade"])
        return grafo

    # ALGORITMO EXCLUSIVO: Dijkstra para Caminho Ótimo
    def dijkstra(self, origem, destino):
        heap = [(0.0, origem, [origem])]
        distancias = {origem: 0.0}

        while heap:
            custo_atual, atual, caminho = heapq.heappop(heap)

            if atual == destino:
                rota_nomes = [self.usuarios[uid] for uid in caminho]
                return rota_nomes, round(custo_atual, 2)

            if custo_atual > distancias.get(atual, float("inf")):
                continue

            for aresta in self.adj.get(atual, []):
                if not aresta["ativa"]:
                    continue
                v = aresta["destino"]
                novo_custo = custo_atual + aresta["peso"]
                if novo_custo < distancias.get(v, float("inf")):
                    distancias[v] = novo_custo
                    heapq.heappush(heap, (novo_custo, v, caminho + [v]))

        return None, float("inf")

    # Simulação de Falhas e Recálculo Automático com Dijkstra
    def desativar_conexao(self, u, v):
        for aresta in self.adj.get(u, []):
            if aresta["destino"] == v and aresta["ativa"]:
                aresta["ativa"] = False
                return True
        return False

    def simular_falha(self, origem, destino, corte_u, corte_v):
        print(f"\n[SIMULACAO DE FALHA] Desativando vinculo: {self.usuarios[corte_u]} -> {self.usuarios[corte_v]}")
        self.desativar_conexao(corte_u, corte_v)
        
        # Recálculo imediato da rota alternativa via Dijkstra
        nova_rota, novo_custo = self.dijkstra(origem, destino)
        if nova_rota:
            print(f"  -> Rota alternativa recalculada (Dijkstra): {' -> '.join(nova_rota)}")
            print(f"  -> Distancia Social total acumulada: {novo_custo}")
        else:
            print("  -> Nao ha rota alternativa disponivel! Rede desconexa.")


if __name__ == "__main__":
    # 1. Carga externa de dados (Requisito 2)
    rede = GrafoSocial.carregar_json("dados_exemplo.json")

    # 2. Execução do Cenário 2 do PDF (Caminho Mínimo por Dijkstra: Ana -> Carla)
    print("=== CENARIO 2: ROTA DE MENOR DISTANCIA SOCIAL (DIJKSTRA) ===")
    rota, custo = rede.dijkstra("USR-A", "USR-C")
    print(f"Melhor Rota: {' -> '.join(rota)} | Distancia Social: {custo}")

    # 3. Execução do Cenário 3 do PDF (Bloqueio Bruno -> Carla e Recálculo em tempo real)
    print("\n=== CENARIO 3: BLOQUEIO E RECALCULO AUTOMATICO VIA DIJKSTRA ===")
    rede.simular_falha(origem="USR-A", destino="USR-C", corte_u="USR-B", corte_v="USR-C")
