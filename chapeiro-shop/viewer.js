// Visualizador 3D das peças.
// Cada peça vira um volume "inflado" a partir da silhueta da foto: a frente recebe a textura
// da frente, as costas a textura das costas, e as duas metades se encontram na borda.
import * as THREE from "three";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";
import { RoomEnvironment } from "three/addons/environments/RoomEnvironment.js";

const GRID = 200;          // resolução da malha no lado maior
const SHIRT_HEIGHT = 2.2;  // altura da peça em unidades da cena

export class ShirtViewer {
  constructor(container) {
    this.container = container;
    this.renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true, preserveDrawingBuffer: true });
    this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    this.renderer.outputColorSpace = THREE.SRGBColorSpace;
    container.appendChild(this.renderer.domElement);

    this.scene = new THREE.Scene();
    const pmrem = new THREE.PMREMGenerator(this.renderer);
    this.scene.environment = pmrem.fromScene(new RoomEnvironment(), 0.04).texture;

    this.camera = new THREE.PerspectiveCamera(30, 1, 0.1, 100);
    this.camera.position.set(0, 0.1, 5.4);

    const key = new THREE.DirectionalLight(0xffffff, 1.1);
    key.position.set(2.5, 3, 4);
    const rim = new THREE.DirectionalLight(0xffffff, 0.9);
    rim.position.set(-2.5, 2, -4);
    this.scene.add(key, rim, new THREE.AmbientLight(0xffffff, 0.9));

    this.controls = new OrbitControls(this.camera, this.renderer.domElement);
    this.controls.enableDamping = true;
    this.controls.enablePan = false;
    this.controls.minDistance = 2.6;
    this.controls.maxDistance = 8;
    this.controls.minPolarAngle = Math.PI * 0.22;
    this.controls.maxPolarAngle = Math.PI * 0.78;
    this.controls.autoRotate = true;
    this.controls.autoRotateSpeed = 1.6;
    this.controls.addEventListener("start", () => { this.controls.autoRotate = false; this.tween = null; });

    this.shadow = makeShadow();
    this.shadow.position.y = -SHIRT_HEIGHT / 2 - 0.18;
    this.scene.add(this.shadow);

    this.group = new THREE.Group();
    this.scene.add(this.group);

    new ResizeObserver(() => this.resize()).observe(container);
    this.resize();
    this.renderer.setAnimationLoop((t) => this.tick(t));
  }

  resize() {
    const { clientWidth: w, clientHeight: h } = this.container;
    if (!w || !h) return;
    this.renderer.setSize(w, h, false);
    this.camera.aspect = w / h;
    // em telas estreitas afasta a câmera para a peça caber inteira
    this.camera.position.setLength(Math.max(5.4, 5.4 * 0.85 / this.camera.aspect));
    this.camera.updateProjectionMatrix();
  }

  async load(frontUrl, backUrl) {
    const token = (this.loadToken = Symbol());
    const loader = new THREE.TextureLoader();
    const [front, back, img] = await Promise.all([
      loader.loadAsync(frontUrl), loader.loadAsync(backUrl), loadImage(frontUrl),
    ]);
    if (token !== this.loadToken) return;
    for (const t of [front, back]) {
      t.colorSpace = THREE.SRGBColorSpace;
      t.anisotropy = this.renderer.capabilities.getMaxAnisotropy();
    }
    const geometry = buildShirtGeometry(img);
    const mat = (map) => new THREE.MeshStandardMaterial({
      map, roughness: 0.92, metalness: 0, side: THREE.DoubleSide, envMapIntensity: 0.35,
    });
    const mesh = new THREE.Mesh(geometry, [mat(front), mat(back)]);
    for (const old of [...this.group.children]) {
      this.group.remove(old);
      old.geometry.dispose();
      old.material.forEach((m) => { m.map.dispose(); m.dispose(); });
    }
    this.group.add(mesh);
    this.group.scale.setScalar(0.92);
    this.popStart = performance.now();
  }

  // Gira a câmera até a frente (0) ou as costas (π).
  showSide(side) {
    this.controls.autoRotate = false;
    const from = this.controls.getAzimuthalAngle();
    let to = side === "back" ? Math.PI : 0;
    let delta = ((to - from + Math.PI * 3) % (Math.PI * 2)) - Math.PI;
    this.tween = { from, delta, start: performance.now(), dur: 700 };
  }

  facing() {
    const a = this.controls.getAzimuthalAngle();
    return Math.abs(a) > Math.PI / 2 ? "back" : "front";
  }

  setAutoRotate(on) { this.controls.autoRotate = on; }

  tick(now) {
    if (this.tween) {
      const k = Math.min(1, (now - this.tween.start) / this.tween.dur);
      const e = 1 - Math.pow(1 - k, 3);
      const az = this.tween.from + this.tween.delta * e;
      const r = this.camera.position.length();
      const polar = this.controls.getPolarAngle();
      this.camera.position.set(r * Math.sin(polar) * Math.sin(az), r * Math.cos(polar), r * Math.sin(polar) * Math.cos(az));
      this.camera.lookAt(this.controls.target);
      if (k === 1) this.tween = null;
    }
    if (this.popStart) {
      const k = Math.min(1, (now - this.popStart) / 450);
      this.group.scale.setScalar(0.92 + 0.08 * (1 - Math.pow(1 - k, 3)));
      if (k === 1) this.popStart = 0;
    }
    this.controls.update();
    this.renderer.render(this.scene, this.camera);
    this.onFrame?.();
  }
}

