# Chapeiro Shop: catálogo 3D

Site estático com os 60 modelos (120 variações) das pranchas Básica, Autoral e Premium, Vol. 01 e Vol. 02.
Cada peça abre num visualizador 3D que gira e mostra frente e costas.

## Como rodar

Qualquer servidor estático serve. Por exemplo:

```bash
cd chapeiro-shop
python3 -m http.server 8000
# abra http://localhost:8000
```

Abrir o `index.html` direto do disco (`file://`) não funciona, porque o navegador bloqueia módulos e texturas locais.
No GitHub Pages funciona sem ajuste.

Links diretos: `index.html#A01-a`, `index.html#P16-b` etc.

## Arquivos

| Arquivo | O que tem |
| --- | --- |
| `index.html` | Página, estilos e o mapa de importação do three.js (CDN jsDelivr) |
| `app.js` | Palco do produto, filtros e grade do catálogo |
| `viewer.js` | Visualizador 3D: monta o volume da peça a partir da silhueta da foto |
| `data.js` | Nomes, linhas, modelagens e textos de cada modelo |
| `assets/<código><a\|b>-front.webp` | Textura da frente |
| `assets/<código><a\|b>-back.webp` | Textura das costas (vista por trás, já espelhada) |
| `assets/meta.json` | Cor predominante de cada variação (nome e hex) |
| `tools/` | Scripts que recortaram as peças das pranchas e geraram as texturas |

## Sobre o lado que não aparece na prancha

As pranchas mostram só um lado de cada peça. O outro lado foi gerado:

- Peças mostradas de frente ganham costas lisas na cor do tecido, com as dobras da foto e a assinatura "CHAPEIRO 303" abaixo da gola.
- Peças mostradas de costas (A02, A11, A16, P10, P11, P16) ganham uma frente lisa com o ícone em órbita no peito.
- Peças de estampa total (A03, A19, P03) repetem o padrão nas costas.

Quando existirem fotos reais das costas, basta substituir o arquivo `-back.webp` correspondente (mesmo tamanho e silhueta espelhada).

## Qualidade das texturas

Cada camiseta ocupa cerca de 230 px de largura nas pranchas, então as texturas foram ampliadas 2x.
Para o site final, vale exportar cada peça em alta resolução, frente e costas, com fundo transparente, e rodar `tools/` de novo.
