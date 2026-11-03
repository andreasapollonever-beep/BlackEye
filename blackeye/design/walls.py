"""Shared engine for earth-retaining walls (cantilever, gravity, ...).

Coordinate system (per unit length of wall, base units N and mm): x is
horizontal from the toe (front edge of the base) towards the retained soil,
z is vertical upwards from the underside of the base.  Earth pressures act on
a *virtual back* — the vertical plane through the rear edge of the base — so
soil above the heel / back batter moves with the wall.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import numpy as np

from ..core import Calculation, DesignModule, Field, InputError
from ..core.units import from_base
from ..report.scene3d import PALETTE, Scene3D
from ..report.svg import wall_section
from .geotech import (bearing_factors, clip_z, k_mononobe_okabe, ka_coulomb,
                      linear_resultant, poly_props)

GAMMA_W = 9.81e-6  # N/mm³

#            γG,unf γG,fav  γQ    γφ'   γc'   γR,v  γR,h   (EN 1997-1 Annex A)
COMBOS = {
    "DA1-C1": (1.35, 1.00, 1.50, 1.00, 1.00, 1.00, 1.00),
    "DA1-C2": (1.00, 1.00, 1.30, 1.25, 1.25, 1.00, 1.00),
    "DA2": (1.35, 1.00, 1.50, 1.00, 1.00, 1.40, 1.10),
    "DA3": (1.00, 1.00, 1.30, 1.25, 1.25, 1.00, 1.00),
}
APPROACHES = {"DA1": ["DA1-C1", "DA1-C2"], "DA2": ["DA2"], "DA3": ["DA3"]}
EQU = (1.10, 0.90, 1.50, 1.25, 1.25)  # γG,dst γG,stb γQ,dst γφ' γc'

HINT_SLIDING = ("Increase the base width (longer heel adds stabilising soil weight), add a "
                "shear key below the base, or improve drainage to remove water pressure.")
HINT_BEARING = ("Increase the base width or the toe length to spread the load and bring the "
                "resultant closer to the centre of the base.")
HINT_ECC = ("Lengthen the toe (or heel) so that the resultant falls inside the middle part of "
            "the base.")
HINT_OVT = "Increase the toe length or the heel length (more soil weight behind the wall)."


# ----------------------------------------------------------------- actions
@dataclass
class Comp:
    """A characteristic action on the wall (per unit length)."""
    name: str
    H: float = 0.0     # horizontal, positive towards the toe (destabilising)
    zH: float = 0.0
    V: float = 0.0     # vertical, positive downwards
    xV: float = 0.0
    kind: str = "G"    # G permanent | Q variable | A accidental/seismic (unfactored)
    role: str = "weight"  # weight | thrust | water | uplift | inertia
    inertia: bool = True  # include in seismic inertia (weights only)


@dataclass
class Totals:
    H: float
    V: float
    M_stb: float
    M_dst: float
    rows: list

    @property
    def x_R(self) -> float:
        return (self.M_stb - self.M_dst) / self.V if self.V > 0 else 0.0


def factored(comps: list[Comp], g_unf: float, g_fav: float, gq: float,
             max_vertical: bool = False) -> Totals:
    """Apply partial factors. ``max_vertical`` makes vertical actions unfavourable."""
    H = V = Ms = Md = 0.0
    rows = []
    for c in comps:
        if c.kind == "A":
            fH = fV = 1.0
        elif c.role == "uplift":
            fH, fV = 0.0, (g_fav if max_vertical else g_unf)
        else:
            unf = g_unf if c.kind == "G" else gq
            fav = g_fav if c.kind == "G" else 0.0
            fH = unf
            fV = unf if max_vertical else fav
        h, v = fH * c.H, fV * c.V
        H += h
        V += v
        Md += h * c.zH
        if v >= 0:
            Ms += v * c.xV
        else:
            Md += -v * c.xV
        rows.append((c, fH, fV, h, v))
    return Totals(H, V, Ms, Md, rows)


# ---------------------------------------------------------------- geometry
class WallGeometry:
    """Base class. Subclasses set the polygons and key coordinates."""

    concrete: list[tuple[str, list]]   # [(name, polygon)]
    B: float          # base width
    tb: float         # level of base top (soil over heel starts here)
    top: float        # level of wall top
    x0: float         # x where the retained surface starts (back of wall top)
    xbb: float        # x of the back face at level tb
    x_front: float    # x of the front face at level tb (end of toe)
    df: float         # soil depth over toe above tb

    def __init__(self, inp: dict) -> None:
        self.beta = math.radians(inp["beta"])
        self.gb, self.gsat, self.gf = inp["gamma_b"], inp["gamma_sat"], inp["gamma_f"]
        self.hw, self.L = inp["h_w"], inp["length"]

    def finish(self) -> None:
        self.hv = self.top + (self.B - self.x0) * math.tan(self.beta)
        self.far = self.B + max(2000.0, 0.6 * self.hv)
        self.D = self.tb + self.df

    def zs(self, x: float) -> float:
        return self.top + max(x - self.x0, 0) * math.tan(self.beta)

    @property
    def back_soil(self) -> list:
        pts = [(self.xbb, self.tb), (self.B, self.tb), (self.B, self.zs(self.B)),
               (self.x0, self.top)]
        out = []
        for p in pts:
            if not out or abs(p[0] - out[-1][0]) + abs(p[1] - out[-1][1]) > 1e-9:
                out.append(p)
        return out

    @property
    def front_soil(self) -> list | None:
        if self.df <= 0 or self.x_front <= 0:
            return None
        return [(0, self.tb), (self.x_front, self.tb), (self.x_front, self.tb + self.df),
                (0, self.tb + self.df)]

    def sigma_v(self, z: float) -> float:
        """Effective vertical stress on the virtual back at height z."""
        depth = self.hv - z
        if self.hw > 0 and z < self.hw:
            dw = self.hv - self.hw
            return self.gb * dw + (self.gsat - GAMMA_W) * (depth - dw)
        return self.gb * depth

    def earth_force(self, K: float) -> tuple[float, float]:
        """Horizontal earth thrust K·σ'v on the virtual back and its height."""
        zk = sorted({0.0, min(self.hw, self.hv), self.hv})
        F = M = 0.0
        for z1, z2 in zip(zk[:-1], zk[1:]):
            f, zc = linear_resultant(z1, K * self.sigma_v(z1), z2, K * self.sigma_v(z2))
            F += f
            M += f * zc
        return F, (M / F if F else self.hv / 3)

    def base_pressure(self, t: Totals) -> list[tuple[float, float]]:
        """Linear (no tension) contact pressure q(x) for the given design totals."""
        V, xr, B = t.V, t.x_R, self.B
        e = B / 2 - xr
        xs = np.linspace(0, B, 41)
        if abs(e) <= B / 6:
            q = V / B * (1 + 12 * e * (B / 2 - xs) / B**2)
        elif e > 0:
            Lc = 3 * xr
            q = np.where(xs < Lc, 2 * V / Lc * (1 - xs / Lc), 0.0) if Lc > 0 else 0 * xs
        else:
            Lc = 3 * (B - xr)
            q = np.where(xs > B - Lc, 2 * V / Lc * (1 - (B - xs) / Lc), 0.0)
        return list(zip(xs.tolist(), np.maximum(q, 0).tolist()))


