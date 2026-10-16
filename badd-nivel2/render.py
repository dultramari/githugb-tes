#!/usr/bin/env python3
"""BADD · Árvore da Vida 2022 — prévia 3, nível 2.

Recompõe o vídeo original (720x720, com textos queimados) em 1080x1080:
  - recorta só a faixa de imagem 16:9 (fora das legendas antigas),
  - aplica tratamento de cor, nitidez e grão de filme,
  - redesenha toda a tipografia com animação (serifada para a narração,
    condensada para as frases de impacto, itálico âmbar para as emoções),
  - desfoca a imagem nos dois títulos centrais que estavam queimados na faixa,
  - normaliza o áudio para -14 LUFS (padrão de redes sociais).

Uso: python3 render.py <video_original.mp4> <saida.mp4> [--frames 10.5,44] [--preview-dir dir]
"""
import argparse
import math
import os
import subprocess
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
FONTS = os.path.join(HERE, "fonts")

W = H = 1080
FPS = 25
BAND_Y, BAND_H = 240, 600          # faixa de imagem 16:9 no quadro final
SRC_CROP = "crop=720:400:0:160"    # área 16:9 do original, sem as linhas laranja

WHITE = (244, 240, 232)
AMBER = (242, 166, 64)
BASE = (9, 9, 10)


def font(name, size):
    paths = {
        "serif": os.path.join(FONTS, "InstrumentSerif-Regular.ttf"),
        "serif-i": os.path.join(FONTS, "InstrumentSerif-Italic.ttf"),
        "anton": os.path.join(FONTS, "Anton.ttf"),
        "label": "/usr/share/fonts/opentype/inter/Inter-Medium.otf",
        "label-b": "/usr/share/fonts/opentype/inter/InterDisplay-SemiBold.otf",
    }
    return ImageFont.truetype(paths[name], size)


# ---------------------------------------------------------------- easing
def clamp(x, a=0.0, b=1.0):
    return max(a, min(b, x))


def ease_out_cubic(x):
    x = clamp(x)
    return 1 - (1 - x) ** 3


def ease_out_expo(x):
    x = clamp(x)
    return 1.0 if x >= 1 else 1 - 2 ** (-10 * x)


def ease_in_out(x):
    x = clamp(x)
    return x * x * (3 - 2 * x)


# ---------------------------------------------------------------- texto
def text_width(txt, f, tracking):
    if not txt:
        return 0
    return sum(f.getlength(c) for c in txt) + tracking * (len(txt) - 1)


def render_text(txt, f, color, tracking=0.0, alpha=255):
    """Desenha uma linha com espaçamento entre letras; retorna RGBA recortado."""
    asc, desc = f.getmetrics()
    pad = int(f.size * 0.25)
    w = int(math.ceil(text_width(txt, f, tracking))) + pad * 2
    h = asc + desc + pad * 2
    im = Image.new("RGBA", (max(w, 1), h), (0, 0, 0, 0))
    d = ImageDraw.Draw(im)
    x = pad
    for c in txt:
        d.text((x, pad), c, font=f, fill=color + (alpha,))
        x += f.getlength(c) + tracking
    return im, pad


def wrap(txt, f, max_w, tracking=0.0):
    """Quebra equilibrada: evita palavra órfã na última linha."""
    out = []
    for para in txt.split("\n"):
        words = para.split(" ")
        if text_width(para, f, tracking) <= max_w:
            out.append(para)
            continue
        best = min(range(1, len(words)),
                   key=lambda i: max(text_width(" ".join(words[:i]), f, tracking),
                                     text_width(" ".join(words[i:]), f, tracking)))
        out += [" ".join(words[:best]), " ".join(words[best:])]
    return out


def wrap_greedy(txt, f, max_w, tracking=0.0):
    lines = []
    for para in txt.split("\n"):
        cur = ""
        for word in para.split(" "):
            test = (cur + " " + word).strip()
            if text_width(test, f, tracking) <= max_w or not cur:
                cur = test
            else:
                lines.append(cur)
                cur = word
        lines.append(cur)
    return lines


