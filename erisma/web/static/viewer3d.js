// Erisma 3D viewer — renders the generic scene produced by erisma/report/scene3d.py.
import * as THREE from "three";
import { OrbitControls } from "three/addons/OrbitControls.js";
import { CSS2DObject, CSS2DRenderer } from "three/addons/CSS2DRenderer.js";

const T = (k) => (window.ErismaI18n ? window.ErismaI18n(k) : k);

class Viewer {
  constructor(host) {
    this.host = host;
    this.hidden = {};
    this.scene = new THREE.Scene();
    this.applyTheme();
    window.addEventListener("erisma:theme", () => this.applyTheme());
    this.camera = new THREE.PerspectiveCamera(38, 1, 0.05, 1000);
    this.renderer = new THREE.WebGLRenderer({ antialias: true, preserveDrawingBuffer: true });
    this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
    this.renderer.shadowMap.enabled = true;
    this.labels = new CSS2DRenderer();
    this.labels.domElement.className = "v3d-labels";
    host.append(this.renderer.domElement, this.labels.domElement);
    this.controls = new OrbitControls(this.camera, this.labels.domElement);
    this.controls.enableDamping = true;
    this.scene.add(new THREE.HemisphereLight(0xffffff, 0x8a7a66, 1.6));
    this.sun = new THREE.DirectionalLight(0xffffff, 1.5);
    this.sun.castShadow = true;
    this.sun.shadow.mapSize.set(2048, 2048);
    this.scene.add(this.sun, this.sun.target);
    this.buildUi();
    this.enablePicking();
    new ResizeObserver(() => this.resize()).observe(host);
    const loop = () => { this.controls.update(); this.render(); requestAnimationFrame(loop); };
    loop();
  }

  applyTheme() {
    const bg = getComputedStyle(document.documentElement).getPropertyValue("--v3d-bg").trim() || "#eef1f5";
    this.scene.background = new THREE.Color(bg);
  }

  buildUi() {
    this.panel = document.createElement("div");
    this.panel.className = "v3d-panel";
    this.panel.addEventListener("change", (e) => {
      const k = e.target.dataset.k;
      if (!k) return;
      this.hidden[k] = !e.target.checked;
      this.applyVisibility();
    });
    this.panel.addEventListener("click", (e) => {
      const v = e.target.dataset.view;
      if (v === "png") this.snapshot();
      else if (v) this.setView(v);
    });
    this.results = document.createElement("div");
    this.results.className = "v3d-results";
    this.legend = document.createElement("div");
    this.legend.className = "v3d-legend";
    this.help = document.createElement("div");
    this.help.className = "v3d-help";
    this.host.append(this.panel, this.results, this.legend, this.help);
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
    a.download = `erisma-3d-${this.kind || "model"}.png`;
    a.click();
  }

  applyVisibility() {
    // CSS2DRenderer only looks at each label's own .visible flag, so propagate it.
    const showLabels = !this.hidden.labels;
    for (const [k, g] of Object.entries(this.groups)) {
      g.visible = !this.hidden[k];
      g.traverse((o) => { if (o.isCSS2DObject) o.visible = g.visible && showLabels; });
    }
  }

  material(color, opacity) {
    return new THREE.MeshStandardMaterial({ color, roughness: 0.85, metalness: 0.02,
      transparent: opacity < 1, opacity, depthWrite: opacity >= 0.95, side: THREE.DoubleSide });
  }

  withEdges(mesh, geo, color, opacity) {
    const e = new THREE.LineSegments(new THREE.EdgesGeometry(geo, 25),
      new THREE.LineBasicMaterial({ color: new THREE.Color(color).multiplyScalar(0.55),
        transparent: true, opacity: opacity < 1 ? 0.6 : 0.9 }));
    mesh.add(e);
  }

  build(o) {
    const obj = this.build1(o);
    if (obj && o.pick) obj.userData.pick = o.pick;
    return obj;
  }

