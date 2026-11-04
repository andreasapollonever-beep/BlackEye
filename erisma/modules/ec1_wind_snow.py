"""Site wind and snow loads — EN 1991-1-4 and EN 1991-1-3 (with National Annex data)."""

from __future__ import annotations

import math

from ..core import Calculation, DesignModule, Field, InputError, register
from ..design import sitezones
from ..design.annex import get_annex, ground_snow
from ..report.scene3d import PALETTE, Scene3D

TERRAIN = {"0": (0.003, 1.0), "I": (0.01, 1.0), "II": (0.05, 2.0), "III": (0.3, 5.0),
           "IV": (1.0, 10.0)}  # EN 1991-1-4 Table 4.1: z0, zmin [m]
CE = {"Windswept": 0.8, "Normal": 1.0, "Sheltered": 1.2}  # EN 1991-1-3 Table 5.1


def cpe_walls(h_d: float) -> tuple[float, float]:
    """EN 1991-1-4 Table 7.1, cpe,10 for zones D (windward) and E (leeward)."""
    pts = [(0.25, 0.7, -0.3), (1.0, 0.8, -0.5), (5.0, 0.8, -0.7)]
    if h_d <= 0.25:
        return pts[0][1], pts[0][2]
    if h_d >= 5:
        return pts[-1][1], pts[-1][2]
    for (x1, d1, e1), (x2, d2, e2) in zip(pts, pts[1:]):
        if h_d <= x2:
            t = (h_d - x1) / (x2 - x1)
            return d1 + t * (d2 - d1), e1 + t * (e2 - e1)
    return pts[-1][1], pts[-1][2]  # pragma: no cover


def site_qp(calc: Calculation, inp: dict, z_mm: float) -> float:
    """Peak velocity pressure q_p(z) [N/mm²] at height z (EN 1991-1-4 Section 4),
    v_b,0 from the National Annex map of the project site when available.

    Uses the inputs use_site, vb0, terrain and co; writes the steps to the report."""
    na = get_annex(calc.project.annex)
    p = calc.project
    site = None
    if inp["use_site"] and na.wind_map:
        try:
            site = (float(p.lat), float(p.lon))
        except (TypeError, ValueError):
            calc.note("No project site selected — manual v_b,0 is used (pick the site with "
                      "📍 Map in the project details).")
    calc.heading("Basic wind velocity")
    if site:
        w = sitezones.wind_at(na.code, *site)
        if w["special"]:
            raise InputError("The site lies in the Troodos summit area of the wind map, for "
                             "which the National Annex gives no value — a special study is "
                             "required.", "use_site")
        if not w["vb0"]:
            raise InputError("The project site is outside the wind map", "use_site")
        vb0 = calc.formula("v_b,0", "NA wind map at the site", w["vb0"], "",
                           "Fundamental basic wind velocity [m/s]",
                           ref="NA to CYS EN 1991-1-4, NA 2.4 Fig. 1", dp=1)
        if w["near_boundary"]:
            calc.note("The site is near an isotach — the higher value within 1 km is used.")
    else:
        vb0 = calc.input("v_b,0", inp["vb0"], "", "Fundamental basic wind velocity [m/s]",
                         dp=1)
    cdir = cseason = 1.0
    vb = calc.formula("v_b", "c_dir c_season v_b,0", cdir * cseason * vb0, "",
                      "Basic wind velocity [m/s] (c_dir = c_season = 1.0)", ref="Eq. 4.1",
                      dp=2)

    calc.heading("Mean wind and turbulence")
    z0, zmin = TERRAIN[inp["terrain"]]
    z = z_mm / 1000
    calc.label("Terrain category", inp["terrain"])
    calc.input("z_0", z0 * 1000, "m", "Roughness length", dp=3)
    kr = calc.formula("k_r", "0.19 (z_0 / 0.05)^0.07", 0.19 * (z0 / 0.05) ** 0.07, "",
                      ref="Eq. 4.5", dp=4)
    ze = max(z, zmin)
    cr = calc.formula("c_r(z)", "k_r ln(max(z, z_min) / z_0)", kr * math.log(ze / z0), "",
                      ref="Eq. 4.4", dp=4)
    co = inp["co"]
    vm = calc.formula("v_m(z)", "c_r c_o v_b", cr * co * vb, "", "Mean wind velocity [m/s]",
                      ref="Eq. 4.3", dp=2)
    Iv = calc.formula("I_v(z)", "k_I / (c_o ln(z / z_0)), k_I = 1.0",
                      1.0 / (co * math.log(ze / z0)), "", ref="Eq. 4.7", dp=4)
    rho = na.air_density
    qb = 0.5 * rho * vb**2 / 1000  # kN/m²
    qp = calc.formula("q_p(z)", "[1 + 7 I_v] ½ ρ v_m²", (1 + 7 * Iv) * 0.5 * rho * vm**2 / 1e6,
                      "kN/m²", calc.tr("Peak velocity pressure (ρ = {r:g} kg/m³)", r=rho), ref="Eq. 4.8",
                      dp=3)
    calc.formula("c_e(z)", "q_p / q_b", qp * 1e3 / qb, "", "Exposure factor", dp=3)
    return qp


