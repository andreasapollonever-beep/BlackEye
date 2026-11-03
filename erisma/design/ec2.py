"""Shared EN 1992-1-1 design routines (N, mm)."""

from __future__ import annotations

import math

from ..core import Calculation

EPS_CU3 = 0.0035
ES = 200000.0
XI_LIM = 0.45  # x/d limit for ductility without redistribution, fck ≤ 50 (5.6.3)


def concrete_props(fck: float) -> dict[str, float]:
    return {"fctm": 0.30 * fck ** (2 / 3), "fcm": fck + 8,
            "Ecm": 22000 * ((fck + 8) / 10) ** 0.3}


def bar_area(dia: float) -> float:
    return math.pi * dia**2 / 4


def section_capacity(b: float, d: float, As: float, fcd: float, fyd: float,
                     d2: float = 0.0, As2: float = 0.0) -> tuple[float, float]:
    """Moment resistance of a doubly reinforced rectangle by strain compatibility.

    Rectangular stress block λ = 0.8, η = 1.0, ε_cu3 = 3.5‰, elastic-perfectly
    plastic steel.  Returns ``(M_Rd, x)``.
    """

    def stresses(x: float) -> tuple[float, float]:
        es = EPS_CU3 * (d - x) / x
        es2 = EPS_CU3 * (x - d2) / x
        return (max(min(ES * es, fyd), -fyd), max(min(ES * es2, fyd), -fyd))

    def resid(x: float) -> float:
        s1, s2 = stresses(x)
        return 0.8 * x * b * fcd + As2 * s2 - As * s1

    lo, hi = 1e-6 * d, 1.25 * d
    if resid(hi) < 0:  # grossly over-reinforced
        hi = 5 * d
    for _ in range(200):
        mid = 0.5 * (lo + hi)
        if resid(mid) > 0:
            hi = mid
        else:
            lo = mid
    x = 0.5 * (lo + hi)
    _, s2 = stresses(x)
    M = 0.8 * x * b * fcd * (d - 0.4 * x) + As2 * s2 * (d - d2)
    return M, x


