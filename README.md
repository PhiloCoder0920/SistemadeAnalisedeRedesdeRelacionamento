# Sistema de Análise de Redes de Relacionamento

Projeto prático de Teoria dos Grafos (Tema 3). A interface HTML não usa JavaScript.

## Executar localmente

```powershell
python app.py
```

Abra <http://127.0.0.1:5500>. O modelo existente está em `rede_relacionamento.py`; a interface usa `dados/exemplo-pdf.json`.

## Publicar no Vercel

O Vercel executa o app Flask em `app.py`; não publique apenas os arquivos HTML como site estático. Para manter a rede importada entre requisições:

1. Em **Storage** no projeto Vercel, crie e conecte um Vercel Blob **privado** ao projeto.
2. Confirme que a conexão disponibiliza `BLOB_STORE_ID` e autenticação OIDC para as funções Python.
3. Faça um novo deploy após enviar os arquivos deste repositório.

O conteúdo da rede fica salvo em `rede-atual.json` no Blob. Arquivos CSV/JSON importados são limitados a 4 MB. **Sem senha de administrador, qualquer visitante pode importar, bloquear ou restaurar a rede do site.**

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

- `app.py`: app Flask para Vercel e servidor local que conecta os formulários HTML ao modelo Python
- `requirements.txt`: dependências Flask e Vercel Blob
- `rede_relacionamento.py`: classe original `GrafoSocial` e algoritmo Dijkstra
- `html/` e `index.html`: páginas da interface
- `css/`: estilos
- `dados/exemplo-pdf.json`: rede carregada pelo servidor

Na página Dados, importe um CSV com cabeçalho `from,to,afinidade` (ou `origem,destino,peso`); `interacoes` é opcional. O grafo importado aparece nas páginas Início e Dados. Localmente, importações e bloqueios duram enquanto o servidor estiver executando. No Vercel, são persistidos no Blob conectado ao projeto.
