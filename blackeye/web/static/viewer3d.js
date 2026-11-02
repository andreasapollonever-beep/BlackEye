// BlackEye 3D viewer — retaining wall with earth/water/seismic pressures and results.
import * as THREE from "three";
import { OrbitControls } from "three/addons/OrbitControls.js";
import { CSS2DObject, CSS2DRenderer } from "three/addons/CSS2DRenderer.js";

const COLORS = { earth: 0xc47a2c, surcharge: 0x8e6cc4, water: 0x2f8fd8, seismic: 0xe03b3b,
  bearing: 0x2e9b5f, concrete: 0xb4b8bf, soil: 0xd9bf8c, front: 0xe6d3ad };
const LAYERS = [
  ["soil", "Soil"], ["water", "Groundwater"], ["earth", "Earth pressure"],
  ["surcharge", "Surcharge pressure"], ["seismic", "Seismic increment"],
  ["bearing", "Base pressure"], ["forces", "Resultant forces"], ["labels", "Labels"],
];

class WallViewer {
  constructor(host) {
    this.host = host;
    this.visible = Object.fromEntries(LAYERS.map(([k]) => [k, true]));
    this.groups = {};
    this.scene = new THREE.Scene();
    this.scene.background = new THREE.Color(0xeef1f5);
    this.camera = new THREE.PerspectiveCamera(40, 1, 0.05, 500);
    this.renderer = new THREE.WebGLRenderer({ antialias: true, preserveDrawingBuffer: true });
    this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    this.renderer.shadowMap.enabled = true;
    this.labels = new CSS2DRenderer();
    this.labels.domElement.className = "v3d-labels";
    host.append(this.renderer.domElement, this.labels.domElement);
    this.controls = new OrbitControls(this.camera, this.labels.domElement);
    this.controls.enableDamping = true;
    this.scene.add(new THREE.HemisphereLight(0xffffff, 0x8a7a66, 1.6));
    const sun = new THREE.DirectionalLight(0xffffff, 1.6);
    sun.position.set(-6, 12, 9);
    sun.castShadow = true;
    sun.shadow.mapSize.set(2048, 2048);
    Object.assign(sun.shadow.camera, { left: -15, right: 15, top: 15, bottom: -15 });
    this.scene.add(sun);
    this.buildUi();
    new ResizeObserver(() => this.resize()).observe(host);
    const loop = () => { this.controls.update(); this.render(); requestAnimationFrame(loop); };
    loop();
  }

  buildUi() {
    const panel = document.createElement("div");
    panel.className = "v3d-panel";
    panel.innerHTML = `<div class="v3d-title">Layers</div>` + LAYERS.map(([k, label]) =>
      `<label><input type="checkbox" data-k="${k}" checked> ${label}</label>`).join("") +
      `<div class="v3d-btns"><button data-view="iso">3D</button><button data-view="side">Section</button>` +
      `<button data-view="png">PNG</button></div>`;
    panel.addEventListener("change", (e) => {
      const k = e.target.dataset.k;
      if (!k) return;
      this.visible[k] = e.target.checked;
      this.applyVisibility();
    });
    panel.addEventListener("click", (e) => {
      const v = e.target.dataset.view;
      if (v === "png") return this.snapshot();
      if (v) this.setView(v);
    });
    this.results = document.createElement("div");
    this.results.className = "v3d-results";
    this.legend = document.createElement("div");
    this.legend.className = "v3d-legend";
    this.host.append(panel, this.results, this.legend);
  }

  resize() {
    const w = this.host.clientWidth, h = this.host.clientHeight;
    if (!w || !h) return;
    this.camera.aspect = w / h;
    this.camera.updateProjectionMatrix();
    this.renderer.setSize(w, h);
    this.labels.setSize(w, h);
  }

  render() { this.renderer.render(this.scene, this.camera); this.labels.render(this.scene, this.camera); }

  snapshot() {
    this.render();
    const a = document.createElement("a");
    a.href = this.renderer.domElement.toDataURL("image/png");
    a.download = "retaining-wall-3d.png";
    a.click();
  }

  applyVisibility() {
    for (const [k, g] of Object.entries(this.groups)) g.visible = this.visible[k] !== false;
    // labels in hidden groups are hidden by CSS2DRenderer automatically; global label toggle:
    this.scene.traverse((o) => { if (o.isCSS2DObject) o.element.style.display = this.visible.labels ? "" : "none"; });
  }

  group(key) {
    const g = new THREE.Group();
    g.name = key;
    this.groups[key] = g;
    this.root.add(g);
    return g;
  }

  label(text, pos, cls = "") {
    const div = document.createElement("div");
    div.className = `v3d-label ${cls}`;
    div.textContent = text;
    const o = new CSS2DObject(div);
    o.position.copy(pos);
    return o;
  }

