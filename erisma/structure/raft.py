"""Design of a raft foundation analysed with MITC4 plates on Winkler springs.

* **Bending** — Wood–Armer design moments (Wood 1968, the method of EN 1992 practice and
  of commercial FE design programs): bottom m_x* = m_x + |m_xy|, top m_x* = −(m_x − |m_xy|)
  (likewise for y).  A basic mesh is chosen per face and direction for the bulk of the raft,
  with additional bars where the demand exceeds it (EN 1992-1-1 6.1, 9.3.1.1 minimum
  and maximum spacing).
* **Shear** — EN 1992-1-1 6.2.2 (no shear reinforcement) away from the columns.
* **Punching** — EN 1992-1-1 6.4 at every column: basic control perimeter u₁ at 2d,
  clipped by the raft edges; V_Ed,red = V_Ed − ΔV_Ed with the soil reaction inside the
  perimeter (6.4.4(2)); β = 1.15 / 1.4 / 1.5 (6.4.3(6)); v_Ed,0 at the column face ≤ v_Rd,max.
* **Soil** — EN 1997-1 6.5.2 / Annex D: average pressure ≤ q_Rd of the B × L raft with shape
  factors, every combination of the National Annex; seismic with EN 1998-5 material factors.
* **Settlement** — EN 1997-1 Annex H: relative rotation between columns ≤ 1/500 and total
  settlement ≤ 50 mm under the quasi-permanent combination G + ψ₂Q.

Seismic action effects on the foundation include γ_Rd·Ω (EN 1998-1 4.4.2.6).
"""

from __future__ import annotations

import math

import numpy as np

from ..design.ec2 import section_capacity
from ..design.geotech import bearing_factors

KEYS = ("Mx", "My", "Mxy", "Qx", "Qy")
MESH = [(d, s) for d in ("12", "14", "16", "20", "25") for s in (250.0, 200.0, 150.0, 125.0, 100.0)]


def _vec(f: dict) -> np.ndarray:
    return np.array([f[k] for k in KEYS], dtype=float)


def _seismic_env(seis, pid: str) -> np.ndarray:
    """|E| of the plate resultants (modal CQC, torsion, θ, EX + 0.3 EY)."""
    out = {}
    for d in ("X", "Y"):
        r = seis.rs[d]
        modal = np.array([_vec(m.plate_forces(pid)) for m in r.modal])
        e = r.combine(modal) + np.abs(_vec(seis.torsion[d].plate_forces(pid)))
        out[d] = seis.amplification[d] * e
    return np.maximum(out["X"] + 0.3 * out["Y"], 0.3 * out["X"] + out["Y"])


def _as_req(M: float, d: float, fcd: float, fyd: float) -> float:
    """Tension steel per mm width for moment M (Nmm/mm), rectangular block (EN 1992-1-1 3.1.7)."""
    if M <= 0:
        return 0.0
    # 0.8 x f_cd (d − 0.4 x) = M  (λ = 0.8, η = 1)
    disc = 0.64 * d**2 - 1.28 * M / fcd
    if disc < 0:
        return math.inf
    x = (0.8 * d - math.sqrt(disc)) / 0.64
    if x > 0.45 * d:                     # EN 1992-1-1 5.6.3(2): keep the section ductile
        return math.inf
    return 0.8 * x * fcd / fyd


def _mesh_area(c) -> float:
    return math.pi * float(c[0]) ** 2 / 4 / c[1]   # mm²/mm


def bearing_rect(B: float, L: float, D: float, phi: float, c: float, gamma: float,
                 g_phi: float = 1.0, g_c: float = 1.0, g_R: float = 1.0) -> float:
    """EN 1997-1 Annex D.4, drained, vertical central load, shape factors for B × L (B ≤ L)."""
    B, L = min(B, L), max(B, L)
    phid = math.atan(math.tan(math.radians(phi)) / g_phi)
    Nq, Nc, Ng = bearing_factors(phid)
    sq = 1 + B / L * math.sin(phid)
    sg = 1 - 0.3 * B / L
    sc = (sq * Nq - 1) / (Nq - 1)
    return (c / g_c * Nc * sc + gamma * D * Nq * sq + 0.5 * gamma * B * Ng * sg) / g_R