@register
class WindSnowEC1(DesignModule):
    id = "ec1_wind_snow"
    title = "Wind and snow loads at the site"
    category = "Loads"
    standard = "EN 1991-1-4, EN 1991-1-3"
    uses_annex = True
    has_3d = True
    description = ("Peak velocity pressure q_p(z), wall pressures and roof snow load. With the "
                   "Cyprus National Annex v_b,0 and s_k are taken automatically from the project "
                   "site on the official maps.")

    fields = [
        Field("use_site", "Use the project site (maps of the National Annex)", kind="bool",
              default=True, group="Site",
              help="Pick the site in the project details (📍 Map). Otherwise give v_b,0 and s_k."),
        Field("vb0", "Fundamental basic wind velocity v_b,0", "", 24.0, min=10, max=60,
              group="Site", help="m/s — used when no site is selected or for EN values."),
        Field("A", "Site altitude above sea level", "", 100.0, min=0, max=3000, group="Site",
              help="m"),
        Field("sk_manual", "Ground snow load s_k (manual)", "kN/m²", 0.5, min=0, group="Site",
              help="Used only when the National Annex gives no snow map/formula."),
        Field("terrain", "Terrain category", kind="choice", choices=list(TERRAIN), default="III",
              group="Wind", help="0 sea, I lakes/flat, II open country, III suburbs/villages, "
                                 "IV cities (≥15 % covered by buildings > 15 m)."),
        Field("co", "Orography factor c_o", "", 1.0, min=1.0, max=2.0, group="Wind",
              help="1.0 unless the site is on a hill or cliff (Annex A.3)."),
        Field("z", "Reference height z (building height)", "m", 9.0, min=1, max=200,
              group="Wind"),
        Field("d", "Building depth in the wind direction d", "m", 12.0, min=1, group="Wind"),
        Field("roof", "Roof pitch α", "°", 0.0, min=0, max=80, group="Snow"),
        Field("Ce", "Exposure (snow)", kind="choice", choices=list(CE), default="Normal",
              group="Snow"),
    ]

    @classmethod
    def run(cls, calc: Calculation, inp: dict) -> None:
        na = get_annex(calc.project.annex)
        qp = site_qp(calc, inp, inp["z"])

        calc.heading("Pressures on vertical walls (rectangular building)")
        h_d = inp["z"] / inp["d"]
        cD, cE = cpe_walls(h_d)
        calc.formula("h/d", "z / d", h_d, "", dp=3)
        calc.formula("c_pe,10 (D)", "Table 7.1", cD, "", "Windward wall", ref="EN 1991-1-4 7.2.2",
                     dp=2)
        calc.formula("c_pe,10 (E)", "Table 7.1", cE, "", "Leeward wall", dp=2)
        wD = calc.formula("w_D", "q_p c_pe,D", qp * cD, "kN/m²", "Windward pressure", dp=3)
        wE = calc.formula("w_E", "q_p c_pe,E", qp * cE, "kN/m²", "Leeward suction", dp=3)
        f = 0.85 if h_d <= 1 else (1.0 if h_d >= 5 else 0.85 + 0.15 * (h_d - 1) / 4)
        calc.formula("w_net", "f (w_D − w_E)", f * (wD - wE), "kN/m²",
                     calc.tr("Net horizontal pressure, lack-of-correlation factor f = {f:.2f}",
                             f=f), ref="7.2.2(3)", dp=3)

        calc.heading("Snow load on the roof")
        A = inp["A"]
        calc.label("A", f"{A:g} m", "Site altitude")
        sk = ground_snow(na, A)
        if sk is None:
            sk = calc.input("s_k", inp["sk_manual"], "kN/m²", "Characteristic ground snow load",
                            dp=3)
        else:
            if na.snow_max_altitude and A > na.snow_max_altitude:
                raise InputError("Above {a:g} m a special snow study is required by the National "
                                 "Annex".format(a=na.snow_max_altitude), "A")
            sk = calc.formula("s_k", "0.289 [1 + (A/452)²]", sk * 1e-3, "kN/m²",
                              "Characteristic ground snow load (Annex C, Mediterranean, Z = 1)",
                              ref="NA to CYS EN 1991-1-3 NA 2.5", dp=3)
        a = inp["roof"]
        mu = 0.8 if a <= 30 else (0.8 * (60 - a) / 30 if a < 60 else 0.0)
        mu = calc.formula("μ_1", "Table 5.2 (α = {:g}°)".format(a), mu, "",
                          "Snow load shape coefficient", ref="EN 1991-1-3 5.3.2", dp=3)
        Ce = calc.formula("C_e", "Table 5.1", CE[inp["Ce"]], "", inp["Ce"], dp=2)
        calc.formula("s", "μ_1 C_e C_t s_k, C_t = 1.0", mu * Ce * 1.0 * sk, "kN/m²",
                     "Snow load on the roof", ref="Eq. 5.1", dp=3)
        hi = A > 1000
        calc.text("ψ factors for snow (EN 1990 Table A1.1): {p}", p="ψ0 = {:g}, ψ1 = {:g}, ψ2 = {:g}"
                  .format(*na.psi["snow_high" if hi else "snow_low"]))
        calc.model3d = cls._scene(calc, inp, qp, wD, wE, mu * Ce * sk)

    @staticmethod
    def _scene(calc, inp, qp, wD, wE, snow) -> dict:
        H, D = inp["z"] / 1000, inp["d"] / 1000
        W = D
        a = math.radians(inp["roof"])
        sc = Scene3D("wind_snow", calc.tr)
        for key, label in (("building", "Building"), ("wind", "Wind pressures"),
                           ("snow", "Snow on the roof")):
            sc.layer(key, label, toggle=key != "building")
        sc.box("building", (0, H / 2, 0), (D, H, W), "#c9ccd1", opacity=0.55)
        ridge = H + D / 2 * math.tan(a) if a > 0 else H
        if a > 0:
            sc.prism("building", [(-D / 2, H), (D / 2, H), (0, ridge)], W, "#9a5b45")
        wmax = max(abs(wD), abs(wE), 1e-9)
        for i in range(1, 4):
            for j in range(1, 4):
                y, z = H * i / 4, -W / 2 + W * j / 4
                ln = 0.6 + 1.4 * abs(wD) / wmax
                sc.arrow("wind", (-D / 2 - ln - 0.05, y, z), (1, 0, 0), ln, "#e03b3b", 0.25)
                ln2 = 0.6 + 1.4 * abs(wE) / wmax
                sc.arrow("wind", (D / 2 + 0.05, y, z), (1, 0, 0), ln2, "#2f8fd8", 0.25)
        sc.box("wind", (-D / 2 - 0.01, H / 2, 0), (0.02, H, W), "#e03b3b", opacity=0.35)
        sc.box("wind", (D / 2 + 0.01, H / 2, 0), (0.02, H, W), "#2f8fd8", opacity=0.35)
        sc.label("wind", calc.tr("Windward w_D = {w:.2f} kN/m²", w=wD * 1000),
                 (-D / 2 - 1.5, H + 0.6, W / 2), "force")
        sc.label("wind", calc.tr("Leeward w_E = {w:.2f} kN/m²", w=wE * 1000),
                 (D / 2 + 1.5, H + 0.6, W / 2), "force")
        sc.label("wind", calc.tr("q_p = {q:.2f} kN/m²", q=qp * 1000), (0, ridge + 1.6, 0),
                 "result")
        t = max(0.08, min(0.6, snow * 1000 / 2))
        if snow > 0:
            if a > 0:
                for sgn in (-1, 1):
                    sc.prism("snow", [(0, ridge + 0.02), (sgn * D / 2, H + 0.02),
                                      (sgn * D / 2, H + 0.02 + t), (0, ridge + 0.02 + t)], W,
                             "#f4f7fb", opacity=0.9)
            else:
                sc.box("snow", (0, H + t / 2, 0), (D, t, W), "#f4f7fb", opacity=0.9)
            sc.label("snow", calc.tr("s = {s:.2f} kN/m²", s=snow * 1000), (0, ridge + t + 0.6, 0),
                     "result")
        sc.arrow("wind", (-D / 2 - 4.5, H + 1.5, 0), (1, 0, 0), 2.0, PALETTE["load"], 0.4)
        sc.label("wind", calc.tr("Wind"), (-D / 2 - 4.5, H + 1.9, 0), "")
        return sc.to_dict()