def paste(canvas, im, x, y, opacity=1.0):
    if opacity <= 0.003:
        return
    if opacity < 1:
        a = im.getchannel("A").point(lambda v: int(v * opacity))
        im = im.copy()
        im.putalpha(a)
    canvas.alpha_composite(im, (int(round(x)), int(round(y))))


_cache = {}


def cached(key, fn):
    if key not in _cache:
        _cache[key] = fn()
    return _cache[key]


# ---------------------------------------------------------------- cues
# Tempos ajustados aos do original para manter a sincronia com a trilha.
NARRATION = [  # topo, serifada, entrada palavra a palavra
    (0.90, 4.40, "Tem noites que não acabam quando a música para."),
    (5.00, 8.60, "Elas continuam vivendo dentro da gente."),
    (9.00, 12.80, "Em 2022, na Árvore da Vida,"),
    (13.00, 16.10, "milhares de caminhos se cruzaram por um mesmo motivo."),
    (17.00, 19.90, "E quando BADD encontrou aquela pista,"),
    (20.00, 21.90, "o que se ouviu foi muito mais que música."),
    (42.00, 45.90, "Olha de novo. Não são apenas pessoas dançando."),
    (46.90, 50.90, "São histórias, abraços e lembranças que não se apagam."),
    (51.90, 55.60, "Porque a festa termina…\nmas o que a gente sente, fica."),
]

STATEMENTS = [  # base, condensada (impacto) ou itálico âmbar (emoção)
    (0.40, 4.50, "NÃO É SÓ UMA FESTA.", "impact"),
    (5.00, 8.90, "É um sentimento.", "feel"),
    (10.90, 14.00, "ÁRVORE DA VIDA  ·  2022", "stamp"),
    (22.00, 24.30, "Foi conexão.", "feel"),
    (43.00, 48.40, "UMA PISTA. MIL HISTÓRIAS.", "impact"),
    (49.00, 53.30, "O sentimento fica.", "feel"),
]

TITLE = (13.65, 18.35)       # "BADD" — queimado no original de ~13.8 a ~18.2 (com fades)
END = (53.05, 57.20)         # cartela final — "POR TRÁS DO SET" queimado a partir de ~53.2
STING = (57.20, 58.60)       # corte rápido para a marca Chapeiro Chapado, entra junto com o drop
LINEUP = (58.60, 63.60)      # line-up da edição 2026, 5 s
DURATION = LINEUP[1]
DROP_AT = 24.79              # ataque do drop na trilha original; toca sob a marca e a line-up
POSTER = os.path.join(HERE, "assets", "lineup_2026.png")
BADD_ROW = (128, 639, 588, 674)  # linha "13:00 BADD" no pôster (px do original 1254x1254)


def env(t, t0, t1, fin=0.5, fout=0.35):
    """Envelope de entrada/saída 0..1."""
    if t < t0 or t > t1:
        return 0.0
    return min(ease_out_cubic((t - t0) / fin), ease_in_out((t1 - t) / fout))


# ---------------------------------------------------------------- camadas
NARR_SIZE, NARR_LH, NARR_MAXW = 46, 52, 860
NARR_CY = 158


def draw_narration(canvas, t):
    f = font("serif", NARR_SIZE)
    for t0, t1, txt in NARRATION:
        if not (t0 <= t <= t1):
            continue
        lines = cached(("wrap", txt), lambda: wrap(txt, f, NARR_MAXW))
        out = ease_in_out((t1 - t) / 0.4)
        top = NARR_CY - len(lines) * NARR_LH / 2
        k = 0
        for li, line in enumerate(lines):
            words = line.split(" ")
            space = f.getlength(" ")
            lw = sum(f.getlength(w) for w in words) + space * (len(words) - 1)
            x = (W - lw) / 2
            for w in words:
                p = (t - t0 - k * 0.055) / 0.6
                a = ease_out_cubic(p) * out
                if a > 0:
                    blur = round((1 - ease_out_cubic(p)) * 6)
                    def mk(w=w, blur=blur):
                        im, pad = render_text(w, f, WHITE)
                        if blur:
                            im = im.filter(ImageFilter.GaussianBlur(blur))
                        return im, pad
                    im, pad = cached(("nw", w, blur), mk)
                    dy = (1 - ease_out_cubic(p)) * 14
                    paste(canvas, im, x - pad, top + li * NARR_LH - pad - 6 + dy, a * 0.94)
                x += f.getlength(w) + space
                k += 1