# ------------------------------------------------------------------ fields
def soil_fields() -> list[Field]:
    return [
        Field("beta", "Backfill slope β", "°", 0.0, min=0, max=40, group="Retained soil"),
        Field("phi_b", "Backfill φ'k", "°", 30.0, min=15, max=45, group="Retained soil"),
        Field("gamma_b", "Backfill γ", "kN/m³", 18.0, min=10, group="Retained soil"),
        Field("gamma_sat", "Backfill γsat", "kN/m³", 20.0, min=10, group="Retained soil"),
        Field("q", "Surcharge on backfill (variable)", "kN/m²", 10.0, min=0,
              group="Retained soil", help="e.g. 10 kN/m² for light traffic or storage."),
        Field("h_w", "Water level above base underside", "m", 0.0, min=0,
              group="Retained soil", help="0 = drained backfill (no water pressure)."),
        Field("phi_f", "Foundation φ'k", "°", 32.0, min=10, max=45, group="Foundation soil"),
        Field("c_f", "Foundation c'k", "kN/m²", 0.0, min=0, group="Foundation soil"),
        Field("gamma_f", "Foundation γ", "kN/m³", 19.0, min=10, group="Foundation soil"),
        Field("k_base", "Base friction factor k (tan δ = k tan φ')", "", 1.0, min=0.3, max=1.0,
              group="Foundation soil",
              help="1.0 cast in situ, 2/3 precast (EN 1997-1 6.5.3(10))."),
        Field("approach", "Design approach", kind="choice", choices=list(APPROACHES),
              default="DA1", group="Design basis",
              help="Check the National Annex (DA1 recommended in many countries)."),
        Field("seismic", "Include seismic design (EN 1998-5)", kind="bool", default=True,
              group="Seismic"),
        Field("ag", "Design ground acceleration αgR·γI", "", 0.16, min=0, max=0.6,
              group="Seismic", help="In g. Greece: Zone I 0.16, Zone II 0.24, Zone III 0.36."),
        Field("S", "Soil factor S", "", 1.2, min=1.0, max=1.8, group="Seismic",
              help="EN 1998-1 Table 3.2: ground A 1.0, B 1.2, C 1.15, D 1.35, E 1.4."),
        Field("r", "Displacement factor r", kind="choice", choices=["1.0", "1.5", "2.0"],
              default="2.0", group="Seismic",
              help="EN 1998-5 Table 7.1: 2.0 free gravity walls allowing ~300α·S mm, "
                   "1.0 for walls that cannot move (e.g. propped)."),
        Field("psi2", "ψ2 for surcharge", "", 0.3, min=0, max=1, group="Seismic"),
    ]