  // Extrude a 2D polygon (x, z section coordinates) along the wall length.
  prism(pts, depth, color, opts = {}) {
    const shape = new THREE.Shape(pts.map(([x, y]) => new THREE.Vector2(x, y)));
    const geo = new THREE.ExtrudeGeometry(shape, { depth, bevelEnabled: false });
    geo.translate(0, 0, -depth / 2);
    const mat = new THREE.MeshStandardMaterial({ color, roughness: 0.85, metalness: 0,
      transparent: !!opts.opacity, opacity: opts.opacity ?? 1, depthWrite: !opts.opacity,
      side: THREE.DoubleSide });
    const mesh = new THREE.Mesh(geo, mat);
    mesh.castShadow = !opts.opacity;
    mesh.receiveShadow = true;
    if (opts.edges !== false) {
      const edges = new THREE.LineSegments(new THREE.EdgesGeometry(geo, 25),
        new THREE.LineBasicMaterial({ color: opts.edgeColor ?? 0x3d434c, transparent: true,
          opacity: opts.opacity ? 0.5 : 0.9 }));
      mesh.add(edges);
    }
    return mesh;
  }

  arrow(from, dir, len, color, head = 0.18) {
    const a = new THREE.ArrowHelper(dir.clone().normalize(), from, len, color,
      Math.min(head, len * 0.45), Math.min(head * 0.6, len * 0.3));
    a.line.material.linewidth = 2;
    return a;
  }

