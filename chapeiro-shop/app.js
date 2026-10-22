import { COLLECTIONS, PRODUCTS } from "./data.js";
import { ShirtViewer } from "./viewer.js";

const $ = (s, r = document) => r.querySelector(s);
const asset = (code, v, side) => `assets/${code}${v}-${side}.webp`;
const GENDER = { masculino: "Masculino", feminino: "Feminino", unissex: "Unissex" };

const meta = await fetch("assets/meta.json").then((r) => r.json()).catch(() => ({}));
const state = { code: PRODUCTS[0].code, variant: "a", filters: { line: "all", vol: "all", gender: "all" } };

const viewer = new ShirtViewer($("#stage-canvas"));
const sideButtons = [...document.querySelectorAll("[data-side]")];
viewer.onFrame = () => {
  const f = viewer.facing();
  for (const b of sideButtons) b.setAttribute("aria-pressed", String(b.dataset.side === f));
};

function product(code) { return PRODUCTS.find((p) => p.code === code); }

function select(code, variant = "a", { scroll = false } = {}) {
  state.code = code;
  state.variant = variant;
  const p = product(code), c = COLLECTIONS[p.collection];
  $("#p-eyebrow").textContent = `${c.line} · ${c.vol} — ${c.title}`;
  $("#p-code").textContent = p.code;
  $("#p-name").textContent = p.name;
  $("#p-type").textContent = p.type;
  $("#p-desc").textContent = p.desc;
  $("#p-gender").textContent = GENDER[p.gender];
  const generated = p.view === "frente" ? "costas" : "frente";
  $("#p-note").textContent = p.allover
    ? "Estampa total: as costas repetem o padrão da frente."
    : `A prancha mostra ${p.view === "frente" ? "a frente" : "as costas"}; ${generated === "costas" ? "as costas são uma prévia gerada" : "a frente é uma prévia gerada"} com a cor do tecido e a assinatura Chapeiro.`;

  const vs = $("#p-variants");
  vs.replaceChildren(...["a", "b"].map((v) => {
    const m = meta[code + v] || {};
    const b = document.createElement("button");
    b.type = "button";
    b.className = "variant";
    b.setAttribute("aria-pressed", String(v === variant));
    b.innerHTML = `<span class="swatch" style="background:${m.hex || "#888"}"></span><span><b>${v.toUpperCase()}</b> ${m.color || ""}</span>`;
    b.onclick = () => select(code, v);
    return b;
  }));

  viewer.load(asset(code, variant, "front"), asset(code, variant, "back"));
  viewer.setAutoRotate(true);
  for (const card of document.querySelectorAll(".card")) card.toggleAttribute("data-current", card.dataset.code === code);
  history.replaceState(null, "", `#${code}-${variant}`);
  if (scroll) $("#stage").scrollIntoView({ behavior: matchMedia("(prefers-reduced-motion: reduce)").matches ? "auto" : "smooth" });
}

function step(dir) {
  const list = visible();
  const i = list.findIndex((p) => p.code === state.code);
  const next = list[(i + dir + list.length) % list.length] || PRODUCTS[0];
  select(next.code, "a");
}

function visible() {
  const f = state.filters;
  return PRODUCTS.filter((p) => {
    const c = COLLECTIONS[p.collection];
    return (f.line === "all" || c.line === f.line) && (f.vol === "all" || c.vol === f.vol) && (f.gender === "all" || p.gender === f.gender);
  });
}

function renderGrid() {
  const list = visible();
  $("#count").textContent = `${list.length} modelos · ${list.length * 2} variações`;
  $("#grid").replaceChildren(...list.map((p) => {
    const c = COLLECTIONS[p.collection];
    const el = document.createElement("article");
    el.className = "card";
    el.dataset.code = p.code;
    el.toggleAttribute("data-current", p.code === state.code);
    const dots = ["a", "b"].map((v) => `<span class="dot" style="background:${meta[p.code + v]?.hex || "#888"}" title="${meta[p.code + v]?.color || v}"></span>`).join("");
    el.innerHTML = `
      <button type="button" class="card-hit" aria-label="Ver ${p.name} em 3D">
        <div class="card-img">
          <img loading="lazy" src="${asset(p.code, "a", "front")}" alt="${p.name}, frente">
          <img loading="lazy" class="back" src="${asset(p.code, "a", "back")}" alt="" aria-hidden="true">
        </div>
        <div class="card-meta">
          <span class="card-code">${p.code}</span>
          <span class="card-name">${p.name}</span>
          <span class="card-sub">${c.line} ${c.vol.replace("Vol. ", "")} · ${GENDER[p.gender]}</span>
          <span class="dots">${dots}</span>
        </div>
      </button>`;
    el.querySelector("button").onclick = () => select(p.code, "a", { scroll: true });
    return el;
  }));
}

for (const group of document.querySelectorAll("[data-filter]")) {
  group.addEventListener("click", (e) => {
    const b = e.target.closest("button[data-value]");
    if (!b) return;
    state.filters[group.dataset.filter] = b.dataset.value;
    for (const x of group.querySelectorAll("button")) x.setAttribute("aria-pressed", String(x === b));
    renderGrid();
  });
}
for (const b of sideButtons) b.onclick = () => viewer.showSide(b.dataset.side);
$("#prev").onclick = () => step(-1);
$("#next").onclick = () => step(1);
$("#spin").onclick = () => viewer.setAutoRotate(true);

renderGrid();
const m = /^#?([ABP]\d{2})-([ab])$/.exec(location.hash);
if (m && product(m[1])) select(m[1], m[2]);
else select("A01", "a");