  // click (without dragging) on an object carrying a "pick" id → erisma:pick event
  enablePicking() {
    const el = this.labels.domElement;
    let down = null;
    el.addEventListener("pointerdown", (e) => { down = [e.clientX, e.clientY, e.button]; });
    el.addEventListener("pointerup", (e) => {
      if (!down || Math.hypot(e.clientX - down[0], e.clientY - down[1]) > 4 || down[2] !== 0) return;
      const r = el.getBoundingClientRect();
      const ndc = new THREE.Vector2(((e.clientX - r.left) / r.width) * 2 - 1, -((e.clientY - r.top) / r.height) * 2 + 1);
      const ray = new THREE.Raycaster();
      ray.setFromCamera(ndc, this.camera);
      const cands = [];
      this.root?.traverse((o) => {
        if (o.isMesh && o.userData.pick) {
          let v = true;
          for (let p = o; p; p = p.parent) if (p.visible === false) v = false;
          if (v) cands.push(o);
        }
      });
      const hit = ray.intersectObjects(cands, false)[0];
      window.dispatchEvent(new CustomEvent("erisma:pick", { detail: { host: this.host.id,
        pick: hit ? hit.object.userData.pick : null, shift: e.shiftKey || e.ctrlKey || e.metaKey } }));
    });
  }

  highlight(picks) {
    this.picked = new Set(picks || []);
    this.root?.traverse((o) => {
      if (!o.isMesh || !o.userData.pick || !o.material?.emissive) return;
      o.material.emissive.set(this.picked.has(o.userData.pick) ? 0x3b82f6 : 0x000000);
      o.material.emissiveIntensity = this.picked.has(o.userData.pick) ? 0.9 : 0;
    });
  }

  build1(o) {
    if (o.t === "prism") {
      const shape = new THREE.Shape(o.pts.map(([x, y]) => new THREE.Vector2(x, y)));
      const geo = new THREE.ExtrudeGeometry(shape, { depth: o.depth, bevelEnabled: false });
      geo.translate(0, 0, o.z - o.depth / 2);
      const m = new THREE.Mesh(geo, this.material(o.color, o.opacity));
      m.castShadow = o.opacity >= 0.95; m.receiveShadow = true;
      if (o.edges) this.withEdges(m, geo, o.color, o.opacity);
      return m;
    }
    if (o.t === "box") {
      const geo = new THREE.BoxGeometry(...o.s);
      const m = new THREE.Mesh(geo, this.material(o.color, o.opacity));
      m.position.set(...o.c);
      m.castShadow = o.opacity >= 0.95; m.receiveShadow = true;
      if (o.edges) this.withEdges(m, geo, o.color, o.opacity);
      return m;
    }
    if (o.t === "mesh") {
      const geo = new THREE.BufferGeometry();
      geo.setAttribute("position", new THREE.Float32BufferAttribute(o.v.flat(), 3));
      geo.setIndex(o.f.flat());
      geo.computeVertexNormals();
      const mat = this.material(o.vc ? 0xffffff : o.color, o.opacity);
      if (o.vc) {
        const cols = [];
        o.vc.forEach((c) => { const k = new THREE.Color(c); cols.push(k.r, k.g, k.b); });
        geo.setAttribute("color", new THREE.Float32BufferAttribute(cols, 3));
        mat.vertexColors = true;
      }
      return new THREE.Mesh(geo, mat);
    }
    if (o.t === "line") {
      const pts = o.p.map((p) => new THREE.Vector3(...p));
      if (o.closed) pts.push(pts[0].clone());
      const geo = new THREE.BufferGeometry().setFromPoints(pts);
      const mat = o.dashed
        ? new THREE.LineDashedMaterial({ color: o.color, dashSize: 0.15, gapSize: 0.1 })
        : new THREE.LineBasicMaterial({ color: o.color });
      const l = new THREE.Line(geo, mat);
      if (o.dashed) l.computeLineDistances();
      return l;
    }
    if (o.t === "cyl") {
      const a = new THREE.Vector3(...o.a), b = new THREE.Vector3(...o.b);
      const dir = b.clone().sub(a);
      const geo = new THREE.CylinderGeometry(o.r, o.r, dir.length(), 14);
      const m = new THREE.Mesh(geo, this.material(o.color, o.opacity));
      m.position.copy(a).add(b).multiplyScalar(0.5);
      m.quaternion.setFromUnitVectors(new THREE.Vector3(0, 1, 0), dir.normalize());
      m.castShadow = true;
      return m;
    }
    if (o.t === "arrow") {
      const head = o.head ?? Math.min(0.25, o.len * 0.3);
      return new THREE.ArrowHelper(new THREE.Vector3(...o.d).normalize(), new THREE.Vector3(...o.o),
        o.len, o.color, Math.min(head, o.len * 0.45), Math.min(head * 0.6, o.len * 0.3));
    }
    if (o.t === "label") {
      const div = document.createElement("div");
      div.className = `v3d-label ${o.style || ""}`;
      div.textContent = o.text;
      const l = new CSS2DObject(div);
      l.position.set(...o.p);
      return l;
    }
    return null;
  }