STMT_CY = 952


def draw_statements(canvas, t):
    for t0, t1, txt, kind in STATEMENTS:
        if not (t0 <= t <= t1):
            continue
        if kind == "impact":
            f = font("anton", 74)
            tr = 2.0
            out = ease_in_out((t1 - t) / 0.35)
            words = txt.split(" ")
            space = f.getlength(" ") + tr * 2
            total = sum(text_width(w, f, tr) for w in words) + space * (len(words) - 1)
            x = (W - total) / 2
            asc, desc = f.getmetrics()
            for i, w in enumerate(words):
                im, pad = cached(("imp", w), lambda w=w: render_text(w, f, WHITE, tr))
                p = ease_out_expo((t - t0 - i * 0.07) / 0.7)
                # revelação por máscara: a palavra sobe por trás de uma linha de corte
                box_h = asc + pad
                off = int((1 - p) * box_h)
                if off < box_h:
                    clip = im.crop((0, 0, im.width, box_h - off + pad))
                    paste(canvas, clip, x - pad, STMT_CY - asc / 2 - pad + off - 4, out)
                x += text_width(w, f, tr) + space
        elif kind == "feel":
            f = font("serif-i", 84)
            p = (t - t0) / 1.1
            e = ease_out_cubic(p)
            out = ease_in_out((t1 - t) / 0.45)
            tr = round((1 - e) * 14, 1)
            blur = round((1 - e) * 10 + (1 - out) * 6)
            im, pad = cached(("feel", txt, tr, blur), lambda: _feel(txt, f, tr, blur))
            asc, _ = f.getmetrics()
            paste(canvas, im, (W - im.width) / 2, STMT_CY - asc / 2 - pad - 4, e * out)
        elif kind == "stamp":
            f = font("label", 19)
            a = env(t, t0, t1, 0.6, 0.4)
            im, pad = cached(("stamp", txt), lambda: render_text(txt, f, WHITE, 7.0))
            cy = STMT_CY
            paste(canvas, im, (W - im.width) / 2, cy - 14 - pad, a * 0.75)
            # filetes laterais que crescem a partir do texto
            g = ease_out_expo((t - t0) / 1.0)
            half = im.width / 2 - pad + 26
            ln = 90 * g
            d = ImageDraw.Draw(canvas)
            col = AMBER + (int(200 * a),)
            d.line([(W / 2 - half - ln, cy), (W / 2 - half, cy)], fill=col, width=1)
            d.line([(W / 2 + half, cy), (W / 2 + half + ln, cy)], fill=col, width=1)


def _feel(txt, f, tr, blur):
    im, pad = render_text(txt, f, AMBER, tr)
    glow = im.filter(ImageFilter.GaussianBlur(14))
    ga = glow.getchannel("A").point(lambda v: int(v * 0.35))
    glow.putalpha(ga)
    out = Image.new("RGBA", im.size, (0, 0, 0, 0))
    out.alpha_composite(glow)
    out.alpha_composite(im)
    if blur:
        out = out.filter(ImageFilter.GaussianBlur(blur))
    return out, pad


