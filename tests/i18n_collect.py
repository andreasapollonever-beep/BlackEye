"""Run every module in Greek over many scenarios and list untranslated strings."""

from erisma import i18n
from erisma.core import InputError, all_modules, get_module
from erisma.report import render_html

SCENARIOS = {
    "ec2_rc_beam": [{}, {"MEd": 380, "n_bars": 5, "dia": "25", "n_comp": 2, "dia_comp": "12"},
                    {"MEd": 900}, {"VEd": 600}],
    "ec3_steel_beam": [{}, {"L": 12, "Lcr": 0}, {"section": "IPE 600", "grade": "S235"},
                       {"Gk_pt": 50, "Qk_pt": 30}, {"section": "HEA 300", "L": 3, "qk": 200}],
    "beam_analysis": [{}],
    "building_frame": [{}, {"wind": True}, {"seismic": False}, {"design": False, "n_modes": 3},
                       {"walls": [], "pdelta": True, "capacity": True},
                       {"found_type": "Isolated pad footings", "walls": []},
                       {"found_type": "Foundation beams (Winkler)"},
                       {"loads": {"cases": [{"name": "S", "type": "S", "loads": [
                           {"kind": "area", "panels": "all", "storeys": "roof", "q": 0.8}]},
                           {"name": "Q2", "type": "Q", "category": "B", "loads": []}],
                           "combos": [{"name": "U", "factors": {"G": 1.0}}]}},
                       {"raft_t": 400, "raft_over": 0.0},
                       {"capacity": False, "layout": {"omit_columns": ["B2"], "openings": ["A1"],
                                                      "beam_sizes": {"A2-A3": [300, 600]}}},
                       {"walls": [{"at": "A1", "dir": "X", "L": 1.0, "t": 150}], "ag": 0.4},
                       {"col_b": 250, "col_h": 250, "beam_b": 200, "beam_h": 300, "ag": 0.36,
                        "storeys": [{"h": 3.0}] * 5, "x_spans": [{"L": 7.0}], "walls": [],
                        "y_spans": [{"L": 7.0}]}],
    "ec1_wind_snow": [{}, {"use_site": False}, {"roof": 45, "Ce": "Sheltered", "A": 1200}],
    "ec1_imposed_loads": [{}, {"element": "Column or wall (several storeys)", "n": 5},
                          {"cat": "C4 — physical activities (dance halls, gymnasia, stages)", "A": 200},
                          {"cat": "F — garages, vehicles ≤ 30 kN"},
                          {"cat": "G — traffic areas, vehicles 30–160 kN"},
                          {"cat": "H — roofs not accessible except for maintenance"},
                          {"cat": "E1 — storage (incl. books and documents)", "element": "Column or wall (several storeys)"},
                          {"element": "Column or wall (several storeys)", "n": 2},
                          {"partitions": "Heavier partitions (> 3.0 kN/m)", "mode": "My own values"},
                          {"layers": [{"name": "X", "material": "Other material (enter γ)", "t": 50, "gamma": 12}]}],
    "ec1_wind_pressures": [{}, {"roof": "Monopitch", "alpha": 15, "view": "θ = 180°"},
                           {"roof": "Monopitch", "alpha": 3}, {"roof": "Duopitch", "alpha": 3},
                           {"roof": "Flat (α < 5°)", "view": "θ = 90°"},
                           {"roof": "Flat (α < 5°)", "eave": "Parapets", "hp": 0.1},
                           {"roof": "Flat (α < 5°)", "eave": "Curved eaves"},
                           {"roof": "Flat (α < 5°)", "eave": "Mansard eaves"},
                           {"roof": "Hipped", "alpha": 25}, {"roof": "Duopitch", "alpha": -20},
                           {"internal": "From the opening ratio μ (Figure 7.13)"},
                           {"internal": "None (no openings)", "A": 1, "L": 5, "h": 20},
                           {"kind": "Canopy roof (no walls)"},
                           {"kind": "Canopy roof (no walls)", "canopy": "Duopitch canopy", "alpha": -10, "bays": 4},
                           {"roof": "Vaulted (cylindrical)", "f": 3}, {"roof": "Vaulted (cylindrical)", "f": 1, "view": "θ = 90°"},
                           {"roof": "Monopitch", "alpha": 15, "spans": 3}, {"roof": "Duopitch", "spans": 2},
                           {"internal": "Dominant opening (7.2.9(5))"},
                           {"internal": "Dominant opening (7.2.9(5))", "dom_face": "End face (width W)"},
                           {"L": 60, "Wd": 12, "h": 5},
                           {"kind": "Free-standing wall or parapet", "L": 20, "h": 2, "ret": 2, "sheltered": True},
                           {"kind": "Free-standing wall or parapet", "on_building": True, "L": 10, "h": 1, "wphi": 0.8},
                           {"kind": "Signboard", "L": 6, "h": 3, "zg": 3}, {"kind": "Signboard", "L": 10, "h": 3, "zg": 0.5}],
    "en1990_combinations": [{}],
    "ec7_berlin_wall": [{}, {"support": "Cantilever"}, {"phi": 20, "support": "Cantilever"},
                        {"approach": "DA2", "seismic": False}, {"section": "HEB 100"}],
    "ec7_retaining_wall": [{}, {"h_w": 1.5, "beta": 10}, {"approach": "DA2", "key": True},
                           {"step": True, "key": True}, {"step": True, "key": True, "toe": 0.3},
                           {"approach": "DA3", "seismic": False}, {"toe": 0.3, "heel": 1.0}],
    "ec7_gravity_wall": [{}, {"t_footing": 0}, {"h_w": 1.0, "B_body": 1.2}],
    "ec7_pad_footing": [{}, {"h": 0.4}, {"Bx": 1.2, "By": 1.2}, {"approach": "DA2"}],
    "ec2_rc_column": [{}, {"NEd": 3500}, {"L": 8, "Mh_top": 10}, {"seismic": False},
                      {"s": 300}, {"braced": False, "L": 6}, {"Mb_top": 200, "VEd": 400}],
    "ec2_rc_slab": [{}, {"punch": True}, {"type": "One-way continuous"},
                    {"type": "One-way continuous", "spans": 1}, {"e1": "Simply supported",
                    "e3": "Simply supported"}, {"h": 120, "q": 15},
                    {"punch": True, "pos": "Edge", "VEd": 150}],
    "ec7_pile": [{}, {"method": "Ground test profiles (ξ3, ξ4)", "n_prof": 3, "stiff": True},
                 {"ptype": "Driven", "T": 900}, {"L": 6}, {"G": 3000},
                 {"layers": [{"h": 30, "soil": "Sand", "gamma": 19, "phi": 32, "cu": 0}]}],
    "ec7_settlement": [{}, {"rigid": False}, {"q": 600}, {"layers": [
        {"h": 3, "soil": "Clay", "gamma": 19, "Eoed": 5, "Cc": 0.3, "Cr": 0.05, "e0": 0.9,
         "OCR": 1}]}],
    "ec7_gabion_wall": [{}, {"seismic": False, "beta": 15}, {"h_w": 1.0}, {"courses": [
        {"b": 2.0, "h": 1.0, "setback": 0}, {"b": 1.0, "h": 1.0, "setback": 0.5},
        {"b": 1.0, "h": 1.0, "setback": 0}]}],
    "ec7_embedded_wall": [{}, {"anchors": []}, {"seismic": True}, {"t": 1.0}, {"zw": 3.0},
                          {"D": 0.4, "nbar": 6}],
    "ec3_steel_column": [{}, {"section": "IPE 300", "L": 8}, {"section": "HEA 100", "NEd": 3000},
                         {"My_top": 0, "My_bot": 0}, {"VEd": 600}, {"section": "IPE 600"}],
    "ec3_bolted_connection": [{}, {"ecc": 150, "Ft": 40}, {"n1": 12, "V": 900},
                              {"thread": False, "planes": "2", "cls": "10.9"},
                              {"e1": 20, "p1": 30, "n2": 1}],
    "ec3_base_plate": [{}, {"MEd": 5}, {"MEd": 200}, {"NEd": 0, "MEd": 50}],
    "ec5_timber_beam": [{}, {"cls": "C24", "h": 250, "b": 75, "L": 4}, {"sc": "3"},
                        {"q": 0}, {"top": False, "lef_f": 2}],
    "ec6_masonry_wall": [{}, {"t": 150, "restraint": "Top and bottom (timber floors)"},
                         {"lw": 0.3}, {"restraint": "Top, bottom and both vertical edges"},
                         {"restraint": "Top, bottom and one vertical edge", "h": 6, "t": 150},
                         {"VEd": 0, "unit": "Aggregate concrete", "group": "Group 3"}],
    "ec2_tank": [{}, {"top": "Pinned (roof slab)"}, {"hgw": 2.5, "toe": 0},
                 {"H": 4, "hw": 3.8, "hs": 4}, {"hs": 0, "hgw": 0}, {"t": 130}],
    "ec8_3_assessment": [{}, {"strengthen": "None (assessment only)"},
                         {"strengthen": "FRP wrapping"}, {"strengthen": "FRP wrapping", "nf": 6},
                         {"primary": False, "detailing": True, "ribbed": False},
                         {"kl": "KL1 — limited knowledge", "VE": 400}],
    "ec3_weld": [{}, {"sides": False, "V": 50}, {"top": False}, {"a": 3, "N": 600}],
    "ec2_rc_stair": [{}, {"support": "Continuous with landings"}, {"n": 6, "t": 120}],
    "ec2_pile_cap": [{}, {"n": "2"}, {"n": "3", "Mx": -900}, {"h": 500}],
    "ec8_rc_wall": [{}, {"NEd": 9000, "MEd": 20000}, {"sh": 200, "lc": 300}, {"storeys": 10}],
    "ec7_raft": [{}, {"t": 300, "k": 3}, {"N": 6000, "Nk": 4200}],
    "ec8_5_liquefaction": [{}, {"ag": 0.05}, {"layers": [{"h": 3, "soil": "Sand", "gamma": 18,
                           "N60": 6, "FC": 5}, {"h": 6, "soil": "Sand", "gamma": 19, "N60": 8, "FC": 40}]},
                           {"zw": 30}],
    "ec3_fire": [{}, {"protection": "None"}, {"exposure": "4 sides (column)", "U": 0.3, "R": "R30"}],
    "ec5_fire": [{}, {"R": "R60", "sides": "4 sides"}, {"cls": "C24", "b": 100, "h": 200}],
    "ec2_fire": [{}, {"member": "One-way slab", "b": 70}, {"member": "Two-way slab (l_y/l_x ≤ 1.5)"},
                 {"member": "Two-way slab (1.5 < l_y/l_x ≤ 2)", "R": "R240"}, {"b": 60, "R": "R240"},
                 {"layers": False}],
    "ec7_slope_stability": [{}, {"slope": 45, "c": 0}, {"slope": 40, "nails": [
        {"z": 2, "angle": 15, "L": 9, "sh": 1.5, "Td": 150, "bond": 40}]}],
    "ec7_strip_footing": [{}, {"seismic": True}, {"B": 0.6, "MG": 40}, {"tie": False},
                          {"th": 0.3, "tn": 4, "tdia": "10"}],
}
BAD = [("ec3_steel_beam", {"L": -1}), ("ec3_steel_beam", {"L": "abc"}),
       ("ec3_steel_beam", {"section": "XYZ"}), ("ec7_retaining_wall", {"t_top": 0.5, "t_bot": 0.3}),
       ("ec7_retaining_wall", {"h_w": 50}), ("ec7_retaining_wall", {"beta": 25}),
       ("ec7_gravity_wall", {"b_top": 3}), ("ec7_pad_footing", {"D": 0.3}),
       ("ec7_pad_footing", {"cx": 5}), ("ec2_rc_beam", {"n_bars": 2.5}),
       ("beam_analysis", {"supports": [{"x": 0, "kind": "pinned"}]}),
       ("ec7_slope_stability", {"phi": 0, "c": 0}), ("ec7_berlin_wall", {"z_a": 6}),
       ("ec7_berlin_wall", {"a": 0.1}), ("ec7_retaining_wall", {"step": True, "t_low": 0.3}),
       ("ec7_retaining_wall", {"step": True, "h_step": 5}),
       ("ec7_retaining_wall", {"key": True, "key_x": 9}), ("en1990_combinations", {"actions": []}), ("ec1_wind_pressures", {"kind": "Canopy roof (no walls)", "alpha": 45}),
       ("ec1_wind_pressures", {"roof": "Monopitch", "alpha": 80}), ("ec1_wind_pressures", {"roof": "Vaulted (cylindrical)", "f": 8}), ("ec1_imposed_loads", {"layers": []}),
       ("ec1_imposed_loads", {"layers": [{"name": "X", "material": "Other material (enter γ)", "t": 50, "gamma": 0}]}),
       ("ec7_strip_footing", {"D": 0.3}),
       ("ec3_base_plate", {"lp": 260}), ("ec3_base_plate", {"w": 390}),
       ("ec3_base_plate", {"ex": 120, "lp": 400}),
       ("ec6_masonry_wall", {"unit": "Autoclaved aerated concrete", "group": "Group 2"}),
       ("ec2_tank", {"hw": 3}), ("ec3_weld", {"top": False, "bottom": False, "sides": False}),
       ("ec2_rc_stair", {"n": 2, "L": 0.1}), ("ec2_pile_cap", {"s": 800}),
       ("ec8_rc_wall", {"lc": 2500}), ("ec8_5_liquefaction", {"layers": []}),
       ("ec5_fire", {"b": 60, "R": "R120"}), ("ec8_3_assessment", {"cover": 140}), ("ec2_tank", {"hs": 3}), ("ec7_pile", {"layers": []}),
       ("ec7_pile", {"L": 40}), ("ec7_pile", {"gRd": 1.1}),
       ("ec7_pile", {"layers": [{"h": 30, "soil": "Clay", "gamma": 19, "phi": 0, "cu": 0}]}),
       ("ec7_settlement", {"layers": []}), ("ec7_settlement", {"D": 30}),
       ("ec7_gabion_wall", {"courses": []}),
       ("ec7_gabion_wall", {"courses": [{"b": 1, "h": 1, "setback": 0},
                                        {"b": 1, "h": 1, "setback": 1.5}]}),
       ("ec7_embedded_wall", {"a": 0.2}),
       ("ec7_embedded_wall", {"anchors": [{"z": 9, "alpha": 20, "sh": 2, "P0": 100, "Lfr": 6,
                                           "At": 600, "Rad": 500}]}),
       ("ec7_embedded_wall", {"anchors": [], "t": 0.5, "H": 10}), ("ec7_strip_footing", {"bw": 2})]


