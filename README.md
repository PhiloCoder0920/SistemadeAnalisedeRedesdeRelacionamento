# Sistema de Análise de Redes de Relacionamento

Projeto prático de Teoria dos Grafos (Tema 3). Para usar a interface HTML sem JavaScript, inicie o servidor Python:

```powershell
python app.py
```

Abra <http://127.0.0.1:5500>. O modelo existente está em `rede_relacionamento.py`; a interface usa `dados/exemplo-pdf.json`.

## Modelo

Grafo **direcionado e ponderado**: vértices são usuários e arestas `u → v` são relações assimétricas ("u segue v"). Cada aresta tem `afinidade` (maior = mais próximo) e `interacoes`. Nos algoritmos de menor caminho o custo da aresta é `1 / afinidade`.

## Interface

| Página | Conteúdo |
|---|---|
| Início | Métricas da rede, grafo, ranking e conexões desativadas |
| Consultas | Caminho de menor distância social usando Dijkstra |
| Análise | Matriz Floyd-Warshall, componentes fortemente conexos, ciclos e busca DFS |
| Falhas | Bloqueio de conexão e recálculo da rota |
| Perfil | Métricas, seguidores, conexões e vizinhança direta de um perfil |
| Dados | Importação de CSV/JSON e visualização da rede atual |

## Estrutura

- `app.py`: ponto de entrada e servidor HTTP que conecta os formulários ao modelo
- `apresentacao.py`: renderização das páginas, fragmentos HTML e visualização SVG
- `analises.py`: matriz de distâncias, componentes conexos, ciclos e busca de caminhos
- `importacao_dados.py`: validação e importação de arquivos CSV e JSON
- `rede_relacionamento.py`: classe original `GrafoSocial` e algoritmo Dijkstra
- `html/` e `index.html`: páginas da interface
- `css/`: estilos
- `dados/exemplo-pdf.json`: rede carregada pelo servidor

Na página Dados, importe um CSV com cabeçalho `from,to,afinidade` (ou `origem,destino,peso`); `interacoes` é opcional. O grafo importado aparece nas páginas Início e Dados. A importação e os bloqueios ficam ativos enquanto o servidor estiver executando; ao reiniciá-lo, a rede volta ao exemplo.