function loadImage(url) {
  return new Promise((resolve, reject) => {
    const img = new Image();
    img.crossOrigin = "anonymous";
    img.onload = () => resolve(img);
    img.onerror = reject;
    img.src = url;
  });
}

// Constrói o volume da peça a partir do canal alfa da foto.
function buildShirtGeometry(img) {
  const aspect = img.width / img.height;
  const gw = aspect >= 1 ? GRID : Math.round(GRID * aspect);
  const gh = aspect >= 1 ? Math.round(GRID / aspect) : GRID;
  const W = gw + 1, H = gh + 1;

  const cv = document.createElement("canvas");
  cv.width = W; cv.height = H;
  const ctx = cv.getContext("2d", { willReadFrequently: true });
  ctx.drawImage(img, 0, 0, W, H);
  const px = ctx.getImageData(0, 0, W, H).data;
  const inside = new Uint8Array(W * H), alpha = new Float32Array(W * H);
  for (let i = 0; i < W * H; i++) {
    alpha[i] = px[i * 4 + 3] / 255;
    inside[i] = alpha[i] >= 0.5 ? 1 : 0;
  }

  // volume "inflado": resolve ∇²h = -1 dentro da silhueta com h = 0 na borda (SOR),
  // e usa √h para um perfil arredondado sem vincos
  let h = new Float32Array(W * H);
  const omega = 1.9;
  for (let it = 0; it < 500; it++) {
    for (let y = 1; y < H - 1; y++) for (let x = 1; x < W - 1; x++) {
      const i = y * W + x;
      if (!inside[i]) continue;
      const g = (h[i - 1] + h[i + 1] + h[i - W] + h[i + W] + 1) / 4;
      h[i] += omega * (g - h[i]);
    }
  }
  let hMax = 0;
  for (let i = 0; i < W * H; i++) hMax = Math.max(hMax, h[i]);
  const depth = SHIRT_HEIGHT * 0.065;
  const z = new Float32Array(W * H);
  for (let i = 0; i < W * H; i++) z[i] = inside[i] ? depth * Math.sqrt(h[i] / hMax) : 0;

  const used = new Uint8Array(W * H);
  const quads = [];
  for (let y = 0; y < gh; y++) for (let x = 0; x < gw; x++) {
    const a = y * W + x, b = a + 1, c = a + W, e = c + 1;
    if (inside[a] | inside[b] | inside[c] | inside[e]) {
      quads.push(a, b, c, e);
      used[a] = used[b] = used[c] = used[e] = 1;
    }
  }

  const index = new Int32Array(W * H).fill(-1);
  const pos = [], uv = [];
  let n = 0;
  for (let i = 0; i < W * H; i++) if (used[i]) index[i] = n++;
  // vértices da borda deslizam até onde o alfa cruza 0,5: contorno liso e costura fechada
  const gx = new Float32Array(W * H), gy = new Float32Array(W * H);
  for (let i = 0; i < W * H; i++) {
    if (!used[i]) continue;
    const x = i % W, y = (i / W) | 0;
    gx[i] = x; gy[i] = y;
    if (inside[i]) continue;
    let sx = 0, sy = 0, k = 0;
    for (let dy = -1; dy <= 1; dy++) for (let dx = -1; dx <= 1; dx++) {
      const nx = x + dx, ny = y + dy;
      if ((!dx && !dy) || nx < 0 || ny < 0 || nx >= W || ny >= H) continue;
      const j = ny * W + nx;
      if (!inside[j]) continue;
      const t = Math.min(1, Math.max(0, (0.5 - alpha[i]) / Math.max(1e-3, alpha[j] - alpha[i])));
      sx += x + dx * t; sy += y + dy * t; k++;
    }
    if (k) { gx[i] = sx / k; gy[i] = sy / k; }
  }
  // suaviza o anel da borda para tirar o serrilhado da grade
  const ring = [];
  for (let i = 0; i < W * H; i++) {
    if (!used[i]) continue;
    const x = i % W, y = (i / W) | 0;
    let edge = !inside[i];
    for (let dy = -1; dy <= 1 && !edge; dy++) for (let dx = -1; dx <= 1; dx++) {
      const nx = x + dx, ny = y + dy;
      if (nx < 0 || ny < 0 || nx >= W || ny >= H || !inside[ny * W + nx]) { edge = true; break; }
    }
    if (edge) ring.push(i);
  }
  const isRing = new Uint8Array(W * H);
  for (const i of ring) isRing[i] = 1;
  for (let it = 0; it < 4; it++) {
    const nx2 = new Float32Array(gx), ny2 = new Float32Array(gy);
    for (const i of ring) {
      const x = i % W, y = (i / W) | 0;
      let sx = 0, sy = 0, k = 0;
      for (let dy = -1; dy <= 1; dy++) for (let dx = -1; dx <= 1; dx++) {
        const j = (y + dy) * W + (x + dx);
        if ((dx || dy) && x + dx >= 0 && y + dy >= 0 && x + dx < W && y + dy < H && isRing[j] && !inside[j] === !inside[i]) {
          sx += gx[j]; sy += gy[j]; k++;
        }
      }
      if (k) { nx2[i] = gx[i] * 0.5 + (sx / k) * 0.5; ny2[i] = gy[i] * 0.5 + (sy / k) * 0.5; }
    }
    gx.set(nx2); gy.set(ny2);
  }
  const width = SHIRT_HEIGHT * (gw / gh);
  for (const side of [1, -1]) {
    for (let i = 0; i < W * H; i++) {
      if (!used[i]) continue;
      const u = gx[i] / gw, v = 1 - gy[i] / gh;
      pos.push((u - 0.5) * width, (v - 0.5) * SHIRT_HEIGHT, side * z[i]);
      uv.push(side === 1 ? u : 1 - u, v);
    }
  }
  const idx = [];
  for (let q = 0; q < quads.length; q += 4) {
    const [a, b, c, e] = [quads[q], quads[q + 1], quads[q + 2], quads[q + 3]].map((k) => index[k]);
    idx.push(a, c, b, b, c, e);
  }
  const frontCount = idx.length;
  for (let q = 0; q < frontCount; q += 3) idx.push(idx[q] + n, idx[q + 2] + n, idx[q + 1] + n);

  const g = new THREE.BufferGeometry();
  g.setAttribute("position", new THREE.Float32BufferAttribute(pos, 3));
  g.setAttribute("uv", new THREE.Float32BufferAttribute(uv, 2));
  g.setIndex(idx);
  g.addGroup(0, frontCount, 0);
  g.addGroup(frontCount, frontCount, 1);
  g.computeVertexNormals();
  return g;
}

function makeShadow() {
  const c = document.createElement("canvas");
  c.width = c.height = 128;
  const ctx = c.getContext("2d");
  const grd = ctx.createRadialGradient(64, 64, 4, 64, 64, 64);
  grd.addColorStop(0, "rgba(0,0,0,0.35)");
  grd.addColorStop(1, "rgba(0,0,0,0)");
  ctx.fillStyle = grd;
  ctx.fillRect(0, 0, 128, 128);
  const m = new THREE.Mesh(
    new THREE.PlaneGeometry(2.6, 0.9),
    new THREE.MeshBasicMaterial({ map: new THREE.CanvasTexture(c), transparent: true, depthWrite: false }),
  );
  m.rotation.x = -Math.PI / 2;
  return m;
}