def design_flexure(calc: Calculation, b: float, d: float, MEd: float, fck: float,
                   fcd: float, fyk: float, fyd: float, h: float, d2: float | None = None,
                   allow_compression: bool = True, per_metre: bool = False) -> dict[str, float]:
    """Write the flexural design of a rectangular section to ``calc``.

    Returns required areas ``As`` and ``As2`` (compression).  When
    ``per_metre`` is true areas are reported in mm²/m (``b`` must be 1000).
    """
    unit_a = "mm²/m" if per_metre else "mm²"
    area = (lambda a: a * 1e-3) if per_metre else (lambda a: a)
    mu = calc.formula("μ", "M_Ed / (b d² f_cd)", MEd / (b * d**2 * fcd), "", dp=4)
    mu_lim = 0.8 * XI_LIM * (1 - 0.4 * XI_LIM)
    calc.formula("μ_lim", "0.8ξ_lim(1 − 0.4ξ_lim), ξ_lim = 0.45", mu_lim, "",
                 "Limit for singly reinforced section (ductility, 5.6.3)", dp=4)
    fctm = 0.30 * fck ** (2 / 3)
    As_min = 0.0
    res = {"As2": 0.0, "mu": mu}
    if mu <= mu_lim:
        xi = calc.formula("ξ", "1.25(1 − √(1 − 2μ))", 1.25 * (1 - math.sqrt(1 - 2 * mu)), "",
                          "Neutral axis depth ratio x/d (λ = 0.8, η = 1.0)", ref="3.1.7",
                          dp=4)
        z = calc.formula("z", "d(1 − 0.4ξ) ≤ 0.95d", min(d * (1 - 0.4 * xi), 0.95 * d), "mm",
                         "Lever arm")
        As = MEd / (fyd * z)
        calc.formula("A_s,req", "M_Ed / (f_yd z)", area(As), unit_a,
                     "Required tension reinforcement")
        calc.text("μ ≤ μ_lim — no compression reinforcement required.")
        res["z"] = z
    elif not allow_compression or d2 is None:
        calc.warn("μ > μ_lim — the section is too small for a singly reinforced design; "
                  "increase the thickness.")
        calc.check("Singly reinforced: μ ≤ μ_lim", mu, mu_lim, "", "5.6.3",
                   hint="Increase the thickness of the member.")
        As = float("inf")
        res["z"] = 0.9 * d
    else:
        calc.text("μ > μ_lim — **compression reinforcement is required** "
                  "(neutral axis limited to x = 0.45d).")
        x_lim = calc.formula("x_lim", "ξ_lim d", XI_LIM * d, "mm")
        z_lim = calc.formula("z_lim", "d − 0.4x_lim", d - 0.4 * x_lim, "mm")
        M_lim = calc.formula("M_lim", "μ_lim b d² f_cd", mu_lim * b * d**2 * fcd, "kNm",
                             "Moment resisted by concrete alone")
        calc.input("d_2", d2, "mm", "Depth to compression reinforcement")
        eps2 = calc.formula("ε_s2", "ε_cu3 (x_lim − d_2) / x_lim",
                            EPS_CU3 * (x_lim - d2) / x_lim, "", "Strain in compression steel",
                            dp=5)
        sig2 = calc.formula("σ_s2", "min(E_s ε_s2, f_yd)", min(ES * eps2, fyd), "N/mm²",
                            ref="3.2.7")
        if sig2 <= 0:
            calc.warn("Compression bars lie below the neutral axis — not effective.")
            sig2 = 1e-9
        As2 = calc.formula("A_s2,req", "(M_Ed − M_lim) / (σ_s2 (d − d_2))",
                           (MEd - M_lim) / (sig2 * (d - d2)), "mm²",
                           "Required compression reinforcement")
        As = calc.formula("A_s,req", "M_lim / (f_yd z_lim) + A_s2,req σ_s2 / f_yd",
                          M_lim / (fyd * z_lim) + As2 * sig2 / fyd, "mm²",
                          "Required tension reinforcement")
        res.update({"As2": As2, "z": z_lim})
    As_min = calc.formula("A_s,min", "max(0.26 f_ctm/f_yk b d, 0.0013 b d)",
                          area(max(0.26 * fctm / fyk * b * d, 0.0013 * b * d)), unit_a,
                          ref="9.2.1.1(1)")
    As_max = calc.formula("A_s,max", "0.04 b h", area(0.04 * b * h), unit_a, ref="9.2.1.1(3)")
    res.update({"As": As, "As_min": As_min / (1e-3 if per_metre else 1),
                "As_max": As_max / (1e-3 if per_metre else 1)})
    return res


def shear_no_links(calc: Calculation, b: float, d: float, As: float, fck: float,
                   gamma_c: float, VEd: float, per_metre: bool = False) -> float:
    """V_Rd,c (Eq. 6.2) for members without shear reinforcement; records a check."""
    k = calc.formula("k", "1 + √(200/d) ≤ 2.0", min(1 + math.sqrt(200 / d), 2.0), "",
                     ref="6.2.2(1)", dp=3)
    rho = calc.formula("ρ_l", "A_s / (b d) ≤ 0.02", min(As / (b * d), 0.02), "",
                       ref="6.2.2(1)", dp=4)
    vmin = calc.formula("v_min", "0.035 k^1.5 f_ck^0.5", 0.035 * k**1.5 * math.sqrt(fck),
                        "N/mm²", ref="Eq. 6.3N", dp=3)
    u = "kN/m" if per_metre else "kN"
    scale = 1e-3 if per_metre else 1.0
    VRdc = calc.formula("V_Rd,c", "max(0.18/γ_c k(100ρ_l f_ck)^(1/3), v_min) b d",
                        max(0.18 / gamma_c * k * (100 * rho * fck) ** (1 / 3), vmin) * b * d
                        * scale, u, ref="Eq. 6.2")
    calc.check("Shear: V_Ed ≤ V_Rd,c", VEd * scale, VRdc, u, "6.2.2",
               hint="Increase the member thickness (or the tension reinforcement).")
    return VRdc / scale