  load(model, summary) {
    if (this.root) {
      this.root.traverse((o) => { if (o.isCSS2DObject) o.element.remove(); });
      this.scene.remove(this.root);
    }
    this.root = new THREE.Group();
    this.groups = {};
    this.scene.add(this.root);
    const g = model.geometry;
    const { B, t_base: tb, H_stem: Hs, toe, t_top, t_bot, h_v: hv, h_w: hw, length: L } = g;
    const beta = (g.beta * Math.PI) / 180;
    const x0 = toe + t_top, xb = toe + t_bot, far = B + Math.max(2.0, 0.6 * hv);
    const surf = (x) => tb + Hs + Math.max(x - x0, 0) * Math.tan(beta);

    // --- structure (always visible)
    const conc = this.group("concrete");
    conc.add(this.prism([[toe, tb], [xb, tb], [x0, tb + Hs], [toe, tb + Hs]], L, COLORS.concrete));
    conc.add(this.prism([[0, 0], [B, 0], [B, tb], [0, tb]], L, COLORS.concrete));

    // --- soil
    const soil = this.group("soil");
    soil.add(this.prism([[xb, tb], [B, tb], [B, 0], [far, 0], [far, surf(far)], [x0, tb + Hs]],
      L, COLORS.soil, { opacity: 0.28, edgeColor: 0x9a7b4a }));
    if (g.d_front > 0) {
      soil.add(this.prism([[-1.5, 0], [0, 0], [0, tb], [toe, tb], [toe, tb + g.d_front], [-1.5, tb + g.d_front]],
        L, COLORS.front, { opacity: 0.35, edgeColor: 0x9a7b4a }));
    }
    const ground = new THREE.Mesh(new THREE.PlaneGeometry(far + 6, L + 6),
      new THREE.MeshStandardMaterial({ color: 0xcfc6b5, roughness: 1, transparent: true,
        opacity: 0.45, depthWrite: false }));
    ground.rotation.x = -Math.PI / 2;
    ground.position.set(far / 2, -0.003, 0);
    ground.receiveShadow = true;
    const grid = new THREE.GridHelper(Math.max(far + 6, L + 6), Math.round(Math.max(far + 6, L + 6)), 0x9a9182, 0xb8b0a2);
    grid.position.set(far / 2, 0.001, 0);
    const base = this.group("ground");
    base.add(ground, grid);

    // --- water
    if (hw > 0) {
      const wg = this.group("water");
      wg.add(this.prism([[xb, tb], [far, tb], [far, hw], [xb, hw]], L * 0.999, COLORS.water,
        { opacity: 0.22, edgeColor: COLORS.water }));
      wg.add(this.label(`GWL +${hw.toFixed(2)} m`, new THREE.Vector3(far, hw, L / 2), "water"));
    }

    // --- pressures: cumulative prisms on the virtual back + arrows
    const zGrid = Array.from({ length: 41 }, (_, i) => (hv * i) / 40);
    const interp = (pts, z) => {
      for (let i = 1; i < pts.length; i++) {
        const [z1, p1] = pts[i - 1], [z2, p2] = pts[i];
        if (z <= z2 + 1e-9) return p1 + ((p2 - p1) * (z - z1)) / ((z2 - z1) || 1);
      }
      return pts[pts.length - 1][1];
    };
    const totals = zGrid.map(() => 0);
    const pmaxTot = zGrid.reduce((m, z) => Math.max(m, model.pressures.reduce((s, pr) => s + interp(pr.points, z), 0)), 1);
    const scale = Math.max(1.2, 0.45 * hv) / pmaxTot; // m per kN/m²
    const legendRows = [];
    for (const pr of model.pressures) {
      const key = pr.key;
      const grp = this.group(key);
      const inner = zGrid.map((z, i) => [B + totals[i] * scale, z]);
      zGrid.forEach((z, i) => { totals[i] += interp(pr.points, z); });
      const outer = zGrid.map((z, i) => [B + totals[i] * scale, z]);
      const poly = [...inner, ...outer.reverse()];
      // thin "slabs" at both ends and the middle show the distribution clearly
      for (const zPos of [-L / 2, 0, L / 2]) {
        const slab = this.prism(poly, 0.04, COLORS[key], { opacity: 0.55, edgeColor: COLORS[key] });
        slab.position.z = zPos;
        grp.add(slab);
      }
      const sheet = this.prism(poly, L, COLORS[key], { opacity: 0.12, edges: false });
      grp.add(sheet);
      // arrows along the wall
      const nZ = 7, nL = 5;
      for (let j = 0; j < nL; j++) {
        const zz = -L / 2 + (L * (j + 0.5)) / nL;
        for (let i = 0; i < nZ; i++) {
          const z = (hv * (i + 0.5)) / nZ;
          const xIn = interpPoly(inner, z);
          const p = interp(pr.points, z) * scale;
          if (p < 0.03) continue;
          grp.add(this.arrow(new THREE.Vector3(xIn + p, z, zz), new THREE.Vector3(-1, 0, 0), p, COLORS[key], 0.12));
        }
      }
      const [zm, pm] = pr.points.reduce((a, b) => (b[1] > a[1] ? b : a));
      grp.add(this.label(`${pm.toFixed(1)} kN/m²`, new THREE.Vector3(B + totals[zGrid.findIndex((z) => z >= zm - 1e-9)] * scale + 0.1, zm, L / 2), key));
      legendRows.push([key, pr.name, pm]);
    }

    // --- base pressure (governing design case)
    if (model.bearing?.length) {
      const grp = this.group("bearing");
      const qmax = Math.max(...model.bearing.map((b) => b[1]), 1);
      const s = Math.max(0.8, 0.25 * hv) / qmax;
      const poly = [[0, 0], ...model.bearing.map(([x, q]) => [x, -q * s]), [B, 0]];
      grp.add(this.prism(poly, L * 0.98, COLORS.bearing, { opacity: 0.3, edgeColor: COLORS.bearing }));
      for (let j = 0; j < 5; j++) {
        const zz = -L / 2 + (L * (j + 0.5)) / 5;
        for (let i = 0; i <= 8; i++) {
          const x = (B * i) / 8;
          const q = interpXY(model.bearing, x) * s;
          if (q > 0.03) grp.add(this.arrow(new THREE.Vector3(x, -q, zz), new THREE.Vector3(0, 1, 0), q, COLORS.bearing, 0.1));
        }
      }
      const gv = model.governing || {};
      grp.add(this.label(`q,max = ${qmax.toFixed(0)} kN/m² · ${gv.name ?? ""}`,
        new THREE.Vector3(0.1, -qmax * s - 0.2, L / 2), "bearing"));
      legendRows.push(["bearing", `Base pressure (${gv.name ?? "design"})`, qmax]);
    }

    // --- resultant characteristic forces
    const fg = this.group("forces");
    const fmax = Math.max(...model.forces.map((f) => Math.hypot(f.H, f.V)), 1);
    const fs = Math.max(1.0, 0.35 * hv) / fmax;
    for (const f of model.forces) {
      if (f.role === "thrust" || f.role === "water") {
        if (Math.abs(f.H) < 1e-6) continue;
        const len = Math.max(Math.abs(f.H) * fs, 0.25);
        const col = f.role === "water" ? COLORS.water : f.name.startsWith("Surcharge") ? COLORS.surcharge : COLORS.earth;
        const start = new THREE.Vector3(B + len + 0.05, f.z, 0);
        fg.add(this.arrow(start, new THREE.Vector3(-1, 0, 0), len, col, 0.28));
        fg.add(this.label(`${f.name}: ${f.H.toFixed(1)} kN/m @ ${f.z.toFixed(2)} m`, start.clone().add(new THREE.Vector3(0.05, 0.15, 0)), "force"));
      } else if (f.role === "weight" && f.V > 0) {
        const len = Math.max(f.V * fs * 0.6, 0.25);
        const top = new THREE.Vector3(f.x, (f.z || tb) + len, -L / 4);
        fg.add(this.arrow(top, new THREE.Vector3(0, -1, 0), len, 0x444a55, 0.2));
        fg.add(this.label(`${f.name}: ${f.V.toFixed(1)} kN/m`, top.clone().add(new THREE.Vector3(0, 0.12, 0)), "weight"));
      }
    }
    if (model.governing?.R_x !== undefined) {
      const rx = model.governing.R_x;
      fg.add(this.arrow(new THREE.Vector3(rx, -0.9, 0), new THREE.Vector3(0, 1, 0), 0.88, 0x111111, 0.22));
      fg.add(this.label(`Resultant e = ${model.governing.e.toFixed(3)} m, B' = ${model.governing.B_eff.toFixed(2)} m`,
        new THREE.Vector3(rx, -1.05, 0), "result"));
    }

    // --- dimensions
    const lab = this.group("labels");
    lab.add(this.label(`H = ${Hs.toFixed(2)} m`, new THREE.Vector3(toe - 0.15, tb + Hs / 2, L / 2), "dim"));
    lab.add(this.label(`B = ${B.toFixed(2)} m`, new THREE.Vector3(B / 2, 0.02, L / 2 + 0.3), "dim"));
    lab.add(this.label(`β = ${g.beta.toFixed(1)}°`, new THREE.Vector3(far - 0.5, surf(far - 0.5) + 0.2, 0), "dim"));
    lab.add(this.label(`virtual back h = ${hv.toFixed(2)} m`, new THREE.Vector3(B, hv + 0.25, -L / 2), "dim"));

    this.legend.innerHTML = legendRows.map(([k, n, v]) =>
      `<div><span class="sw" style="background:#${COLORS[k].toString(16).padStart(6, "0")}"></span>${n}: <b>${v.toFixed(1)}</b> kN/m²</div>`).join("");
    this.renderResults(model, summary);
    this.extent = { B, hv, L, far };
    this.applyVisibility();
    if (!this.framed) { this.setView("iso"); this.framed = true; }
  }

