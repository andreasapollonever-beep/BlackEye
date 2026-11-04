"""Wind on poles, masts, chimneys, members and plane lattices — EN 1991-1-4 §5.3, §6, §7.6–7.13,
Annexes B, E, F.

F_w = c_s c_d · c_f · q_p(z_e) · A_ref (Eq. 5.3), with c_f = c_f,0 ψ_r ψ_λ, the structural factor by
the detailed procedure of 6.3.1 / Annex B (natural frequency and damping from Annex F) and the
critical velocity of vortex shedding of Annex E.1.  Values: :mod:`erisma.design.wind_members`.
"""

from __future__ import annotations

import math

from ..core import Calculation, DesignModule, Field, InputError, register
from ..design import wind_members as WM
from ..design.annex import get_annex
from ..report.scene3d import Scene3D
from .ec1_wind_snow import TERRAIN, site_qp

SECTIONS = ["Circular (pole, chimney, tube)", "Rectangular or square", "Sharp-edged (I, L, U, T, +)",
            "Regular polygon", "Plane lattice of angle members", "Stranded cable"]
ENDS = ["Free end (Table 7.16, positions 1–3)", "Both ends closed (Table 7.16, position 4)"]
PSI = ["ψ_λ = 1.0 (conservative)", "Given ψ_λ (Figure 7.36)"]
CSCD = ["Detailed procedure (6.3.1, Annex B)", "c_s c_d = 1 (only where 6.2(1) allows)",
        "Given value"]
N1 = ["Uniform cantilever (EI, m)", "Chimney (Eq. F.3)", "Given n1"]
EPS = {"Steel chimney (ε1 = 1000)": 1000.0, "Concrete or masonry chimney (ε1 = 700)": 700.0}