def section_layers(b: float, h: float, nb: int, nh: int, dia: float, cover_to_bar: float):
    """Bar layers (area, depth from the compressed face) for bending across ``h``.

    ``nb`` bars along each face of width b (incl. corners), ``nh`` bars along each face of
    depth h (incl. corners); ``cover_to_bar`` = distance from the face to the bar centre.
    """
    a = bar_area(dia)
    d1 = cover_to_bar
    layers = [(nb * a, d1), (nb * a, h - d1)]
    mid = nh - 2
    for k in range(mid):
        y = d1 + (h - 2 * d1) * (k + 1) / (mid + 1)
        layers.append((2 * a, y))
    return layers


def moment_resistance(b: float, h: float, layers, fcd: float, fyd: float, NEd: float
                      ) -> tuple[float, float]:
    """M_Rd about the centroid for axial force NEd (compression +) — strain compatibility.

    Rectangular stress block (λ = 0.8, η = 1.0), ε_cu3 = 3.5 ‰, elastic–plastic steel.
    Returns ``(M_Rd, x)``; M_Rd = 0 when NEd exceeds the squash load.
    """
    As_tot = sum(a for a, _ in layers)
    N_max = b * h * fcd + As_tot * fyd
    N_min = -As_tot * fyd
    if NEd >= N_max or NEd <= N_min:
        return 0.0, float("nan")

    def forces(x):
        y = min(0.8 * x, h)
        Fc = y * b * fcd
        Fs, Ms = 0.0, 0.0
        for a, d in layers:
            eps = EPS_CU3 * (x - d) / x
            sig = max(min(ES * eps, fyd), -fyd)
            if d < y:  # bar inside the compressed block: deduct displaced concrete
                sig -= fcd if sig > 0 else 0.0
            Fs += a * sig
            Ms += a * sig * (h / 2 - d)
        return Fc + Fs, Fc * (h / 2 - y / 2) + Ms

    lo, hi = 1e-3 * h, 50 * h
    for _ in range(200):
        mid = 0.5 * (lo + hi)
        if forces(mid)[0] > NEd:
            hi = mid
        else:
            lo = mid
    x = 0.5 * (lo + hi)
    return forces(x)[1], x


def circular_moment_resistance(D: float, n: int, dia: float, cover_to_bar: float, fcd: float,
                               fyd: float, NEd: float) -> tuple[float, float]:
    """M_Rd of a circular section with ``n`` equally spaced bars for axial force NEd (comp. +).

    Same assumptions as :func:`moment_resistance`; the compressed circular segment of
    depth 0.8x is integrated in thin strips.  Returns ``(M_Rd, x)``.
    """
    R = D / 2
    rs = R - cover_to_bar
    a1 = math.pi * dia**2 / 4
    bars = [R - rs * math.cos(2 * math.pi * i / n) for i in range(n)]  # depth from top
    As = n * a1
    if NEd >= math.pi * R**2 * fcd + As * fyd or NEd <= -As * fyd:
        return 0.0, float("nan")
    ns = 120

    def forces(x):
        y = min(0.8 * x, D)
        Fc = Mc = 0.0
        for k in range(ns):
            d1, d2 = y * k / ns, y * (k + 1) / ns
            dm = 0.5 * (d1 + d2)
            w = 2 * math.sqrt(max(R**2 - (R - dm) ** 2, 0.0))
            f = w * (d2 - d1) * fcd
            Fc += f
            Mc += f * (R - dm)
        Fs = Ms = 0.0
        for d in bars:
            sig = max(min(ES * EPS_CU3 * (x - d) / x, fyd), -fyd)
            if d < y and sig > 0:
                sig -= fcd
            Fs += a1 * sig
            Ms += a1 * sig * (R - d)
        return Fc + Fs, Mc + Ms

    lo, hi = 1e-3 * D, 50 * D
    for _ in range(100):
        mid = 0.5 * (lo + hi)
        if forces(mid)[0] > NEd:
            hi = mid
        else:
            lo = mid
    x = 0.5 * (lo + hi)
    return forces(x)[1], x
