# Sistema de Análise de Redes de Relacionamento

Projeto prático de Teoria dos Grafos (Tema 3). Aplicação web estática (HTML, CSS e JavaScript, sem dependências): abra `index.html` no navegador.

## Modelo

Grafo **direcionado e ponderado**: vértices são usuários e arestas `u → v` são relações assimétricas ("u segue v"). Cada aresta tem `afinidade` (maior = mais próximo) e `interacoes`. Nos algoritmos de menor caminho o custo da aresta é `1 / afinidade`.

## Páginas

| Página | Conteúdo |
|---|---|
| Início | Métricas gerais, grafo e ranking de grau |
| Consultas | Menor grau de separação (BFS) e maior afinidade (Dijkstra), com rota passo a passo |
| Análise | Floyd-Warshall (todos os pares), componentes fortemente conexos (Tarjan), ciclos e cadeias alternativas (DFS) |
| Falhas | Desativa conexões e recalcula a rota automaticamente; permite reativar |
| Perfil | Vizinhança direta de um usuário |
| Dados | Importação JSON/CSV com validação, exportação e restauração da rede padrão |

## Estrutura

- `js/grafo.js`: classe `Grafo`, rede padrão, persistência (`localStorage`) e desenho no canvas
- `js/algoritmos.js`: BFS, Dijkstra, Floyd-Warshall, DFS, ciclos e SCC
- `js/importacao.js`: leitura e validação de JSON/CSV
- `dados/`: arquivos de exemplo para importar (incluem o Exemplo 1 do enunciado)

## Formatos de importação

JSON: `{"profiles": [{"name": "Ana"}], "connections": [{"from": "Ana", "to": "Bruno", "afinidade": 0.9, "interacoes": 150}]}`

CSV: cabeçalho `from,to,afinidade,interacoes` (aceita `;` e os aliases `origem,destino,peso`).

Regras de validação: afinidade maior que 0, sem perfis duplicados, sem perfis órfãos, sem conexões duplicadas ou para si mesmo.