  renderResults(model, summary) {
    const checks = model.checks || [];
    const groups = {};
    for (const c of checks) {
      const key = c.description.split(":")[0];
      if (!groups[key] || c.utilisation > groups[key].utilisation) groups[key] = c;
    }
    const rows = Object.values(groups).sort((a, b) => b.utilisation - a.utilisation).slice(0, 12);
    const ok = summary ? summary.passed : checks.every((c) => c.passed);
    this.results.innerHTML = `<div class="v3d-title ${ok ? "pass" : "fail"}">${ok ? "✔ All checks pass" : "✖ Design fails"}</div>` +
      rows.map((c) => {
        const u = Number.isFinite(c.utilisation) ? c.utilisation : 9.99;
        const w = Math.min(u, 1.2) / 1.2 * 100;
        return `<div class="v3d-row"><span title="${c.description}">${c.description.split(":")[0]}</span>` +
          `<span class="bar"><i class="${c.passed ? "pass" : "fail"}" style="width:${w}%"></i></span><b>${u.toFixed(2)}</b></div>`;
      }).join("");
  }

  setView(kind) {
    const e = this.extent || { B: 3, hv: 4, L: 8, far: 5 };
    const c = new THREE.Vector3(e.far * 0.5, e.hv * 0.35, 0);
    const d = Math.max(e.hv * 1.6, e.far, e.L) * 1.75;
    if (kind === "side") this.camera.position.set(c.x, c.y, e.L / 2 + d);
    else this.camera.position.set(c.x - d * 0.6, c.y + d * 0.5, d * 0.9);
    this.controls.target.copy(c);
    this.controls.update();
  }
}

function interpPoly(pts, z) {
  // pts: [[x, z], ...] sorted by z -> x at height z
  for (let i = 1; i < pts.length; i++) {
    const [x1, z1] = pts[i - 1], [x2, z2] = pts[i];
    if (z <= z2 + 1e-9) return x1 + ((x2 - x1) * (z - z1)) / ((z2 - z1) || 1);
  }
  return pts[pts.length - 1][0];
}

function interpXY(pts, x) {
  for (let i = 1; i < pts.length; i++) {
    const [x1, y1] = pts[i - 1], [x2, y2] = pts[i];
    if (x <= x2 + 1e-9) return y1 + ((y2 - y1) * (x - x1)) / ((x2 - x1) || 1);
  }
  return pts[pts.length - 1][1];
}

let viewer = null;
function show(detail) {
  const host = document.getElementById("viewer3d");
  if (!host || !detail?.model) return;
  viewer ||= new WallViewer(host);
  viewer.load(detail.model, detail.summary);
  viewer.resize();
}
window.addEventListener("blackeye:model3d", (e) => show(e.detail));
window.addEventListener("blackeye:show3d", () => viewer?.resize());
if (window.__blackeyeModel) show(window.__blackeyeModel);
