# Servidor HTTP e ponto de entrada da aplicação de análise de redes.

import html
import json
import os
from email import policy
from email.parser import BytesParser
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

from apresentacao import renderizar
from importacao_dados import importar_arquivo
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
        conteudo = renderizar(grafo, caminho, usuario_perfil=usuario_perfil)
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
                grafo,
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
                status_importacao = importar_arquivo(grafo, arquivos.get("arquivo"))
                self.responder(
                    renderizar(grafo, caminho, status_importacao=status_importacao)
                )
                return
            if acao == "padrao":
                rede_padrao = carregar_grafo()
                grafo.usuarios.clear()
                grafo.usuarios.update(rede_padrao.usuarios)
                grafo.adj.clear()
                grafo.adj.update(rede_padrao.adj)
                resultado = '<p class="msg-ok">Rede de exemplo restaurada.</p>'
                self.responder(
                    renderizar(grafo, caminho, status_importacao=resultado)
                )
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
                grafo,
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


if __name__ == "__main__":
    grafo = carregar_grafo()
    porta = int(os.environ.get("PORT", 5500))
    print(f"Servidor rodando na porta {porta}")
    HTTPServer(("0.0.0.0", porta), ServidorRede).serve_forever()