def _perimeter(cx, cy, c1, c2, r, bounds, n=720):
    """Length of the rounded-rectangle perimeter at distance r around a c1 × c2 column at
    (cx, cy) inside the raft ``bounds``, and the area it encloses inside the raft."""
    x0, x1, y0, y1 = bounds
    pts = []
    hx, hy = c1 / 2, c2 / 2
    for k in range(n):
        t = 2 * math.pi * k / n
        dx, dy = math.cos(t), math.sin(t)
        px = cx + math.copysign(hx, dx) + r * dx
        py = cy + math.copysign(hy, dy) + r * dy
        pts.append((px, py))
    pts.append(pts[0])
    inside = lambda p: x0 - 1e-6 <= p[0] <= x1 + 1e-6 and y0 - 1e-6 <= p[1] <= y1 + 1e-6  # noqa
    length = sum(math.dist(a, b) for a, b in zip(pts[:-1], pts[1:]) if inside(a) and inside(b))
    straight = 2 * (c1 + c2)                    # the flat parts are not sampled exactly
    full = straight + 2 * math.pi * r
    sampled = sum(math.dist(a, b) for a, b in zip(pts[:-1], pts[1:]))
    length *= full / sampled
    return length


def design_raft(raft: dict, an, res, uls, quasi, seis, ef: float, columns: dict, walls: dict,
                concrete: str, fyk: float, annex, soil: dict, D: float, psi2: float,
                cover: float = 50.0) -> dict:
    """``columns``: grid → (node, member, c1, c2); ``walls``: grid → (node, L, t, dir)."""
    fck = float(concrete.split("/")[0][1:])
    fcd = annex.alpha_cc * fck / annex.gamma_c
    fyd = fyk / annex.gamma_s
    fctm = 0.30 * fck ** (2 / 3)
    t = raft["t"]
    plates = raft["plates"]
    # ---- design moments per element (Wood–Armer), ULS and seismic
    rows = []
    for p in plates:
        pid = p["id"]
        cases = [_vec(uls.plate_forces(pid))]
        if seis is not None:
            q0, e = _vec(quasi.plate_forces(pid)), _seismic_env(seis, pid) * ef
            cases += [q0 + e * s for s in (np.array([1, 1, 1, 1, 1]), np.array([-1, -1, -1, -1, -1]))]
            cases.append(np.concatenate([q0[:2] + e[:2], [abs(q0[2]) + e[2]], q0[3:] + e[3:]]))
            cases.append(np.concatenate([q0[:2] - e[:2], [abs(q0[2]) + e[2]], q0[3:] - e[3:]]))
        bx = max(c[0] + abs(c[2]) for c in cases)
        by = max(c[1] + abs(c[2]) for c in cases)
        tx = max(-(c[0] - abs(c[2])) for c in cases)
        ty = max(-(c[1] - abs(c[2])) for c in cases)
        V = max(max(abs(c[3]), abs(c[4])) for c in cases)
        rows.append({"id": pid, "x0": p["x0"], "x1": p["x1"], "y0": p["y0"], "y1": p["y1"],
                     "bx": max(bx, 0.0), "by": max(by, 0.0), "tx": max(tx, 0.0),
                     "ty": max(ty, 0.0), "V": V})
    # ---- reinforcement: basic mesh (85th percentile) + additional bars where needed
    out_mesh, fail = {}, []
    for face, keys in (("bottom", ("bx", "by")), ("top", ("tx", "ty"))):
        for k, direction in zip(keys, ("x", "y")):
            dd = t - cover - (12 if direction == "x" else 30)   # x bars outer, y inner layer
            req = np.array([_as_req(r[k], dd, fcd, fyd) for r in rows])
            As_min = max(0.26 * fctm / fyk, 0.0013) * dd           # 9.2.1.1 / 9.3.1.1
            s_max = min(2 * t, 250.0)                               # 9.3.1.1(3)
            finite = req[np.isfinite(req)]
            base_need = max(np.percentile(finite, 85) if len(finite) else 0.0, As_min)
            base = next((c for c in MESH if c[1] <= s_max and _mesh_area(c) >= base_need), MESH[-1])
            peak = float(np.max(req)) if len(req) else 0.0
            add = None
            if peak > _mesh_area(base):
                add = next((c for c in MESH if c[1] == base[1]
                            and _mesh_area(base) + _mesh_area(c) >= peak), None)
                if add is None:
                    fail.append(f"{face} {direction}")
                    add = MESH[-1]
            cap = _mesh_area(base) + (_mesh_area(add) if add else 0.0)
            for r, a in zip(rows, req):
                r[f"u_{k}"] = a / _mesh_area(base) if _mesh_area(base) else 0.0
                r[f"add_{k}"] = bool(a > _mesh_area(base))
            out_mesh[(face, direction)] = {"base": base, "add": add, "d": dd, "peak": peak,
                                           "As_min": As_min, "cap": cap,
                                           "MRd": section_capacity(1000, dd, cap * 1000, fcd,
                                                                   fyd)[0] / 1000}
    for r in rows:
        r["util"] = max(r["u_bx"], r["u_by"], r["u_tx"], r["u_ty"])
    # ---- one-way shear away from the columns / walls (punching governs there)
    rho = min(_mesh_area(out_mesh[("bottom", "x")]["base"]),
              _mesh_area(out_mesh[("top", "x")]["base"])) / (t - cover - 12)
    d = t - cover - 21
    k = min(1 + math.sqrt(200 / d), 2.0)
    vmin = 0.035 * k**1.5 * math.sqrt(fck)
    vRdc = max(0.18 / annex.gamma_c * k * (100 * min(rho, 0.02) * fck) ** (1 / 3), vmin) * d
    zones = [(an.model.nodes[c[0]].x, an.model.nodes[c[0]].y, max(c[2], c[3]) / 2 + 2 * d)
             for c in columns.values()]
    zones += [(an.model.nodes[w[0]].x, an.model.nodes[w[0]].y, w[1] / 2 + 2 * d)
              for w in walls.values()]
    shear = max(((r["V"], r["id"]) for r in rows
                 if all(math.hypot((r["x0"] + r["x1"]) / 2 - x, (r["y0"] + r["y1"]) / 2 - y) > rz
                        for x, y, rz in zones)), default=(0.0, ""))
    # ---- punching at the columns
    bounds = raft["bounds"]
    trib = raft["trib"]
    rho_p = min(math.sqrt(_mesh_area(out_mesh[("bottom", "x")]["base"]) / d *
                          _mesh_area(out_mesh[("bottom", "y")]["base"]) / d), 0.02)
    vRd_p = max(0.18 / annex.gamma_c * k * (100 * rho_p * fck) ** (1 / 3), vmin)
    nu = 0.6 * (1 - fck / 250)
    vRd_max = annex.punch_vmax * nu * fcd
    punch = []
    for g, (node, mid, c1, c2) in columns.items():
        n = an.model.nodes[node]
        u1 = _perimeter(n.x, n.y, c1, c2, 2 * d, bounds)
        full = 2 * (c1 + c2) + 2 * math.pi * 2 * d
        beta = 1.15 if u1 > 0.95 * full else (1.4 if u1 > 0.6 * full else 1.5)
        inside = [m for m in trib
                  if math.hypot(max(abs(an.model.nodes[m].x - n.x) - c1 / 2, 0),
                                max(abs(an.model.nodes[m].y - n.y) - c2 / 2, 0)) <= 2 * d]
        cases = []
        Nu = -uls.forces(mid, 2)["N"][0]
        dVu = sum(uls.reaction(m)[2] for m in inside)
        cases.append(("ULS", Nu, dVu))
        if seis is not None:
            f = quasi.forces(mid, 2)
            env = seis.member_envelope(mid)
            Ns = -f["N"][0] + ef * env[0]
            dVs = sum(quasi.reaction(m)[2] - ef * seis.reaction_envelope(m)[2] for m in inside)
            cases.append(("G+ψ2Q+ΩE", Ns, dVs))
        worst = None
        for name, V, dV in cases:
            Vred = max(V - max(dV, 0.0), 0.0)
            vEd = beta * Vred / (u1 * d)
            v0 = beta * V / (2 * (c1 + c2) * d)
            u = max(vEd / vRd_p, v0 / vRd_max)
            if worst is None or u > worst["util"]:
                worst = {"grid": g, "combo": name, "V": V, "dV": dV, "u1": u1, "beta": beta,
                         "vEd": vEd, "vRd": vRd_p, "v0": v0, "vRdmax": vRd_max, "util": u}
        punch.append(worst)
    # ---- soil pressure (average over the raft) and uplift
    x0, x1, y0, y1 = bounds
    Bx, By = x1 - x0, y1 - y0
    area = Bx * By
    soil_rows = []
    approach = annex.approach("National Annex")
    for combo in annex.combinations(approach):
        gG, _f, gQ, gphi, gc, gRv = annex.combos[combo][:6]
        qRd = bearing_rect(Bx, By, D, soil["phi"], soil["c"], soil["gamma"], gphi, gc, gRv)
        Rtot = sum(gG * res["G"].reaction(m)[2] + gQ * res["Q"].reaction(m)[2] for m in trib)
        peak = max((gG * res["G"].reaction(m)[2] + gQ * res["Q"].reaction(m)[2]) / A
                   for m, A in trib.items())
        soil_rows.append({"combo": combo, "p": Rtot / area, "peak": peak, "qRd": qRd})
    uplift = None
    if seis is not None:
        qRd = bearing_rect(Bx, By, D, soil["phi"], soil["c"], soil["gamma"],
                           annex.seismic_gamma_phi, annex.seismic_gamma_c, 1.0)
        Rtot = sum(quasi.reaction(m)[2] for m in trib)
        pk = max(((quasi.reaction(m)[2] + ef * seis.reaction_envelope(m)[2]) / A, m)
                 for m, A in trib.items())
        lo = min(((quasi.reaction(m)[2] - ef * seis.reaction_envelope(m)[2]) / A, m)
                 for m, A in trib.items())
        soil_rows.append({"combo": "G+ψ2Q+ΩE", "p": Rtot / area, "peak": pk[0], "qRd": qRd})
        if lo[0] < 0:
            uplift = {"node": lo[1], "p": lo[0]}
    # ---- settlement (quasi-permanent G + ψ2Q), EN 1997-1 Annex H
    w = {g: -quasi.displacement(c[0])[2] for g, c in {**columns, **{
        g: (w_[0],) for g, w_ in walls.items()}}.items()}
    pos = {g: (an.model.nodes[c[0]].x, an.model.nodes[c[0]].y) for g, c in {**columns, **{
        g: (w_[0],) for g, w_ in walls.items()}}.items()}
    rot, pair = 0.0, ("", "")
    for a, (xa, ya) in pos.items():          # adjacent supports along the grid lines
        for axis in (0, 1):
            cands = [(abs(pb[axis] - pos[a][axis]), b) for b, pb in pos.items() if b != a
                     and abs(pb[1 - axis] - pos[a][1 - axis]) < 1 and pb[axis] > pos[a][axis]]
            if cands:
                L, b = min(cands)
                r_ = abs(w[a] - w[b]) / L
                if r_ > rot:
                    rot, pair = r_, (a, b)
    settle = {"w_max": max(w.values()) if w else 0.0, "rot": rot, "pair": pair}
    return {"elements": rows, "mesh": out_mesh, "fail": fail, "shear": {"V": shear[0],
            "id": shear[1], "VRd": vRdc, "d": d}, "punching": punch, "soil": soil_rows,
            "uplift": uplift, "settlement": settle, "t": t, "area": area}