  load(scene, summary) {
    if (this.root) {
      this.root.traverse((o) => { if (o.isCSS2DObject) o.element.remove(); });
      this.scene.remove(this.root);
    }
    const kindChanged = this.kind !== scene.kind;
    this.kind = scene.kind;
    this.root = new THREE.Group();
    this.groups = {};
    for (const l of scene.layers) {
      const g = new THREE.Group();
      this.groups[l.key] = g;
      this.root.add(g);
      if (kindChanged && !(l.key in this.hidden)) this.hidden[l.key] = !l.visible;
    }
    for (const o of scene.objects) {
      const obj = this.build(o);
      if (!obj) continue;
      (this.groups[o.layer] || this.root).add(obj);
    }
    this.scene.add(this.root);

    // bounding box -> ground grid, light and camera
    const box = new THREE.Box3();
    this.root.traverse((o) => { if (o.isMesh) box.expandByObject(o); });
    if (box.isEmpty()) box.set(new THREE.Vector3(-1, -1, -1), new THREE.Vector3(1, 1, 1));
    this.box = box;
    const size = box.getSize(new THREE.Vector3());
    const c = box.getCenter(new THREE.Vector3());
    const ext = Math.max(size.x, size.z);
    const cell = ext < 2 ? 0.1 : 1;  // fine grid for small details (connections, plates)
    const span = Math.ceil((ext + Math.min(4, ext)) / cell) * cell;
    const grid = new THREE.GridHelper(span, Math.round(span / cell), 0x9a9182, 0xc2bbae);
    grid.position.set(c.x, 0.001, c.z);
    grid.material.transparent = true; grid.material.opacity = 0.5;
    this.root.add(grid);
    this.sun.position.set(c.x - size.x - 4, c.y + size.y * 2 + 8, c.z + size.z + 6);
    this.sun.target.position.copy(c);
    const r = Math.max(size.x, size.y, size.z) * 1.2 + 2;
    Object.assign(this.sun.shadow.camera, { left: -r, right: r, top: r, bottom: -r, far: r * 6 });
    this.sun.shadow.camera.updateProjectionMatrix();

    this.renderPanel(scene);
    this.legend.innerHTML = scene.legend.map((l) =>
      `<div><span class="sw" style="background:${l.color}"></span>${l.text}</div>`).join("");
    this.legend.style.display = scene.legend.length ? "" : "none";
    this.renderResults(summary);
    this.help.textContent = T("Drag to rotate · right-drag to pan · scroll to zoom");
    this.applyVisibility();
    if (kindChanged || !this.framed) { this.setView(scene.views?.default || "iso"); this.framed = true; }
    if (this.picked) this.highlight([...this.picked]);
  }

