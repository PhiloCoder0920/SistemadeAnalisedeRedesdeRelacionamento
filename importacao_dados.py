# Leitura, validação e substituição dos dados importados para a rede.

import csv
import html
import io
import json
import math
from pathlib import Path

from rede_relacionamento import GrafoSocial


# Valida o arquivo enviado e encaminha a importação para o leitor apropriado.
def importar_arquivo(grafo, arquivo):
    if not arquivo:
        return '<p class="msg-erro">Selecione um arquivo CSV ou JSON.</p>'
    nome, conteudo = arquivo
    if Path(nome).suffix.lower() != ".json":
        return importar_csv(grafo, arquivo)
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
    resposta = importar_csv(grafo, (nome + ".csv", linhas.getvalue().encode("utf-8")))
    return resposta.replace(html.escape(nome + ".csv"), html.escape(nome))


# Valida e importa conexões CSV, substituindo o grafo somente se tudo for válido.
def importar_csv(grafo, arquivo):
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

    grafo.usuarios.clear()
    grafo.usuarios.update(nova_rede.usuarios)
    grafo.adj.clear()
    grafo.adj.update(nova_rede.adj)
    return (
        f'<p class="msg-ok"><strong>{html.escape(nome_arquivo)}</strong> importado: '
        f'{len(usuarios)} perfis e {len(conexoes)} conexões. '
        'O grafo atualizado está visível na página Início.</p>'
    )
