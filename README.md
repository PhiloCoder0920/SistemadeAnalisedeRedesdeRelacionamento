# Sistema de Análise de Redes de Relacionamento

Projeto prático de Teoria dos Grafos (Tema 3). Para usar a interface HTML sem JavaScript, inicie o servidor Python:

```powershell
python app.py
```

Abra a aplicação localmente em [http://127.0.0.1:5500](http://127.0.0.1:5500/) ou acesse a versão hospedada no Render em [https://sistemadeanalisederedesderelacionamento.onrender.com/](https://sistemadeanalisederedesderelacionamento.onrender.com/). O modelo existente está em `rede_relacionamento.py`; a interface usa `dados/exemplo-pdf.json`.

## Integrantes

- Eric Joshua Revollo - RA: 1681432612008
- Pedro Henrique Lopes Vilela Coelho - RA: 1681432612032
- Tiago Bondezan Bazani - RA: 1681432612036
- Yuri Shinnishi de Queiroz Rossi - RA: 1681432612038

## Modelo

Grafo **direcionado e ponderado**: vértices são usuários e arestas `u → v` são relações assimétricas ("u segue v"). Cada aresta tem `afinidade` (maior = mais próximo) e `interacoes`. Nos algoritmos de menor caminho o custo da aresta é `1 / afinidade`.

## Requisitos e Instalação

- **Versão do Python:** Python 3.10 ou superior.
- **Sistemas operacionais testados:** Windows e Linux.
- **Dependências:** Caso existam pacotes externos listados em `requirements.txt`, instale-os antes de iniciar o servidor:

```powershell
python -m pip install -r requirements.txt
```

## Exemplos de Uso

- **Consulta de rota (aba Consultas):** Com a rede padrão `dados/exemplo-pdf.json` carregada, selecione origem `Ana` e destino `Carla` e clique em resolver para calcular o caminho de menor distância social (`1 / afinidade`) passando por `Bruno`.
- **Simulação de falha (aba Falhas):** Desative uma conexão ativa para observar o bloqueio na interface e o recálculo automático de rota (quando houver caminho alternativo) ou a indicação de ausência de caminho.
- **Importação de dados (aba Dados):** Importe um CSV com cabeçalho `from,to,afinidade` (ou `origem,destino,peso`); `interacoes` é opcional. O grafo importado aparece nas páginas Início e Dados.

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

## Dados de Teste e Documentação

- **Dados de exemplo e teste:** Pasta `dados/` (incluindo `dados/exemplo-pdf.json` e arquivos de teste utilizados nas validações).
- **Documentação do projeto:** Caderno Técnico e Documento de Casos de Teste na documentação/pasta de entrega do projeto.