def collect() -> set[str]:
    from erisma.design.annex import ANNEXES

    i18n.MISSING.clear()
    for m in all_modules():
        m.schema("el")
        for code in ANNEXES:
            for inp in SCENARIOS.get(m.id, [{}]):
                render_html(m.calculate(inp, {"annex": code}, "el"))
        render_html(m.calculate({"approach": "DA1"} if any(f.name == "approach" for f in m.fields)
                                else {}, {"annex": "CY", "site": "Λεμεσός", "lat": "34.6841",
                                          "lon": "33.0379"}, "el"))
        for proj in ({"annex": "CY", "lat": "34.0", "lon": "30.0"},
                     {"annex": "CY", "lat": "35.1195", "lon": "33.0", "site": "x"},
                     {"annex": "CY", "lat": "34.92", "lon": "32.88"}):
            try:
                render_html(m.calculate({}, proj, "el"))
            except InputError:
                pass
    try:
        get_module("ec1_wind_snow").calculate({"A": 1600}, {"annex": "CY", "lat": "34.6841",
                                                            "lon": "33.0379"}, "el")
    except InputError:
        pass
    for a in ANNEXES.values():
        for z, _ in a.zones:
            i18n.tr(z, "el")
        for n in a.notes:
            i18n.tr(n, "el")
        i18n.tr(a.label, "el")
    for mid, inp in BAD:
        try:
            get_module(mid).calculate(inp, {}, "el")
        except InputError:
            pass
    for s in ["PASS", "FAIL", "ALL CHECKS PASS", "DESIGN FAILS", "max utilisation", "Check",
              "Utilisation", "Result", "Company", "Project", "Job no.", "Section / element",
              "Calc. by / checked", "Date", "In accordance with", "client",
              "Generated by Erisma", "row"]:
        i18n.tr(s, "el")
    return set(i18n.MISSING)


if __name__ == "__main__":
    for s in sorted(collect()):
        print(repr(s))
