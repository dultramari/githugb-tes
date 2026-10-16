# BADD · Árvore da Vida 2022 — Prévia 3 (nível 2)

`BADD_2022_PREVIA_3_NIVEL2_1080.mp4` — 1080x1080, 25 fps, H.264, áudio AAC normalizado em -14 LUFS.

## O que mudou em relação ao original (720x720)
- **Layout fixo**: a imagem fica sempre na mesma faixa 16:9, com filetes finos e luz ambiente com as cores da cena no fundo (o original alternava entre faixa e tela cheia).
- **Tipografia nova**: narração em serifada (Instrument Serif) entrando palavra a palavra; frases de impacto em condensada (Anton) com revelação por máscara; frases emocionais em itálico âmbar com brilho suave.
- **Títulos**: "BADD" e "Por trás do set" redesenhados sobre a imagem desfocada (os textos que estavam queimados no vídeo ficam escondidos no desfoque).
- **Imagem**: redução de ruído de compressão, upscale lanczos, nitidez leve, curva de contraste fílmica, sombras frias e altas quentes, vinheta e grão de filme.
- **Moldura**: cabeçalho (Chapeiro Chapado / Acervo 2022), rodapé (EP. 01) e barra de progresso discreta.
- **Áudio**: de -24,6 LUFS para -14 LUFS (pico -1 dBTP), com fade de entrada e saída.

## Como renderizar de novo
```
python3 render.py video_original.mp4 master.mp4
python3 render.py video_original.mp4 x --frames 10,44 --preview-dir prev   # só quadros de teste
```
Requer ffmpeg, Python 3, Pillow e NumPy. Fontes em `fonts/` (Instrument Serif e Anton, licença SIL OFL) e Inter do sistema.