def draw_chrome(canvas, t, end_k):
    """Cabeçalho, rodapé e barra de progresso."""
    a = ease_out_cubic((t - 0.2) / 1.0) * (1 - end_k)
    if a <= 0:
        return
    fl = font("label", 15)
    fb = font("label-b", 15)
    left, pl = cached("h-l", lambda: render_text("CHAPEIRO CHAPADO", fb, WHITE, 4.5))
    right, pr = cached("h-r", lambda: render_text("ACERVO 2022", fl, WHITE, 4.5))
    paste(canvas, left, 64 - pl, 58 - pl, a * 0.78)
    paste(canvas, right, W - 64 - right.width + pr, 58 - pr, a * 0.5)
    fl2, pl2 = cached("f-l", lambda: render_text("EP. 01", fb, WHITE, 4.5))
    fr2, pr2 = cached("f-r", lambda: render_text("BADD  ·  POR TRÁS DO SET", fl, WHITE, 4.5))
    paste(canvas, fl2, 64 - pl2, 1032 - pl2, a * 0.7)
    paste(canvas, fr2, W - 64 - fr2.width + pr2, 1032 - pr2, a * 0.42)
    d = ImageDraw.Draw(canvas)
    # barra de progresso discreta sob o cabeçalho
    x0, x1, y = 64, W - 64, 92
    d.line([(x0, y), (x1, y)], fill=(255, 255, 255, int(28 * a)), width=1)
    px = x0 + (x1 - x0) * clamp(t / DURATION)
    d.line([(x0, y), (px, y)], fill=AMBER + (int(190 * a),), width=1)


def draw_title(canvas, t):
    t0, t1 = TITLE
    a = env(t, t0 + 0.15, t1 - 0.1, 0.7, 0.45)
    if a <= 0:
        return
    f = font("anton", 210)
    prog = clamp((t - t0) / (t1 - t0))
    tr = round(64 - 34 * ease_out_cubic(prog), 0)   # tracking fecha devagar
    blur = round((1 - ease_out_cubic((t - t0 - 0.15) / 0.8)) * 14)
    im, pad = cached(("title", tr, blur), lambda: _title(f, tr, blur))
    cy = BAND_Y + BAND_H / 2 - 28
    asc, _ = f.getmetrics()
    paste(canvas, im, (W - im.width) / 2 + tr / 2, cy - asc / 2 - pad - 10, a)
    fs = font("label", 18)
    sub, sp = cached("title-sub", lambda: render_text("AO VIVO  ·  ÁRVORE DA VIDA", fs, WHITE, 8.0))
    sa = env(t, t0 + 0.8, t1 - 0.1, 0.7, 0.4)
    paste(canvas, sub, (W - sub.width) / 2, cy + asc / 2 + 10 - sp, sa * 0.85)


def _title(f, tr, blur):
    im, pad = render_text("BADD", f, WHITE, tr)
    if blur:
        im = im.filter(ImageFilter.GaussianBlur(blur))
    return im, pad


def draw_end(canvas, t):
    t0, t1 = END
    fk = font("label-b", 17)
    ft = font("serif-i", 132)
    fs = font("label", 16)
    k1 = env(t, t0 + 0.55, t1, 0.9, 0.06)
    k2 = env(t, t0 + 0.25, t1, 0.7, 0.06)
    k3 = env(t, t0 + 1.2, t1, 0.8, 0.06)
    cy = BAND_Y + BAND_H / 2
    ep, pe = cached("end-ep", lambda: render_text("EPISÓDIO 01", fk, AMBER, 9.0))
    paste(canvas, ep, (W - ep.width) / 2 + 4, cy - 118 - pe, k2)
    p = ease_out_cubic((t - t0 - 0.55) / 1.4)
    blur = round((1 - p) * 12)
    tr = round((1 - p) * 10, 1)
    im, pad = cached(("end-t", tr, blur), lambda: _end_title(ft, tr, blur))
    asc, _ = ft.getmetrics()
    paste(canvas, im, (W - im.width) / 2, cy - asc / 2 - pad - 4, k1)
    cr, pc = cached("end-cr", lambda: render_text("ÁRVORE DA VIDA 2026  ·  14 E 15 NOV", fs, WHITE, 7.0))
    paste(canvas, cr, (W - cr.width) / 2 + 3, cy + 112 - pc, k3 * 0.7)
    d = ImageDraw.Draw(canvas)
    ln = 60 * ease_out_expo((t - t0 - 1.0) / 1.0)
    d.line([(W / 2 - ln, cy + 90), (W / 2 + ln, cy + 90)], fill=AMBER + (int(180 * k3),), width=1)


