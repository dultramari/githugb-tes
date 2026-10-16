#!/usr/bin/env python3
"""Análise de um vídeo novo do acervo, antes de montar o episodio.json.

Gera em <episodio>/analise/:
  - folhas de contato (1 quadro por segundo, com o tempo) para ler as legendas antigas,
  - relatório com: linhas da faixa 16:9, janelas de texto queimado no centro da faixa,
    envelope de volume a cada 0,5 s e candidatos a drop.

ATENÇÃO: textos com fade enganam a detecção (no EP01 o "BADD" foi detectado de 14,28 a
17,66 s, mas aparecia de ~13,8 a ~18,2 s). Sempre confirme olhando as folhas de contato e
os recortes em 0,1 s antes de fixar as janelas de "titulo" e "cartela_inicio".

Uso: python3 motor/analisar.py episodios/ep02-artista [--video arquivo.mp4]
"""
import argparse
import os
import subprocess

import numpy as np


def ffprobe(path):
    out = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
                          "stream=width,height,r_frame_rate:format=duration", "-of", "default=nw=1", path],
                         capture_output=True, text=True).stdout
    d = dict(line.split("=", 1) for line in out.split())
    num, den = d["r_frame_rate"].split("/")
    return int(d["width"]), int(d["height"]), float(num) / float(den), float(d["duration"])


def gray_frames(path, w, h):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", path, "-f", "rawvideo", "-pix_fmt", "gray", "-"],
                         capture_output=True).stdout
    return np.frombuffer(raw, np.uint8).reshape(-1, h, w)


def rgb_frame(path, t, w, h):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-ss", str(t), "-i", path, "-frames:v", "1",
                          "-f", "rawvideo", "-pix_fmt", "rgb24", "-"], capture_output=True).stdout
    return np.frombuffer(raw, np.uint8).reshape(h, w, 3).astype(int)


def windows(mask, fps, min_len=0.4):
    out, start = [], None
    for i, v in enumerate(list(mask) + [False]):
        if v and start is None:
            start = i
        elif not v and start is not None:
            if (i - start) / fps >= min_len:
                out.append((start / fps, i / fps))
            start = None
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("episodio")
    ap.add_argument("--video", default="original.mp4")
    args = ap.parse_args()
    src = os.path.join(args.episodio, args.video)
    out_dir = os.path.join(args.episodio, "analise")
    os.makedirs(out_dir, exist_ok=True)
    w, h, fps, dur = ffprobe(src)
    rep = [f"vídeo: {w}x{h}, {fps:g} fps, {dur:.2f} s"]

    # 1. linhas da faixa 16:9 (no padrão do acervo são laranja: R alto, B baixo)
    # amostra 15 quadros: alguns planos são tela cheia (sem linhas), por isso vale a maioria
    from collections import Counter
    votes = Counter()
    times = np.linspace(dur * 0.05, dur * 0.95, 15)
    for t in times:
        a = rgb_frame(src, t, w, h)
        votes.update(y for y in range(h) if a[y, :, 0].mean() - a[y, :, 2].mean() > 40)
    common = sorted(y for y, c in votes.items() if c >= len(times) * 0.3)
    rep.append(f"linhas laranja da faixa (y): {common}")
    if common:
        top = max(y for y in common if y < h / 2) + 3
        bot = min(y for y in common if y > h / 2) - 2
        bh = (bot - top) // 2 * 2
        rep.append(f"sugestão de recorte: \"crop={w}:{bh}:0:{top}\"  (confira se é ~16:9: {w / bh:.3f})")
    else:
        top, bh = int(h * 0.22), int(h * 0.56)
        rep.append("nenhuma linha laranja encontrada: o layout é diferente do EP01, defina o recorte olhando os quadros")

    # 2. texto branco queimado no centro da faixa (onde fica o nome do artista / título final)
    g = gray_frames(src, w, h)
    cy = top + bh // 2
    zone = g[:, cy - 30:cy + 30, int(w * 0.2):int(w * 0.8)]
    metric = (zone > 235).mean((1, 2))
    win = windows(metric > 0.1, fps, 0.8)
    rep.append("texto claro no centro da faixa (provável título queimado; ADICIONE ~0,5 s de margem pelos fades):")
    rep += [f"   {a:6.2f} → {b:6.2f} s" for a, b in win] or ["   nenhum"]

    # 3. áudio: envelope e candidatos a drop
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", src, "-ac", "1", "-ar", "8000", "-f", "s16le", "-"],
                         capture_output=True).stdout
    au = np.frombuffer(raw, np.int16).astype(float)
    s = 4000
    env = [20 * np.log10(np.sqrt((au[i * s:(i + 1) * s] ** 2).mean()) / 32768 + 1e-9) for i in range(len(au) // s)]
    rep.append("volume a cada 0,5 s (dBFS):")
    for i in range(0, len(env), 8):
        rep.append("   " + "  ".join(f"{i * 0.5 + j * 0.5:5.1f}:{v:6.1f}" for j, v in enumerate(env[i:i + 8])))
    # drop = trecho mais alto e sustentado (média dos 4 s seguintes), fora da introdução
    score = {i: np.mean(env[i:i + 8]) for i in range(6, len(env) - 8)}
    best = sorted(score, key=score.get, reverse=True)
    picks = []
    for i in best:
        if all(abs(i - j) > 8 for j in picks):
            picks.append(i)
        if len(picks) == 3:
            break
    rep.append("trechos mais fortes (candidatos a drop; refine o ataque em 0,05 s antes de usar): "
               + ", ".join(f"{i * 0.5:.1f} s ({score[i]:.1f} dB)" for i in sorted(picks)))

    # 4. folhas de contato
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", src, "-vf",
                    "fps=1,scale=360:-1,drawtext=text='%{pts\\:hms}':x=5:y=5:fontsize=18:fontcolor=yellow:"
                    "box=1:boxcolor=black,tile=5x3", "-q:v", "3", os.path.join(out_dir, "folha_%02d.jpg")],
                   check=True)
    rep.append(f"folhas de contato: {out_dir}/folha_*.jpg (1 quadro por segundo)")

    txt = "\n".join(rep)
    open(os.path.join(out_dir, "relatorio.txt"), "w", encoding="utf-8").write(txt + "\n")
    print(txt)


if __name__ == "__main__":
    main()