  renderPanel(scene) {
    const rows = scene.layers.filter((l) => l.toggle).map((l) =>
      `<label><input type="checkbox" data-k="${l.key}" ${this.hidden[l.key] ? "" : "checked"}> ${l.label}</label>`);
    rows.push(`<label><input type="checkbox" data-k="labels" ${this.hidden.labels ? "" : "checked"}> ${T("Labels")}</label>`);
    this.panel.innerHTML = `<div class="v3d-title">${T("Layers")}</div>${rows.join("")}` +
      `<div class="v3d-btns"><button data-view="iso">3D</button><button data-view="front">${T("Front")}</button>` +
      `<button data-view="top">${T("Top")}</button><button data-view="png" title="${T("Save image")}">PNG</button></div>`;
  }

  renderResults(summary) {
    if (!summary) { this.results.style.display = "none"; return; }
    this.results.style.display = "";
    const groups = {};
    for (const c of summary.checks) {
      const key = c.description.split(":")[0];
      if (!groups[key] || c.utilisation > groups[key].utilisation) groups[key] = c;
    }
    const rows = Object.values(groups).sort((a, b) => b.utilisation - a.utilisation).slice(0, 14);
    const ok = summary.passed;
    this.results.innerHTML = `<div class="v3d-title ${ok ? "pass" : "fail"}">${ok ? "✔ " + T("All checks pass") : "✖ " + T("Design fails")}</div>` +
      rows.map((c) => {
        const u = Math.min(c.utilisation, 9.99);
        const w = (Math.min(u, 1.2) / 1.2) * 100;
        const tip = (c.description + (c.hint ? "\n💡 " + c.hint : "")).replace(/"/g, "&quot;");
        return `<div class="v3d-row" title="${tip}"><span>${c.description.split(":")[0]}</span>` +
          `<span class="bar"><i class="${c.passed ? "pass" : "fail"}" style="width:${w}%"></i></span><b>${u.toFixed(2)}</b></div>`;
      }).join("");
  }

  setView(kind) {
    const b = this.box;
    if (!b) return;
    const size = b.getSize(new THREE.Vector3());
    const c = b.getCenter(new THREE.Vector3());
    if (kind && typeof kind === "object") kind = "iso";  // auto-fit is more reliable
    const m = Math.max(size.x, size.y, size.z);
    const d = m * 1.6 + Math.min(2, m * 0.6);
    const pos = {
      iso: [c.x - d * 0.75, c.y + d * 0.6, c.z + d * 0.95],
      front: [c.x, c.y, c.z + d * 1.4],
      top: [c.x, c.y + d * 1.6, c.z + 0.001],
    }[kind] || [c.x + d, c.y + d, c.z + d];
    this.camera.position.set(...pos);
    this.controls.target.copy(c);
    this.controls.update();
  }
}

// One viewer per host element: the calculation preview ("viewer3d") and the
// Erisma Structure workspace ("st-3d") each have their own.
const viewers = {};
function show(detail) {
  const id = detail?.host || "viewer3d";
  const host = document.getElementById(id);
  if (!host || !detail?.model) return;
  viewers[id] ||= new Viewer(host);
  viewers[id].load(detail.model, detail.summary);
  viewers[id].resize();
}
window.addEventListener("erisma:model3d", (e) => show(e.detail));
window.addEventListener("erisma:show3d", (e) => viewers[e.detail?.host || "viewer3d"]?.resize());
window.addEventListener("erisma:layers", (e) => {
  const v = viewers[e.detail?.host || "viewer3d"];
  if (!v) return;
  Object.entries(e.detail.show || {}).forEach(([k, on]) => { v.hidden[k] = !on; });
  v.applyVisibility();
  v.panel.querySelectorAll("input[data-k]").forEach((i) => { i.checked = !v.hidden[i.dataset.k]; });
});
window.addEventListener("erisma:highlight", (e) => viewers[e.detail?.host || "viewer3d"]?.highlight(e.detail.picks));
if (window.__erismaModel) show(window.__erismaModel);
