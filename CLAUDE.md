# Contexto para o Claude

Este repositório guarda a série de vídeos **"Por trás do set"** (Chapeiro Chapado · Árvore da
Vida 2026), um episódio por dia. **Tudo fica em `serie/`. Leia `serie/README.md` antes de qualquer coisa.**

Regras:
- Quando o usuário mandar um vídeo novo, ele quer o **próximo episódio no mesmo padrão**. Siga o
  passo a passo de `serie/README.md`: analisar.py → episodio.json → quadros de teste → render.
- **Não mude o padrão visual** (`serie/marca/`, layout, fontes, cores, estrutura do fechamento)
  sem pedido explícito. Se o usuário pedir uma mudança de padrão, aplique em `marca.json` / `motor/`
  e avise que ela vale para os episódios seguintes (e se os anteriores devem ser re-renderizados).
- Imagens são de 2022 (narração e "ACERVO 2022" dizem 2022); o fechamento anuncia a edição 2026.
- Antes de entregar, confira visualmente quadros perto do título do artista e da cartela final:
  nenhum texto queimado do original pode aparecer.
- A entrega precisa ficar abaixo de 100 MB (limite do GitHub). O master não vai para o git.
- O usuário prefere respostas diretas, em português, começando pelo ponto crítico.