# ------------------------------------------------------------------ module
class WallModule(DesignModule):
    """Template for wall modules: subclasses provide geometry + structural design."""

    @classmethod
    def make_geometry(cls, inp: dict) -> WallGeometry:  # pragma: no cover
        raise NotImplementedError

    @classmethod
    def record_geometry(cls, calc: Calculation, g: WallGeometry, inp: dict) -> None:
        raise NotImplementedError  # pragma: no cover

    @classmethod
    def structural(cls, calc: Calculation, g: WallGeometry, inp: dict,
                   weights: list[Comp], seis: dict | None) -> None:
        pass

    # ---------------------------------------------------------------- run
    @classmethod
    def run(cls, calc: Calculation, inp: dict) -> None:
        g = cls.make_geometry(inp)
        if inp["h_w"] > g.hv + 1e-6:
            raise InputError("Water level is above the retained ground surface", "h_w")
        if math.radians(inp["beta"]) >= math.atan(math.tan(math.radians(inp["phi_b"])) / 1.25):
            raise InputError("Backfill slope is too steep for the design angle of shearing "
                             "resistance (β must be < φ'd)", "beta")
        cls.record_geometry(calc, g, inp)
        fig_index = len(calc.items)
        cls._soil_section(calc, g, inp)
        weights = cls._weights(calc, g, inp)
        gov: dict = {"util": -1}

        for name in APPROACHES[inp["approach"]]:
            gu, gf, gq, gphi, gc, gRv, gRh = COMBOS[name]
            calc.heading(calc.tr("Stability — {name} (EN 1997-1 Annex A)", name=name))
            calc.text("Partial factors: γ_G = {gu} (unfav.) / {gf} (fav.), γ_Q = {gq}, "
                      "γ_φ' = {gphi}, γ_c' = {gc}, γ_R,v = {gRv}, γ_R,h = {gRh}.",
                      gu=gu, gf=gf, gq=gq, gphi=gphi, gc=gc, gRv=gRv, gRh=gRh)
            thrust, _ = cls._thrust(calc, g, inp, gphi, record=True)
            cls._stability(calc, g, inp, name, weights + thrust, gu, gf, gq, gphi, gc, gRv,
                           gRh, gov)

        calc.heading("Overturning — EQU (EN 1997-1 2.4.7.2)")
        dst, stb, gq, gphi, _ = EQU
        calc.text("Partial factors: γ_G,dst = {dst}, γ_G,stb = {stb}, γ_Q,dst = {gq}, "
                  "γ_φ' = {gphi}.", dst=dst, stb=stb, gq=gq, gphi=gphi)
        thrust, _ = cls._thrust(calc, g, inp, gphi, record=True)
        t = factored(weights + thrust, dst, stb, gq)
        cls._table(calc, t, "EQU — design actions about the toe")
        Md = calc.formula("M_dst,d", "Σ H_d z + Σ U_d x", t.M_dst, "kNm/m",
                          "Destabilising moment about toe")
        Ms = calc.formula("M_stb,d", "Σ V_d x", t.M_stb, "kNm/m", "Stabilising moment about toe")
        calc.check("Overturning: M_dst,d ≤ M_stb,d", Md, Ms, "kNm/m", "EN 1997-1 Eq. 2.4",
                   hint=HINT_OVT)

        seis = None
        if inp["seismic"] and inp["ag"] > 0:
            seis = cls._seismic(calc, g, inp, weights, gov)

        cls.structural(calc, g, inp, weights, seis)

        pressures = cls._pressure_profiles(g, inp, seis)
        calc.model3d = cls._scene(calc, g, inp, weights, pressures, gov)
        calc.figure(wall_section(cls._outline(g), pressures, gov.get("bearing", []),
                                 calc.tr("pressures in kN/m² (characteristic)")),
                    "Section with characteristic earth/water pressures and governing design "
                    "base pressure")
        calc.items.insert(fig_index, calc.items.pop())

    # ------------------------------------------------------------- pieces
    @staticmethod
    def _soil_section(calc: Calculation, g: WallGeometry, inp: dict) -> None:
        calc.heading("Soil and materials")
        calc.table(["", "φ'k [°]", "c'k [kN/m²]", "γ [kN/m³]", "γsat [kN/m³]"],
                   [[calc.tr("Retained backfill"), f"{inp['phi_b']:g}", "0",
                     f"{from_base(g.gb, 'kN/m³'):g}", f"{from_base(g.gsat, 'kN/m³'):g}"],
                    [calc.tr("Foundation soil"), f"{inp['phi_f']:g}",
                     f"{from_base(inp['c_f'], 'kN/m²'):g}",
                     f"{from_base(g.gf, 'kN/m³'):g}", "—"]],
                   caption="Characteristic soil parameters")
        calc.input("q_k", inp["q"], "kN/m²", "Variable surcharge on retained surface")
        if g.hw > 0:
            calc.input("h_w", g.hw, "m", "Groundwater level above base underside")
            calc.note("Water is assumed behind the wall only; uplift varies linearly from "
                      "γ_w h_w at the heel to zero at the toe.")
        else:
            calc.note("Drained backfill — no water pressure (provide drainage/weep holes).")
        calc.text("Wall friction on the virtual back δ = β (EN 1997-1 Annex C). Passive "
                  "resistance in front of the wall is conservatively ignored.")

    @staticmethod
    def _weights(calc: Calculation, g: WallGeometry, inp: dict) -> list[Comp]:
        calc.heading("Characteristic vertical actions")
        out: list[Comp] = []

        def add(name, pts, gamma, kind="G", inertia=True):
            a, cx, cz = poly_props(pts)
            if a > 1e-6:
                out.append(Comp(calc.tr(name), V=a * gamma, xV=cx, zH=cz, kind=kind,
                                role="weight", inertia=inertia))

        for name, pts in g.concrete:
            add(name, pts, inp["gamma_c"])
        soil = g.back_soil
        if g.hw > g.tb:
            add("Backfill over heel (above water)", clip_z(soil, g.hw, False), g.gb)
            add("Backfill over heel (below water)", clip_z(soil, g.hw, True), g.gsat)
        else:
            add("Backfill over heel", soil, g.gb)
        if g.front_soil:
            add("Soil over toe", g.front_soil, g.gf, inertia=False)
        qw = g.B - g.x0
        if inp["q"] > 0 and qw > 0:
            out.append(Comp(calc.tr("Surcharge over heel"), V=inp["q"] * qw, xV=g.x0 + qw / 2,
                            zH=g.hv, kind="Q", role="weight", inertia=False))
        if g.hw > 0:
            out.append(Comp(calc.tr("Uplift"), V=-GAMMA_W * g.hw * g.B / 2, xV=2 * g.B / 3,
                            kind="G", role="uplift", inertia=False))
        calc.table(["Action", "Type", "V [kN/m]", "x from toe [m]", "M [kNm/m]"],
                   [[c.name, c.kind, f"{from_base(c.V, 'kN/m'):.2f}",
                     f"{from_base(c.xV, 'm'):.3f}", f"{from_base(c.V * c.xV, 'kNm/m'):.2f}"]
                    for c in out], caption="Weights per metre run (G permanent, Q variable)")
        return out

    @staticmethod
    def _thrust(calc: Calculation | None, g: WallGeometry, inp: dict, gphi: float,
                record: bool) -> tuple[list[Comp], dict]:
        tr = calc.tr if calc is not None else (lambda s, **k: s)
        phi_d = math.atan(math.tan(math.radians(inp["phi_b"])) / gphi)
        beta = math.radians(inp["beta"])
        delta = beta
        Ka = ka_coulomb(phi_d, beta, delta)
        cd = math.cos(delta)
        if calc is not None and record:
            calc.formula("φ'_d", "atan(tan φ'_k / γ_φ')", math.degrees(phi_d), "°",
                         "Design angle of shearing resistance (backfill)", dp=2)
            calc.formula("K_a", "cos²φ'_d / [cos δ (1 + √(sin(φ'_d+δ) sin(φ'_d−β) / "
                         "(cos δ cos β)))²]", Ka, "", "Coulomb active coefficient, δ = β",
                         ref="EN 1997-1 Annex C", dp=4)
        Ph, zP = g.earth_force(Ka * cd)
        out = [Comp(tr("Active earth pressure"), H=Ph, zH=zP, V=Ph * math.tan(delta), xV=g.B,
                    kind="G", role="thrust")]
        if inp["q"] > 0:
            pq = Ka * cd * inp["q"]
            out.append(Comp(tr("Surcharge pressure"), H=pq * g.hv, zH=g.hv / 2,
                            V=pq * g.hv * math.tan(delta), xV=g.B, kind="Q", role="thrust"))
        if g.hw > 0:
            out.append(Comp(tr("Water pressure"), H=GAMMA_W * g.hw**2 / 2, zH=g.hw / 3,
                            kind="G", role="water"))
        return out, {"phi_d": phi_d, "Ka": Ka}

    @staticmethod
    def _table(calc: Calculation, t: Totals, caption: str) -> None:
        rows = []
        for c, fH, fV, h, v in t.rows:
            rows.append([c.name, f"{fH:.2f}" if c.H else "", f"{from_base(h, 'kN/m'):.2f}"
                         if c.H else "", f"{from_base(c.zH, 'm'):.2f}" if c.H else "",
                         f"{fV:.2f}" if c.V else "", f"{from_base(v, 'kN/m'):.2f}"
                         if c.V else "", f"{from_base(c.xV, 'm'):.2f}" if c.V else ""])
        rows.append([calc.tr("Total"), "", f"{from_base(t.H, 'kN/m'):.2f}", "", "",
                     f"{from_base(t.V, 'kN/m'):.2f}", ""])
        calc.table(["Action", "γ_H", "H_d [kN/m]", "z [m]", "γ_V", "V_d [kN/m]", "x [m]"],
                   rows, caption=caption)

    @classmethod
    def _stability(cls, calc, g, inp, name, comps, gu, gf, gq, gphi, gc, gRv, gRh,
                   gov) -> None:
        t = factored(comps, gu, gf, gq)
        cls._table(calc, t, calc.tr("{name} — design actions (vertical actions favourable)",
                                    name=name))
        phi_fd = math.atan(math.tan(math.radians(inp["phi_f"])) / gphi)
        c_fd = inp["c_f"] / gc
        calc.formula("φ'_f,d", "atan(tan φ'_f,k / γ_φ')", math.degrees(phi_fd), "°",
                     "Design φ' of foundation soil", dp=2)
        tan_db = calc.formula("tan δ_d", "k tan φ'_f,d", inp["k_base"] * math.tan(phi_fd), "",
                              ref="EN 1997-1 6.5.3(10)", dp=4)
        Hd = calc.formula("H_d", "Σ H_d", t.H, "kN/m", "Design horizontal action")
        Rh = calc.formula("R_h,d", "V'_d tan δ_d / γ_R,h", max(t.V, 0) * tan_db / gRh, "kN/m",
                          "Sliding resistance", ref="Eq. 6.3a")
        calc.check(calc.tr("{name} sliding: H_d ≤ R_h,d", name=name), Hd, Rh, "kN/m",
                   "EN 1997-1 6.5.3", hint=HINT_SLIDING)
        Nq, Nc, Ng = bearing_factors(phi_fd)
        best = None
        for label, mv in (("max V", True), ("min V", False)):
            tt = factored(comps, gu, gf, gq, max_vertical=mv)
            if tt.V <= 0:
                continue
            e = g.B / 2 - tt.x_R
            Bp = g.B - 2 * abs(e)
            iq = ig = ic = 0.0
            if Bp <= 0:
                q_rd, q_ed = 0.0, float("inf")
            else:
                ratio = max(1 - tt.H / (tt.V + Bp * c_fd / math.tan(phi_fd)), 0.0)
                iq, ig = ratio**2, ratio**3
                ic = iq - (1 - iq) / (Nc * math.tan(phi_fd))
                q_rd = (c_fd * Nc * ic + g.gf * g.D * Nq * iq
                        + 0.5 * g.gf * Bp * Ng * ig) / gRv
                q_ed = tt.V / Bp
            u = q_ed / q_rd if q_rd > 0 else float("inf")
            if best is None or u > best[0]:
                best = (u, label, tt, e, Bp, q_ed, q_rd, iq, ig, ic)
        if best is None:
            raise InputError("The wall has no net downward load — check the geometry")
        u, label, tt, e, Bp, q_ed, q_rd, iq, ig, ic = best
        calc.text("Bearing — governing sub-case: vertical actions **{label}** "
                  "(V_d = {V:.1f} kN/m, H_d = {H:.1f} kN/m).", label=label,
                  V=from_base(tt.V, "kN/m"), H=from_base(tt.H, "kN/m"))
        calc.formula("e", "B/2 − (M_stb − M_dst)/V_d", e, "m",
                     "Eccentricity of resultant (+ towards toe)", dp=3)
        calc.check_limit(calc.tr("{name} eccentricity: |e| ≤ B/3", name=name), abs(e),
                         g.B / 3, "m", "EN 1997-1 6.5.4", hint=HINT_ECC)
        calc.formula("B'", "B − 2|e|", Bp, "m", "Effective base width")
        calc.formula("N_q", "e^(π tan φ') tan²(45° + φ'/2)", Nq, "",
                     calc.tr("Bearing factors: Nc = {Nc:.2f}, Nγ = {Ng:.2f}", Nc=Nc, Ng=Ng),
                     dp=2)
        calc.formula("i_q", "(1 − H/(V + B'c' cot φ'))^m, m = 2", iq, "",
                     calc.tr("iγ = {ig:.3f}, ic = {ic:.3f} (strip footing)", ig=ig, ic=ic),
                     ref="D.4(7)", dp=3)
        calc.formula("q_Rd", "(c'N_c i_c + q'N_q i_q + 0.5γ'B'N_γ i_γ) / γ_R,v", q_rd, "kN/m²",
                     calc.tr("Design bearing resistance (q' = γ D, D = {D:.2f} m)",
                             D=from_base(g.D, "m")), ref="EN 1997-1 Annex D.4")
        calc.formula("q_Ed", "V_d / B'", q_ed, "kN/m²", "Design bearing pressure")
        calc.check(calc.tr("{name} bearing: q_Ed ≤ q_Rd", name=name), q_ed, q_rd, "kN/m²",
                   "EN 1997-1 6.5.2", hint=HINT_BEARING)
        if u > gov["util"]:
            gov.update({"util": u, "name": f"{name} ({label})", "e": e, "B_eff": Bp,
                        "q_Ed": q_ed, "x_R": tt.x_R, "bearing": g.base_pressure(tt)})

    @classmethod
    def _seismic(cls, calc, g, inp, weights, gov) -> dict:
        calc.heading("Seismic design situation (EN 1998-5 §7.3 and Annex E)")
        alpha = calc.input("α", inp["ag"], "", "Design ground acceleration ratio a_g/g", dp=3)
        S = calc.input("S", inp["S"], "", "Soil factor", dp=2)
        r = calc.input("r", float(inp["r"]), "", "Displacement factor (Table 7.1)", dp=1)
        kh = calc.formula("k_h", "α S / r", alpha * S / r, "", ref="EN 1998-5 Eq. 7.1", dp=4)
        kv = calc.formula("k_v", "±0.5 k_h", 0.5 * kh, "", ref="Eq. 7.2", dp=4)
        gphi = 1.25
        phi_d = math.atan(math.tan(math.radians(inp["phi_b"])) / gphi)
        calc.formula("φ'_d", "atan(tan φ'_k / γ_φ'), γ_φ' = 1.25", math.degrees(phi_d), "°",
                     ref="EN 1998-5 3.1(3)", dp=2)
        beta = math.radians(inp["beta"])
        delta = beta
        Ka = ka_coulomb(phi_d, beta, delta)
        if g.hw > 0:
            calc.warn("Seismic thrust is computed for dry backfill plus hydrostatic water "
                      "pressure (simplified; see EN 1998-5 E.6–E.8 for saturated soil).")
        result = None
        for sgn, label in ((-1, "k_v upwards"), (1, "k_v downwards")):
            kvs = sgn * kv
            theta = math.atan(kh / (1 + kvs))
            try:
                Kae = k_mononobe_okabe(phi_d, beta, delta, theta)
            except ValueError as exc:
                raise InputError("β > φ'd − θ: Mononobe-Okabe has no solution — reduce the "
                                 "backfill slope", "beta") from exc
            E_tot = 0.5 * g.gb * (1 + kvs) * Kae * g.hv**2
            dE = max(E_tot - 0.5 * g.gb * Ka * g.hv**2, 0.0)
            cd, sd = math.cos(delta), math.sin(delta)
            comps: list[Comp] = []
            for w in weights:
                if w.role == "weight" and w.kind == "G":
                    comps.append(Comp(w.name, V=w.V * (1 + kvs), xV=w.xV, kind="A"))
                    if w.inertia:
                        comps.append(Comp(calc.tr("Inertia — {name}", name=w.name),
                                          H=kh * w.V, zH=w.zH, kind="A", role="inertia"))
                elif w.role == "weight" and w.kind == "Q":
                    comps.append(Comp(w.name + " (ψ2)", V=inp["psi2"] * w.V, xV=w.xV,
                                      kind="A"))
                elif w.role == "uplift":
                    comps.append(Comp(w.name, V=w.V, xV=w.xV, kind="A", role="uplift"))
            Ph, zP = g.earth_force(Ka * cd)
            comps.append(Comp(calc.tr("Static earth pressure"), H=Ph, zH=zP,
                              V=Ph * math.tan(delta), xV=g.B, kind="A", role="thrust"))
            comps.append(Comp(calc.tr("Dynamic earth increment ΔE"), H=dE * cd, zH=g.hv / 2,
                              V=dE * sd, xV=g.B, kind="A", role="thrust"))
            if inp["q"] > 0 and inp["psi2"] > 0:
                Eq = Kae * (1 + kvs) * inp["psi2"] * inp["q"] * g.hv
                comps.append(Comp(calc.tr("Surcharge ψ2q (seismic)"), H=Eq * cd, zH=g.hv / 2,
                                  V=Eq * sd, xV=g.B, kind="A", role="thrust"))
            if g.hw > 0:
                comps.append(Comp(calc.tr("Water pressure"), H=GAMMA_W * g.hw**2 / 2,
                                  zH=g.hw / 3, kind="A", role="water"))
            t = factored(comps, 1, 1, 1)
            if result is None or t.H / max(t.V, 1e-9) > result["t"].H / max(result["t"].V,
                                                                         1e-9):
                result = {"label": label, "kvs": kvs, "theta": theta, "Kae": Kae,
                          "E": E_tot, "dE": dE, "comps": comps, "t": t, "kh": kh, "Ka": Ka,
                          "phi_d": phi_d}
        calc.text("Both directions of the vertical seismic action were analysed; the "
                  "governing case is **{label}**.", label=calc.tr(result["label"]))
        calc.formula("θ", "atan(k_h / (1 ± k_v))", math.degrees(result["theta"]), "°",
                     ref="Eq. E.6", dp=2)
        calc.formula("K", "Mononobe-Okabe, β ≤ φ'_d − θ", result["Kae"], "",
                     "Seismic active earth pressure coefficient", ref="EN 1998-5 Eq. E.2",
                     dp=4)
        calc.formula("E_d", "½ γ (1 ± k_v) K h_v²", result["E"], "kN/m",
                     "Total design earth thrust (static + dynamic)", ref="Eq. E.1")
        calc.formula("ΔE_d", "E_d − ½ γ K_a h_v²", result["dE"], "kN/m",
                     "Dynamic increment, applied at mid-height of the virtual back",
                     ref="E.9(3)")
        cls._stability(calc, g, inp, calc.tr("Seismic"), result["comps"], 1, 1, 1, gphi, 1.25,
                       1.0, 1.0, gov)
        t = result["t"]
        calc.check("Seismic overturning: M_dst ≤ M_stb", t.M_dst, t.M_stb, "kNm/m",
                   "EN 1998-5 7.3.1", hint=HINT_OVT)
        return result

    # -------------------------------------------------------- 3D / drawing
    @staticmethod
    def _pressure_profiles(g: WallGeometry, inp: dict, seis) -> list[dict]:
        beta = math.radians(inp["beta"])
        Ka = ka_coulomb(math.radians(inp["phi_b"]), beta, beta) * math.cos(beta)
        zs = np.linspace(0, g.hv, 41)
        out = [{"name": "Active earth pressure (char.)", "key": "earth",
                "points": [[from_base(z, "m"), from_base(Ka * g.sigma_v(z), "kN/m²")]
                           for z in zs]}]
        if inp["q"] > 0:
            p = from_base(Ka * inp["q"], "kN/m²")
            out.append({"name": "Surcharge pressure (char.)", "key": "surcharge",
                        "points": [[0, p], [from_base(g.hv, "m"), p]]})
        if g.hw > 0:
            out.append({"name": "Water pressure", "key": "water",
                        "points": [[from_base(z, "m"),
                                    from_base(GAMMA_W * max(g.hw - z, 0), "kN/m²")]
                                   for z in zs]})
        if seis:
            p = from_base(seis["dE"] * math.cos(beta) / g.hv, "kN/m²")
            out.append({"name": "Seismic increment ΔE (uniform equiv.)", "key": "seismic",
                        "points": [[0, p], [from_base(g.hv, "m"), p]]})
        return out

    @staticmethod
    def _outline(g: WallGeometry) -> dict:
        m = lambda P: [(from_base(x, "m"), from_base(z, "m")) for x, z in P]  # noqa: E731
        far = g.far
        back = [(g.xbb, g.tb), (g.B, g.tb), (g.B, 0), (far, 0), (far, g.zs(far)),
                (g.x0, g.top)]
        front = None
        if g.df > 0:
            front = [(-1500, 0), (0, 0), (0, g.tb), (g.x_front, g.tb),
                     (g.x_front, g.tb + g.df), (-1500, g.tb + g.df)]
        return {"concrete": [m(p) for _, p in g.concrete], "back": m(back),
                "front": m(front) if front else None, "B": from_base(g.B, "m"),
                "hv": from_base(g.hv, "m"), "hw": from_base(g.hw, "m"),
                "tb": from_base(g.tb, "m"), "xbb": from_base(g.xbb, "m"),
                "far": from_base(far, "m"), "top": from_base(g.top, "m"),
                "x_front": from_base(g.x_front, "m")}

    @classmethod
    def _scene(cls, calc, g: WallGeometry, inp, weights, pressures, gov) -> dict:
        o = cls._outline(g)
        L = from_base(g.L, "m")
        B, hv, hw, tb, far = o["B"], o["hv"], o["hw"], o["tb"], o["far"]
        sc = Scene3D("retaining_wall", calc.tr)
        sc.layer("concrete", "Wall", toggle=False)
        sc.layer("soil", "Soil")
        sc.layer("water", "Groundwater")
        for p in pressures:
            sc.layer(p["key"], p["name"])
        sc.layer("bearing", "Base pressure")
        sc.layer("forces", "Resultant forces")
        sc.layer("dims", "Dimensions")
        for poly in o["concrete"]:
            sc.prism("concrete", poly, L, PALETTE["concrete"])
        sc.prism("soil", o["back"], L, PALETTE["soil"], opacity=0.28)
        if o["front"]:
            sc.prism("soil", o["front"], L, PALETTE["soil2"], opacity=0.35)
        sc.box("soil", ((far - 1.5) / 2, -0.004, 0), (far + 3, 0.004, L + 3), "#cfc6b5",
               opacity=0.45, edges=False)
        if hw > 0:
            sc.prism("water", [(o["xbb"], min(tb, hw)), (far, min(tb, hw)), (far, hw),
                               (o["xbb"], hw)], L * 0.999, PALETTE["water"], opacity=0.22)
            sc.label("water", calc.tr("GWL +{h:.2f} m", h=hw), (far, hw, L / 2), "water")

        # cumulative pressure prisms on the virtual back
        zg = np.linspace(0, hv, 41)
        interp = lambda pts, z: float(np.interp(z, [a for a, _ in pts], [b for _, b in pts]))  # noqa
        tot = np.zeros_like(zg)
        pmax = max(sum(interp(p["points"], z) for p in pressures) for z in zg) or 1.0
        s = max(1.2, 0.45 * hv) / pmax
        for p in pressures:
            key, col = p["key"], PALETTE.get(p["key"], "#777")
            inner = [(B + t * s, z) for t, z in zip(tot, zg)]
            tot = tot + np.array([interp(p["points"], z) for z in zg])
            outer = [(B + t * s, z) for t, z in zip(tot, zg)]
            poly = inner + outer[::-1]
            for zpos in (-L / 2, 0.0, L / 2):
                sc.prism(key, poly, 0.04, col, opacity=0.55, z=zpos)
            sc.prism(key, poly, L, col, opacity=0.12, edges=False)
            for j in range(5):
                zz = -L / 2 + L * (j + 0.5) / 5
                for i in range(7):
                    z = hv * (i + 0.5) / 7
                    xin = float(np.interp(z, zg, [a for a, _ in inner]))
                    pl = interp(p["points"], z) * s
                    if pl > 0.03:
                        sc.arrow(key, (xin + pl, z, zz), (-1, 0, 0), pl, col, 0.12)
            zm, pm = max(p["points"], key=lambda a: a[1])
            sc.label(key, f"{pm:.1f} kN/m²",
                     (B + float(np.interp(zm, zg, tot)) * s + 0.1, zm, L / 2), key)
            sc.legend_item(col, f"{calc.tr(p['name'])}: {pm:.1f} kN/m²")

        if gov.get("bearing"):
            qb = [(from_base(x, "m"), from_base(q, "kN/m²")) for x, q in gov["bearing"]]
            qmax = max(q for _, q in qb) or 1.0
            sb = max(0.8, 0.25 * hv) / qmax
            col = PALETTE["bearing"]
            sc.prism("bearing", [(0, 0)] + [(x, -q * sb) for x, q in qb] + [(B, 0)],
                     L * 0.98, col, opacity=0.3)
            for j in range(5):
                zz = -L / 2 + L * (j + 0.5) / 5
                for i in range(9):
                    x = B * i / 8
                    q = float(np.interp(x, [a for a, _ in qb], [b for _, b in qb])) * sb
                    if q > 0.03:
                        sc.arrow("bearing", (x, -q, zz), (0, 1, 0), q, col, 0.1)
            sc.label("bearing", calc.tr("q,max = {q:.0f} kN/m² · {name}", q=qmax,
                                        name=gov["name"]),
                     (0.1, -qmax * sb - 0.2, L / 2), "bearing")
            sc.legend_item(col, calc.tr("Base pressure ({name}): {q:.1f} kN/m²",
                                        name=gov["name"], q=qmax))
            rx = from_base(gov["x_R"], "m")
            sc.arrow("forces", (rx, -0.9, 0), (0, 1, 0), 0.88, PALETTE["result"], 0.22)
            sc.label("forces", calc.tr("Resultant e = {e:.3f} m, B' = {b:.2f} m",
                                       e=from_base(gov["e"], "m"),
                                       b=from_base(gov["B_eff"], "m")),
                     (rx, -1.05, 0), "result")

        chars, _ = cls._thrust(calc, g, inp, 1.0, record=False)
        allf = weights + chars
        fmax = max([math.hypot(from_base(c.H, "kN/m"), from_base(c.V, "kN/m"))
                    for c in allf] + [1.0])
        fs = max(1.0, 0.35 * hv) / fmax
        for c in allf:
            H, V = from_base(c.H, "kN/m"), from_base(c.V, "kN/m")
            if c.role in ("thrust", "water") and abs(H) > 1e-6:
                ln = max(abs(H) * fs, 0.25)
                col = PALETTE["water"] if c.role == "water" else PALETTE["earth"]
                z = from_base(c.zH, "m")
                sc.arrow("forces", (B + ln + 0.05, z, 0), (-1, 0, 0), ln, col, 0.28)
                sc.label("forces", f"{c.name}: {H:.1f} kN/m @ {z:.2f} m",
                         (B + ln + 0.1, z + 0.15, 0), "force")
            elif c.role == "weight" and V > 0:
                ln = max(V * fs * 0.6, 0.25)
                x, z = from_base(c.xV, "m"), from_base(c.zH, "m") or tb
                sc.arrow("forces", (x, z + ln, -L / 4), (0, -1, 0), ln, "#444a55", 0.2)
                sc.label("forces", f"{c.name}: {V:.1f} kN/m", (x, z + ln + 0.12, -L / 4),
                         "weight")
        top = o["top"]
        sc.label("dims", f"H = {top:.2f} m", (o["x_front"] - 0.15, top / 2, L / 2), "dim")
        sc.label("dims", f"B = {B:.2f} m", (B / 2, 0.02, L / 2 + 0.3), "dim")
        sc.label("dims", f"β = {inp['beta']:.1f}°", (far - 0.5, hv + 0.2, 0), "dim")
        sc.label("dims", calc.tr("virtual back h = {h:.2f} m", h=hv), (B, hv + 0.25, -L / 2),
                 "dim")
        return sc.to_dict()