@register
class WindMembersEC1(DesignModule):
    id = "ec1_wind_members"
    title = "Wind on poles, chimneys, members and lattices"
    category = "Loads"
    standard = "EN 1991-1-4 §6, §7.6–7.13, Annexes B, E, F"
    uses_annex = True
    has_3d = True
    description = ("Force coefficient c_f of circular, rectangular, sharp-edged and polygonal "
                   "sections, plane lattices and cables, end-effect factor, the structural factor "
                   "c_s c_d (Annex B, frequency and damping from Annex F), the wind force, base "
                   "moment and the vortex-shedding check.")

    fields = [
        Field("use_site", "Use the project site (maps of the National Annex)", kind="bool",
              default=True, group="Site",
              help="Pick the site in the project details (📍 Map). Otherwise give v_b,0."),
        Field("vb0", "Fundamental basic wind velocity v_b,0", "", 24.0, min=10, max=60,
              group="Site", help="m/s — used when no site is selected or for EN values."),
        Field("terrain", "Terrain category", kind="choice", choices=list(TERRAIN), default="III",
              group="Site", help="0 sea, I lakes/flat, II open country, III suburbs/villages, "
                                 "IV cities (≥15 % covered by buildings > 15 m)."),
        Field("co", "Orography factor c_o", "", 1.0, min=1.0, max=2.0, group="Site"),
        Field("section", "Cross-section", kind="choice", choices=SECTIONS, default=SECTIONS[0],
              group="Element"),
        Field("h", "Height / length of the element ℓ", "m", 12.0, min=0.5, max=200,
              group="Element", help="Cantilever from its base (pole, mast, chimney)."),
        Field("zb", "Height of the base above ground", "m", 0.0, min=0, max=200,
              group="Element", help="0 on the ground; e.g. the roof height for a mast on a roof. "
                                    "z_e = base + ℓ (7.9.2(5))."),
        Field("b", "Width or diameter b (across the wind)", "m", 0.30, min=0.005, max=30,
              group="Element", help="Lattice: width of the face; cable: diameter."),
        Field("d", "Depth d (along the wind)", "m", 0.30, min=0.005, max=50, group="Element",
              show_if="section=Rectangular or square"),
        Field("r", "Corner radius r", "m", 0.0, min=0, group="Element",
              show_if="section=Rectangular or square",
              help="ψ_r of Figure 7.24 applies to square sections (d = b)."),
        Field("surface", "Surface (equivalent roughness, Table 7.13)", kind="choice",
              choices=list(WM.ROUGHNESS), default="Galvanised steel", group="Element",
              show_if="section=Circular (pole, chimney, tube)"),
        Field("sides", "Polygon (number of sides, surface)", kind="choice", choices=WM.POLYGONS,
              default="8 (smooth, r/b < 0.075)", group="Element",
              show_if="section=Regular polygon"),
        Field("phi", "Solidity ratio φ of the lattice", "", 0.3, min=0.01, max=1.0,
              group="Element", show_if="section=Plane lattice of angle members",
              help="Projected area of members and gussets / area of the face (Eq. 7.26)."),
        Field("ends", "Position (end effects)", kind="choice", choices=ENDS, default=ENDS[0],
              group="End effect"),
        Field("psi_mode", "End-effect factor ψ_λ", kind="choice", choices=PSI, default=PSI[0],
              group="End effect", help="Figure 7.36 gives indicative values only."),
        Field("psi_l", "ψ_λ from Figure 7.36", "", 1.0, min=0.5, max=1.0, group="End effect",
              show_if="psi_mode=Given ψ_λ (Figure 7.36)"),
        Field("cscd_mode", "Structural factor c_s c_d", kind="choice", choices=CSCD,
              default=CSCD[0], group="Dynamics"),
        Field("cscd_user", "c_s c_d (given)", "", 1.0, min=0.5, max=2.0, group="Dynamics",
              show_if="cscd_mode=Given value"),
        Field("n1_mode", "Natural frequency n1", kind="choice", choices=N1, default=N1[0],
              group="Dynamics"),
        Field("EI", "Bending stiffness EI", "", 12600.0, min=1, group="Dynamics",
              show_if="n1_mode=Uniform cantilever (EI, m)",
              help="kNm² — e.g. steel tube Ø300×6: I = π/64 (0.300⁴ − 0.288⁴) = 6.0·10⁻⁵ m⁴, "
                   "EI = 210 GPa × 6.0·10⁻⁵ m⁴ = 12 600 kNm²."),
        Field("m", "Mass per unit length m", "", 45.0, min=0.1, group="Dynamics",
              help="kg/m — also the equivalent mass m_e (upper third, F.4(2)); Ø300×6 steel tube: "
                   "7850 · π · 0.294 · 0.006 = 43.5 kg/m."),
        Field("n1", "Natural frequency n1 (given)", "", 1.5, min=0.01, max=50, group="Dynamics",
              show_if="n1_mode=Given n1", help="Hz"),
        Field("eps", "Chimney material", kind="choice", choices=list(EPS),
              default=list(EPS)[0], group="Dynamics", show_if="n1_mode=Chimney (Eq. F.3)"),
        Field("h2", "Height of the tapered lower part h2", "m", 0.0, min=0, group="Dynamics",
              show_if="n1_mode=Chimney (Eq. F.3)", help="Figure F.1; h_eff = h1 + h2/3."),
        Field("ws_wt", "W_s / W_t (stiffening weight / total weight)", "", 1.0, min=0.05,
              max=1.0, group="Dynamics", show_if="n1_mode=Chimney (Eq. F.3)"),
        Field("damping", "Structural damping (Table F.2)", kind="choice",
              choices=list(WM.DAMPING),
              default="Unlined welded steel stack without external insulation", group="Dynamics"),
        Field("St", "Strouhal number St (non-circular sections)", "", 0.12, min=0.05, max=0.3,
              group="Dynamics", help="Table E.1 / Figure E.1; circular sections use 0.18."),
    ]

    @classmethod
    def run(cls, calc: Calculation, inp: dict) -> None:
        na = get_annex(calc.project.annex)
        calc.note("Coefficients: {s}, recommended values; a National Annex may give other "
                  "values.", s=calc.tr(WM.SOURCE))
        l, zb, b = inp["h"] / 1000, inp["zb"] / 1000, inp["b"] / 1000
        sec = inp["section"]
        ze = zb + l
        qp = site_qp(calc, inp, ze * 1000)
        vb = calc.values["v_b"]
        rho = na.air_density
        z0, zmin = TERRAIN[inp["terrain"]]
        co = inp["co"]
        kr = 0.19 * (z0 / 0.05) ** 0.07

        def vm_at(z):
            return kr * math.log(max(z, zmin) / z0) * co * vb

        def iv_at(z):
            return 1.0 / (co * math.log(max(z, zmin) / z0))

        calc.heading("Element and Reynolds number")
        calc.label("Cross-section", sec)
        calc.input("ℓ", inp["h"], "m", "Length of the element")
        calc.input("b", inp["b"], "m", "Width / diameter")
        calc.formula("z_e", "base + ℓ", ze * 1000, "m", "Reference height (top of the element)",
                     ref="7.6–7.9", dp=2)
        v = calc.formula("v(z_e)", "√(2 q_p / ρ)", math.sqrt(2 * qp * 1e6 / rho), "",
                         "Peak wind velocity [m/s]", ref="Figure 7.28 NOTE 2", dp=2)
        Re = calc.formula("Re", "b · v / ν, ν = 15·10⁻⁶ m²/s", b * v / WM.NU_AIR, "",
                          "Reynolds number", ref="Eq. 7.15", dp=0)

        # ---------------------------------------------------------- force coefficient
        calc.heading("Force coefficient")
        circular = sec in (SECTIONS[0], SECTIONS[5])
        psir = 1.0
        Aref = l * b
        if sec == SECTIONS[0]:
            k = WM.ROUGHNESS[inp["surface"]] / 1000
            calc.text("Surface: {s}, equivalent roughness k = {k:g} mm (Table 7.13).",
                      s=calc.tr(inp["surface"]), k=k * 1000)
            kb = calc.formula("k/b", "k / b", k / b, "", "Relative roughness", dp=6)
            cf0 = calc.formula("c_f,0", "max(min(1.2; 0.11/(Re/10⁶)^1.4); "
                               "1.2 + 0.18 log(10 k/b)/(1 + 0.4 log(Re/10⁶)); 0.4)",
                               WM.cf0_circular(Re, kb), "", "Circular cylinder without free-end "
                               "flow", ref="Figure 7.28", dp=3)
        elif sec == SECTIONS[1]:
            d = inp["d"] / 1000
            cf0 = calc.formula("c_f,0", f"Figure 7.23, d/b = {d / b:.3f}", WM.cf0_rectangular(d / b),
                               "", "Rectangular section, sharp corners", ref="Figure 7.23",
                               dp=3)
            if inp["r"] > 0:
                if abs(d / b - 1) < 1e-6:
                    psir = calc.formula("ψ_r", f"Figure 7.24, r/b = {inp['r'] / inp['b']:.3f}",
                                        WM.psi_r(inp["r"] / inp["b"]), "",
                                        "Reduction for rounded corners", ref="Figure 7.24", dp=3)
                else:
                    calc.note("ψ_r of Figure 7.24 is given for square sections only; ψ_r = 1.0 "
                              "is used.")
            if d / b < 0.2:
                calc.warn("Plate-like section (d/b < 0.2): lift forces may increase c_f by up to "
                          "25 % at certain wind angles (7.6(3)).")
        elif sec == SECTIONS[2]:
            cf0 = calc.formula("c_f,0", "7.7(1) NOTE 1", WM.CF0_SHARP_EDGED, "",
                               "Sharp-edged section (recommended)", ref="7.7", dp=2)
        elif sec == SECTIONS[3]:
            val, case = WM.cf0_polygon(inp["sides"], Re)
            if math.isnan(val):
                calc.text("Table 7.11: {c} — treated as a circular cylinder (7.9).",
                          c=calc.tr("Re < 2·10⁵" if case == "circular" else "Re ≥ 1.2·10⁶"))
                cf0 = calc.formula("c_f,0", "Figure 7.28 (k/b = 2·10⁻⁴/b)",
                                   WM.cf0_circular(Re, 0.2e-3 / b), "", "As a circular cylinder",
                                   ref="7.9.2", dp=3)
            else:
                cf0 = calc.formula("c_f,0", f"Table 7.11, {inp['sides']} sides, {case}", val, "",
                                   "Regular polygon", ref="Table 7.11", dp=3)
        elif sec == SECTIONS[4]:
            phi = inp["phi"]
            cf0 = calc.formula("c_f,0", f"Figure 7.33, φ = {phi:g}", WM.cf0_lattice_angles(phi),
                               "", "Plane lattice of angle members", ref="Figure 7.33", dp=3)
            Aref = phi * l * b
        else:
            cf0 = calc.formula("c_f,0", "7.9.2(3)", WM.CF0_CABLE, "", "Stranded cable",
                               ref="7.9.2(3)", dp=2)
        lam = calc.formula("λ", "Table 7.16", WM.slenderness(l, b, circular,
                                                             inp["ends"] == ENDS[1]), "",
                           "Effective slenderness", ref="Table 7.16", dp=1)
        if inp["psi_mode"] == PSI[1]:
            psil = calc.input("ψ_λ", inp["psi_l"], "", "End-effect factor (Figure 7.36, given)",
                              dp=3)
            calc.note("Figure 7.36 gives indicative values of ψ_λ for λ = {l:.1f}; the value is the "
                      "user's reading.", l=lam)
        else:
            psil = calc.input("ψ_λ", 1.0, "", "End-effect factor (no reduction, conservative)",
                              dp=2)
        cf = calc.formula("c_f", "c_f,0 · ψ_r · ψ_λ", cf0 * psir * psil, "", "Force coefficient",
                          ref="Eq. 7.9 / 7.11 / 7.13 / 7.19 / 7.25", dp=3)
        calc.formula("A_ref", "φ · ℓ · b" if sec == SECTIONS[4] else "ℓ · b", Aref * 1e6, "m²",
                     "Reference area", ref="Eq. 7.10 / 7.27", dp=3)

        # ------------------------------------------------------------- dynamics
        calc.heading("Natural frequency and damping")
        m = inp["m"]
        n1 = None
        if inp["n1_mode"] == N1[0]:
            EI = inp["EI"] * 1e3  # kNm² → Nm²
            n1 = calc.formula("n_1", "1.875²/(2π) · √(EI/(m ℓ⁴))",
                              WM.n1_uniform_cantilever(EI, m, l), "",
                              "Fundamental frequency [Hz], uniform cantilever (beam theory)",
                              dp=3)
        elif inp["n1_mode"] == N1[1]:
            eps1 = EPS[inp["eps"]]
            h2 = inp["h2"] / 1000
            if h2 > l:
                raise InputError("h2 cannot exceed the height of the chimney", "h2")
            n1 = calc.formula("n_1", f"ε1 b / h_eff² · √(W_s/W_t), ε1 = {eps1:g}, h_eff = "
                              f"{l - h2:.2f} + {h2:.2f}/3", WM.n1_chimney(eps1, b, l - h2, h2,
                                                                         inp["ws_wt"]), "",
                              "Fundamental frequency [Hz]", ref="Eq. F.3, F.4", dp=3)
        else:
            n1 = calc.input("n_1", inp["n1"], "", "Fundamental frequency [Hz] (given)", dp=3)
        zs = max(0.6 * ze, zmin)
        calc.formula("z_s", "0.6 · h ≥ z_min", zs * 1000, "m", "Reference height for c_s c_d",
                     ref="Figure 6.1 a)", dp=2)
        vms = calc.formula("v_m(z_s)", "c_r(z_s) c_o v_b", vm_at(zs), "", "Mean velocity [m/s]",
                           ref="Eq. 4.3", dp=2)
        ivs = calc.formula("I_v(z_s)", "1 / (c_o ln(z_s/z_0))", iv_at(zs), "",
                           "Turbulence intensity", ref="Eq. 4.7", dp=4)
        ds = calc.formula("δ_s", "Table F.2", WM.DAMPING[inp["damping"]], "",
                          calc.tr("Structural damping — {t}", t=calc.tr(inp["damping"])),
                          ref="Table F.2", dp=3)
        da = calc.formula("δ_a", "c_f ρ b v_m(z_s) / (2 n_1 m_e)",
                          WM.aero_damping(cf, rho, b if sec != SECTIONS[4] else inp["phi"] * b,
                                          vms, n1, m), "", "Aerodynamic damping",
                          ref="Eq. F.18", dp=4)
        delta = calc.formula("δ", "δ_s + δ_a", ds + da, "", "Logarithmic decrement",
                             ref="Eq. F.15", dp=4)

        calc.heading("Structural factor c_s c_d")
        mode = inp["cscd_mode"]
        if mode == CSCD[0]:
            sf = WM.structural_factor(l, b, zs, z0, zmin, vms, ivs, n1, delta)
            calc.formula("L(z_s)", "300 (z_s/200)^α, α = 0.67 + 0.05 ln z_0", sf["L"] * 1000, "m",
                         "Turbulent length scale", ref="Eq. B.1", dp=1)
            calc.formula("B²", "1 / (1 + 0.9 ((b + h)/L)^0.63)", sf["B2"], "",
                         "Background factor", ref="Eq. B.3", dp=4)
            calc.formula("f_L", "n_1 L / v_m", sf["fL"], "", "Non-dimensional frequency",
                         ref="B.1(2)", dp=4)
            calc.formula("S_L", "6.8 f_L / (1 + 10.2 f_L)^(5/3)", sf["SL"], "",
                         "Power spectral density", ref="Eq. B.2", dp=4)
            calc.formula("R_h", f"Eq. B.7, η_h = {sf['eta_h']:.3f}", sf["Rh"], "", ref="Eq. B.7",
                         dp=4)
            calc.formula("R_b", f"Eq. B.8, η_b = {sf['eta_b']:.3f}", sf["Rb"], "", ref="Eq. B.8",
                         dp=4)
            calc.formula("R²", "π²/(2δ) · S_L · R_h · R_b", sf["R2"], "",
                         "Resonance response factor", ref="Eq. B.6", dp=4)
            calc.formula("ν", "n_1 √(R²/(B² + R²)) ≥ 0.08", sf["nu"], "",
                         "Up-crossing frequency [Hz]", ref="Eq. B.5", dp=4)
            calc.formula("k_p", "√(2 ln νT) + 0.6/√(2 ln νT) ≥ 3, T = 600 s", sf["kp"], "",
                         "Peak factor", ref="Eq. B.4", dp=3)
            cscd = calc.formula("c_s c_d", "(1 + 2 k_p I_v √(B² + R²)) / (1 + 7 I_v)",
                                sf["cscd"], "", "Structural factor", ref="Eq. 6.1", dp=3)
            calc.text("c_s = {cs:.3f} (Eq. 6.2), c_d = {cd:.3f} (Eq. 6.3).", cs=sf["cs"],
                      cd=sf["cd"])
            calc.note("Valid for vertical structures of Figure 6.1 a) whose along-wind response is "
                      "governed by the fundamental mode with a mode shape of constant sign "
                      "(6.3.1(2)P).")
        elif mode == CSCD[1]:
            cscd = calc.input("c_s c_d", 1.0, "", "Structural factor", dp=2)
            calc.note("c_s c_d = 1 is allowed only in the cases of 6.2(1) a)–d) (e.g. chimneys of "
                      "circular section with h < 60 m and h < 6.5 b); for other structures use the "
                      "detailed procedure (6.2(1) f)).")
            if sec == SECTIONS[0] and not (ze < 60 and ze < 6.5 * b):
                calc.warn("This chimney/pole does not meet 6.2(1) d) (h < 60 m and h < 6.5 b): "
                          "c_s c_d = 1 is not justified.")
        else:
            cscd = calc.input("c_s c_d", inp["cscd_user"], "", "Structural factor (given)", dp=3)

        # ---------------------------------------------------------------- force
        calc.heading("Wind force")
        Fw = calc.formula("F_w", "c_s c_d · c_f · q_p(z_e) · A_ref", cscd * cf * qp * Aref * 1e6,
                          "kN", "Wind force on the element", ref="Eq. 5.3", dp=2)
        calc.formula("w", "F_w / ℓ", Fw / l / 1000, "kN/m", "Equivalent uniform line load",
                     dp=3)
        calc.formula("M_base", "F_w · ℓ / 2", Fw * l * 1000 / 2, "kNm",
                     "Bending moment at the base (uniform q_p(z_e) over ℓ, conservative)", dp=2)
        if sec == SECTIONS[4]:
            calc.text("Lattice: A_ref = φ ℓ b is the projected area of the members and gussets "
                      "(Eq. 7.27); force per face of a plane lattice.")

        # --------------------------------------------------------------- vortex
        calc.heading("Vortex shedding (Annex E)")
        St = WM.ST_CIRCULAR if circular else inp["St"]
        calc.formula("St", "Table E.1" if circular else "given", St, "", "Strouhal number",
                     ref="Table E.1", dp=3)
        vcrit = calc.formula("v_crit", "b · n_1 / St", b * n1 / St, "",
                             "Critical wind velocity [m/s]", ref="Eq. E.2", dp=2)
        vm_top = calc.formula("v_m(z_e)", "c_r(z_e) c_o v_b", vm_at(ze), "",
                              "Mean velocity at the top [m/s]", ref="Eq. 4.3", dp=2)
        if l / b <= 6:
            calc.text("ℓ/b = {r:.1f} ≤ 6: vortex shedding need not be investigated (E.1.2(1)).",
                      r=l / b)
        elif vcrit > 1.25 * vm_top:
            calc.text("v_crit = {vc:.2f} m/s > 1.25 v_m = {v:.2f} m/s: vortex shedding need not "
                      "be investigated (E.1.2(2), Eq. E.1).", vc=vcrit, v=1.25 * vm_top)
        else:
            calc.text("v_crit = {vc:.2f} m/s ≤ 1.25 v_m = {v:.2f} m/s: the effect of vortex "
                      "shedding is calculated (E.1.2(2)).", vc=vcrit, v=1.25 * vm_top)
            clat0 = None
            if circular and sec != SECTIONS[5]:
                Rec = calc.formula("Re(v_crit)", "b · v_crit / ν", b * vcrit / WM.NU_AIR, "",
                                   "Reynolds number at the critical velocity", ref="Eq. E.5",
                                   dp=0)
                clat0 = calc.formula("c_lat,0", "Figure E.2", WM.clat0_circular(Rec), "",
                                     "Basic lateral force coefficient", ref="Figure E.2", dp=3)
            elif sec == SECTIONS[1] and 0.5 <= inp["d"] / inp["b"] <= 10:
                clat0 = calc.formula("c_lat,0", "Table E.2", WM.CLAT0_RECTANGULAR, "",
                                     "Basic lateral force coefficient", ref="Table E.2", dp=2)
            if clat0 is None:
                calc.warn("Vortex-induced vibration must be checked by Annex E.1.5; the "
                          "amplitude for this cross-section is not calculated here.")
            else:
                Sc = calc.formula("Sc", "2 δ_s m_e / (ρ b²)", WM.scruton(ds, m, rho, b), "",
                                  "Scruton number", ref="Eq. E.4", dp=2)
                vx = WM.vortex_cantilever(b, l, St, Sc, clat0, vcrit,
                                          lambda s: vm_at(zb + s))
                calc.formula("L_j", f"Table E.4, L_j/b = {vx['Lj_b']:.2f}", vx["Lj"] * 1000, "m",
                             "Effective correlation length (iterated with y_F)",
                             ref="Table E.4", dp=2)
                calc.formula("c_lat", f"Table E.3, v_crit/v_m,Lj = {vx['ratio']:.3f}",
                             vx["clat"], "", "Lateral force coefficient", ref="Table E.3", dp=3)
                calc.formula("K_w", "3 (L_j/b)/λ [1 − (L_j/b)/λ + ⅓((L_j/b)/λ)²] ≤ 0.6",
                             vx["Kw"], "", "Effective correlation length factor (λ = ℓ/b)",
                             ref="Table E.5", dp=3)
                calc.text("Mode shape factor K = 0.13 (Table E.5, cantilever, ζ = 2).")
                y = calc.formula("y_F,max", "b · (1/St²) (1/Sc) K K_w c_lat", vx["y"] * 1000, "mm",
                                 "Maximum cross-wind amplitude at the top", ref="Eq. E.7", dp=1)
                calc.formula("y_F/b", "y_F,max / b", vx["y_b"], "", dp=3)
                w2 = (2 * math.pi * n1) ** 2
                calc.formula("M_vortex", "m (2π n_1)² y_F ℓ²/4", m * w2 * vx["y"] * l * l / 4 * 1000,
                             "kNm", "Cross-wind base moment from the inertia forces "
                                    "F_w(s) = m (2π n_1)² Φ(s) y_F, Φ = (s/ℓ)²",
                             ref="Eq. E.6", dp=2)
                calc.formula("V_vortex", "m (2π n_1)² y_F ℓ/3", m * w2 * vx["y"] * l / 3, "kN",
                             "Cross-wind base shear", ref="Eq. E.6", dp=2)
                v0 = 0.2 * vm_top
                N = calc.formula("N", "2 T n_1 ε0 (v_crit/v0)² exp(−(v_crit/v0)²), T = 50 years, "
                                      "ε0 = 0.3, v0 = 0.2 v_m",
                                 WM.load_cycles(n1, vcrit, v0), "", "Number of load cycles "
                                 "(fatigue)", ref="Eq. E.10", dp=0)
                if N < 1e4:
                    calc.text("N < 10⁴: the recommended minimum N = 10⁴ is used (E.1.5.2.6 "
                              "NOTE 1).")
                calc.note("Design the element for the cross-wind moment and check fatigue with N "
                          "cycles (EN 1993-1-9). Vortex shedding and along-wind gusts are not "
                          "combined at the same time.")
        calc.model3d = cls._scene(calc, sec, l, zb, b, inp, Fw)

    @staticmethod
    def _scene(calc, sec, l, zb, b, inp, Fw) -> dict:
        sc = Scene3D("wind_member", calc.tr)
        sc.layer("member", "Element")
        sc.layer("wind", "Wind")
        col = "#8a96a3"
        w = max(b, 0.05)
        if sec == SECTIONS[0] or sec == SECTIONS[5] or sec == SECTIONS[3]:
            n = 16
            verts, faces = [], []
            for i in range(n):
                a = 2 * math.pi * i / n
                for y in (zb, zb + l):
                    verts.append((w / 2 * math.cos(a), y, w / 2 * math.sin(a)))
            for i in range(n):
                j = (i + 1) % n
                faces += [(2 * i, 2 * j, 2 * j + 1), (2 * i, 2 * j + 1, 2 * i + 1)]
            sc.mesh("member", verts, faces, col)
        elif sec == SECTIONS[4]:
            sc.box("member", (0, zb + l / 2, 0), (w, l, w), col, opacity=0.25)
            for k in range(int(l / max(w, 0.5)) + 1):
                y = zb + min(k * max(w, 0.5), l)
                sc.line("member", [(-w / 2, y, 0), (w / 2, y, 0)], "#5a6b7d")
            sc.line("member", [(-w / 2, zb, 0), (-w / 2, zb + l, 0)], "#5a6b7d")
            sc.line("member", [(w / 2, zb, 0), (w / 2, zb + l, 0)], "#5a6b7d")
        else:
            d = inp["d"] / 1000 if sec == SECTIONS[1] else w
            sc.box("member", (0, zb + l / 2, 0), (w, l, d), col)
        if zb > 0:
            sc.box("member", (0, zb / 2, 0), (max(4 * w, 2.0), zb, max(4 * w, 2.0)), "#cfd5dc",
                   opacity=0.35)
        for k in range(5):
            y = zb + l * (k + 0.5) / 5
            sc.arrow("wind", (0, y, -max(1.5, 6 * w)), (0, 0, 1), max(1.0, 4 * w), "#2a6f97")
        sc.label("wind", f"F_w = {Fw / 1000:.2f} kN", (0, zb + l + 0.4, 0), "result")
        return sc.to_dict()