def _end_title(f, tr, blur):
    im, pad = render_text("Por trás do set", f, WHITE, tr)
    if blur:
        im = im.filter(ImageFilter.GaussianBlur(blur))
    return im, pad


# ---------------------------------------------------------------- imagem
def make_grain(n=10, seed=7):
    rng = np.random.default_rng(seed)
    tiles = []
    for _ in range(n):
        g = rng.normal(0, 1, (H // 2, W // 2)).astype(np.float32)
        g = np.asarray(Image.fromarray(g, "F").resize((W, H), Image.BILINEAR))
        tiles.append(g)
    return tiles


def make_vignette(w, h, strength):
    y, x = np.mgrid[0:h, 0:w].astype(np.float32)
    nx, ny = (x - w / 2) / (w / 2), (y - h / 2) / (h / 2)
    r = np.sqrt(nx ** 2 * 0.8 + ny ** 2)
    return (1 - strength * np.clip(r - 0.35, 0, None) ** 1.6)[..., None]


def band_stream(src):
    vf = ",".join([
        SRC_CROP,
        "hqdn3d=2:1.5:3:3",
        "scale=1080:600:flags=lanczos",
        "unsharp=5:5:0.55:5:5:0",
        # contraste fílmico, pretos levemente erguidos, sombras frias e altas quentes
        "curves=master='0/0.035 0.25/0.21 0.5/0.5 0.78/0.81 1/0.97'",
        "colorbalance=rs=-0.04:gs=0.0:bs=0.05:rh=0.04:gh=0.01:bh=-0.04",
        "eq=saturation=1.07",
    ])
    cmd = ["ffmpeg", "-v", "error", "-i", src, "-vf", vf, "-f", "rawvideo", "-pix_fmt", "rgb24", "-"]
    return subprocess.Popen(cmd, stdout=subprocess.PIPE)


def gaussian_np(arr, sigma):
    if sigma < 0.5:
        return arr
    im = Image.fromarray(arr)
    # reduz antes de desfocar: mais rápido e mais macio
    s = 4
    small = im.resize((im.width // s, im.height // s), Image.BILINEAR)
    small = small.filter(ImageFilter.GaussianBlur(sigma / s))
    return np.asarray(small.resize(im.size, Image.BILINEAR))


def compose(band, t, grain, vig_band, vig_full):
    # quanto a faixa é desfocada/escurecida (títulos centrais e final)
    t0, t1 = TITLE
    k_title = min(ease_in_out((t - (t0 - 0.05)) / 0.3), ease_in_out((t1 + 0.15 - t) / 0.35)) if t0 - 0.05 <= t <= t1 + 0.15 else 0.0
    e0, e1 = END
    k_end = ease_in_out((t - (e0 - 0.05)) / 0.4) if t >= e0 - 0.05 else 0.0
    k_blur = max(k_title, k_end)

    b = band
    if k_blur > 0:
        b = gaussian_np(band, 34 * k_blur).astype(np.float32)
        b = b * (1 - 0.45 * k_title - 0.35 * k_end)
        b = np.clip(b, 0, 255).astype(np.uint8)

    # fundo: luz ambiente com as cores da cena
    amb = Image.fromarray(band).resize((24, 14), Image.BILINEAR).resize((W, H), Image.BILINEAR)
    amb = np.asarray(amb).astype(np.float32) * 0.16
    canvas = np.empty((H, W, 3), np.float32)
    canvas[:] = BASE
    canvas += amb * vig_full

    bf = b.astype(np.float32) * vig_band
    # fade de entrada da imagem e escurecimento final
    fade_in = ease_out_cubic(t / 0.9)
    fade_end = 1 - 0.78 * ease_in_out((t - (e0 + 0.2)) / 1.6) if t > e0 else 1.0
    bf *= fade_in * fade_end
    canvas[BAND_Y:BAND_Y + BAND_H] = bf + canvas[BAND_Y:BAND_Y + BAND_H] * 0.0

    img = Image.fromarray(np.clip(canvas, 0, 255).astype(np.uint8)).convert("RGBA")
    d = ImageDraw.Draw(img)
    hl = int(34 * fade_in)
    d.line([(0, BAND_Y - 1), (W, BAND_Y - 1)], fill=(255, 255, 255, hl), width=1)
    d.line([(0, BAND_Y + BAND_H), (W, BAND_Y + BAND_H)], fill=(255, 255, 255, hl), width=1)

    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    draw_chrome(overlay, t, ease_in_out((t - END[0]) / 0.6))
    draw_narration(overlay, t)
    draw_statements(overlay, t)
    draw_title(overlay, t)
    draw_end(overlay, t)
    img.alpha_composite(overlay)

    out = np.asarray(img.convert("RGB")).astype(np.float32)
    g = grain[int(t * FPS) % len(grain)]
    lum = out.mean(2, keepdims=True) / 255.0
    out += g[..., None] * (5.5 + 4.0 * (1 - lum))   # grão mais visível nas sombras
    # fade geral de entrada
    master = ease_out_cubic(t / 0.5)
    out *= master
    return np.clip(out, 0, 255).astype(np.uint8)


# ---------------------------------------------------------------- final: marca + line-up
_poster = None


def poster():
    global _poster
    if _poster is None:
        _poster = Image.open(POSTER).convert("RGB")
    return _poster


def logo():
    def mk():
        im = poster().crop((90, 50, 350, 222)).convert("RGBA")
        im = im.resize((im.width * 2, im.height * 2), Image.LANCZOS)
        # recorte pelo brilho: o fundo do logo no pôster é quase preto
        rgb = np.asarray(im.convert("RGB")).astype(np.float32)
        a = np.clip((rgb.max(2) - 30) / 100, 0, 1)
        edge = Image.new("L", im.size, 0)
        ImageDraw.Draw(edge).rectangle((14, 10, im.width - 14, im.height - 10), fill=255)
        edge = np.asarray(edge.filter(ImageFilter.GaussianBlur(10))) / 255.0
        im.putalpha(Image.fromarray((a * edge * 255).astype(np.uint8)))
        return im
    return cached("logo", mk)


def compose_sting(t):
    t0, t1 = STING
    lt = t - t0
    canvas = Image.new("RGBA", (W, H), BASE + (255,))
    # brilho magenta/laranja da identidade, respirando no ritmo
    glow = cached("sting-glow", lambda: _sting_glow())
    paste(canvas, glow, 0, 0, 0.75 + 0.25 * math.cos(lt / 0.42 * 2 * math.pi))
    lg = logo()
    s = 1.0 + 0.14 * (1 - ease_out_expo(lt / 0.45)) + 0.02 * lt
    blur = round((1 - ease_out_expo(lt / 0.3)) * 8)
    im = lg.resize((int(lg.width * s), int(lg.height * s)), Image.BICUBIC)
    if blur:
        im = im.filter(ImageFilter.GaussianBlur(blur))
    paste(canvas, im, (W - im.width) / 2, 470 - im.height / 2, ease_out_cubic(lt / 0.12))
    f = font("label", 17)
    tag, pt = cached("sting-tag", lambda: render_text("MÚSICA  ·  ARTE  ·  CONEXÃO  ·  LIBERDADE", f, WHITE, 7.0))
    a = ease_out_cubic((lt - 0.25) / 0.4)
    paste(canvas, tag, (W - tag.width) / 2, 690 - pt + (1 - a) * 10, a * 0.72)
    d = ImageDraw.Draw(canvas)
    ln = 70 * ease_out_expo((lt - 0.3) / 0.6)
    d.line([(W / 2 - ln, 660), (W / 2 + ln, 660)], fill=AMBER + (int(190 * a),), width=1)
    flash(canvas, lt, 0.4)
    return canvas


def _sting_glow():
    y, x = np.mgrid[0:H, 0:W].astype(np.float32)
    r1 = np.exp(-(((x - 420) / 420) ** 2 + ((y - 470) / 300) ** 2))
    r2 = np.exp(-(((x - 700) / 380) ** 2 + ((y - 520) / 280) ** 2))
    rgb = (r1[..., None] * np.array([255, 40, 150]) * 0.16 + r2[..., None] * np.array([255, 120, 30]) * 0.10)
    a = np.full((H, W, 1), 255, np.float32)
    return Image.fromarray(np.clip(np.concatenate([rgb + BASE, a], 2), 0, 255).astype(np.uint8), "RGBA")


def flash(canvas, lt, strength):
    a = strength * (1 - ease_out_cubic(lt / 0.16))
    if a > 0.01:
        canvas.alpha_composite(Image.new("RGBA", (W, H), (255, 246, 236, int(255 * a))))


def compose_lineup(t):
    t0, t1 = LINEUP
    lt = t - t0
    src = poster()
    k = W / src.width
    s = 1.0 + 0.07 * (1 - ease_out_expo(lt / 0.7)) + 0.022 * ease_in_out(lt / (t1 - t0))
    ax, ay = W / 2, H * 0.62                      # ancora no meio da timeline
    sk = s * k
    img = src.transform((W, H), Image.AFFINE,
                        (1 / sk, 0, ax / k - ax / sk, 0, 1 / sk, ay / k - ay / sk),
                        resample=Image.BICUBIC).convert("RGBA")
    # destaque na linha do BADD: contorno âmbar que pulsa duas vezes
    x0, y0, x1, y1 = [(v - (ax / k if i % 2 == 0 else ay / k)) * sk + (ax if i % 2 == 0 else ay)
                      for i, v in enumerate(BADD_ROW)]
    hk = ease_out_cubic((lt - 0.9) / 0.4) * ease_in_out((t1 - 0.6 - t) / 0.5)
    if hk > 0:
        pulse = 0.65 + 0.35 * math.cos((lt - 0.9) / 0.84 * 2 * math.pi)
        box = (x0 - 5, y0 - 4, x1 + 5, y1 + 4)
        # ilumina a linha
        fill = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        ImageDraw.Draw(fill).rounded_rectangle(box, radius=10, fill=(255, 214, 150, 255))
        paste(img, fill, 0, 0, hk * 0.16 * pulse)
        ov = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        ImageDraw.Draw(ov).rounded_rectangle(box, radius=10, outline=(255, 226, 170, 255), width=4)
        glow = ov.filter(ImageFilter.GaussianBlur(12))
        for _ in range(2):
            paste(img, glow, 0, 0, hk * pulse)
        paste(img, ov, 0, 0, hk)
        # selo à direita da linha
        f = font("label-b", 13)
        tag, pt = cached("lu-tag", lambda: render_text("NESTE VÍDEO", f, (20, 12, 8), 2.6))
        tw, th = tag.width - pt * 2, 13
        bx1 = box[2] - 12
        bx0 = bx1 - tw - 22
        cy = (box[1] + box[3]) / 2
        pill = Image.new("RGBA", (W, H), (0, 0, 0, 0))
        ImageDraw.Draw(pill).rounded_rectangle((bx0, cy - 12, bx1, cy + 12), radius=12, fill=AMBER + (255,))
        pill.alpha_composite(tag, (int(bx0 + 11 - pt), int(cy - th / 2 - pt - 3)))
        ta = ease_out_cubic((lt - 1.2) / 0.35) * ease_in_out((t1 - 0.6 - t) / 0.5)
        paste(img, pill, 0, 0, ta)
    flash(img, lt, 0.35)
    return img


def finish(img, t, grain, amount):
    out = np.asarray(img.convert("RGB")).astype(np.float32)
    g = grain[int(t * FPS) % len(grain)]
    lum = out.mean(2, keepdims=True) / 255.0
    out += g[..., None] * amount * (1.0 + 0.7 * (1 - lum))
    out *= ease_in_out((DURATION - t) / 0.7)
    return np.clip(out, 0, 255).astype(np.uint8)


def build_audio(src, dst):
    """Trilha original até o corte + drop da própria trilha sob a marca e a line-up."""
    tail = DURATION - STING[0]
    fc = (f"[0:a]atrim=0:{STING[0]},asetpts=PTS-STARTPTS,afade=t=out:st={STING[0] - 0.06}:d=0.06[a1];"
          f"[0:a]atrim={DROP_AT}:{DROP_AT + tail},asetpts=PTS-STARTPTS,"
          f"afade=t=in:d=0.012,afade=t=out:st={tail - 1.9}:d=1.9,volume=-4dB[a2];"
          f"[a1][a2]concat=n=2:v=0:a=1[a]")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", src, "-filter_complex", fc, "-map", "[a]",
                    "-c:a", "pcm_s24le", dst], check=True)


def loudnorm_filter(src):
    """Primeira passada do loudnorm para medir o áudio."""
    import json
    r = subprocess.run(["ffmpeg", "-hide_banner", "-i", src, "-af",
                        "loudnorm=I=-14:TP=-1.0:LRA=11:print_format=json", "-f", "null", "-"],
                       capture_output=True, text=True)
    js = r.stderr[r.stderr.rfind("{"):r.stderr.rfind("}") + 1]
    m = json.loads(js)
    return ("loudnorm=I=-14:TP=-1.0:LRA=11:measured_I={input_i}:measured_TP={input_tp}:"
            "measured_LRA={input_lra}:measured_thresh={input_thresh}:offset={target_offset}:linear=true"
            ).format(**m)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("src")
    ap.add_argument("out")
    ap.add_argument("--frames", help="só renderiza quadros nesses tempos (s), separados por vírgula")
    ap.add_argument("--preview-dir", default=".")
    args = ap.parse_args()

    grain = make_grain()
    vig_band = make_vignette(W, BAND_H, 0.55)
    vig_full = make_vignette(W, H, 0.9)
    want = None
    if args.frames:
        want = {int(round(float(x) * FPS)) for x in args.frames.split(",")}

    proc = band_stream(args.src)
    enc = None
    if want is None:
        audio = os.path.splitext(args.out)[0] + "_audio.wav"
        build_audio(args.src, audio)
        enc = subprocess.Popen([
            "ffmpeg", "-v", "error", "-y",
            "-f", "rawvideo", "-pix_fmt", "rgb24", "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-",
            "-i", audio,
            "-map", "0:v", "-map", "1:a",
            "-af", loudnorm_filter(audio) + ",afade=t=in:d=0.3",
            "-c:v", "libx264", "-preset", "slow", "-crf", "16", "-tune", "film",
            "-profile:v", "high", "-pix_fmt", "yuv420p", "-x264-params", "aq-mode=3",
            "-color_primaries", "bt709", "-color_trc", "bt709", "-colorspace", "bt709",
            "-c:a", "aac", "-b:a", "256k", "-ar", "48000",
            "-movflags", "+faststart", "-shortest", args.out,
        ], stdin=subprocess.PIPE)

    fsize = 1080 * 600 * 3
    total = int(round(DURATION * FPS))
    band = None
    for n in range(total):
        t = n / FPS
        if t < STING[0]:
            buf = proc.stdout.read(fsize)
            if len(buf) == fsize:
                band = np.frombuffer(buf, np.uint8).reshape(600, 1080, 3)
        if want is None or n in want:
            if t >= LINEUP[0]:
                frame = finish(compose_lineup(t), t, grain, 2.5)
            elif t >= STING[0]:
                frame = finish(compose_sting(t), t, grain, 5.0)
            else:
                frame = compose(band, t, grain, vig_band, vig_full)
            if enc:
                enc.stdin.write(frame.tobytes())
            else:
                Image.fromarray(frame).save(os.path.join(args.preview_dir, f"prev_{t:05.2f}.png"))
        if n % 100 == 0:
            print(f"\r{t:5.1f}s", end="", file=sys.stderr, flush=True)
    proc.stdout.close()
    proc.wait()
    if enc:
        enc.stdin.close()
        enc.wait()
        os.remove(audio)
    print(f"\n{total} quadros", file=sys.stderr)


if __name__ == "__main__":
    main()
