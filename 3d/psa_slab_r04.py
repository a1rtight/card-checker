"""psa_slab — the user's PSA 9 Fossil Mew holder, housing the card on the tracker page.

Revision: r04

Purpose: match reference-image/slab-bible-upright.jpg (IMG_9579, the user's own slab, 3024 x 4032, near-orthographic
front view) line for line. Digital render only (index.html, three.js), never manufactured.

Bible measurement (24.0 px/mm: the 63 x 88 mm Japanese card spans 1513 x 2115 px; scale agrees on both axes, so the
photo is used as an orthographic front view). Slab outline x 540..2466, y 256..3470 px -> 80.25 x 134.0 mm.
Edge lines from averaged gradient profiles + 2-4x crops (mm from the outer edge; top/bottom from the top/bottom edge):
  | line                                   | left | right | top  | bottom | notes                                  |
  |----------------------------------------|------|-------|------|--------|----------------------------------------|
  | rolled outer edge ends                 | 0.8  | 0.8   | 0.8  | 0.8    | highlight lines at 0.25 / 0.75          |
  | step A                                 | 1.7  | 1.7   | 2.0  | 1.65   | bright flat band below it at the bottom |
  | step B (S1): frame / card opening edge | 2.7  | 2.7   | 2.75 | 3.1    | top set to 2.6 (C5: 0.5 to label pocket)|
  | label pocket wall                      | 3.85 | 3.85  | 3.1  | 24.1 from top                             |
  | card opening top (divider underside)   |      |       | 26.4 |        | square corners onto S1                 |
  | inner step C2                          | 4.2  | 4.2   | 28.0 | 4.6    |                                        |
  | card well wall                         | 7.4  | 7.4   | 33.2 | 9.6    |                                        |
  | side rails (ledges on the well wall)   | 7.4-8.3 both sides, y 39.5..117.9 from top                       |
  | top / bottom rails (lips on the walls) | x 13.75 in from each side; top 33.2..34.25, bottom 123.3..124.4    |
  | card (63 x 88)                         | x 8.42, y 34.33                                                  |
  | label (68.7 x 19.5)                    | x 5.3, y 3.9                                                     |
Depths are not visible in a front photo: step heights 0.3-0.8 chosen to read as moulded steps within the 6.68 mm
thickness of the eBay 800482929766 drawing (side view: front raised ~0.8 near the edge).

Plan (user 2026-10-03: crisp terraces approved; r03 rolled edges; r04 "the photo is the bible").
  Body = terraces sewn from plan regions (surfcheck.sew_regions, no booleans) + designed rolled edges + walls.
  | patch                         | role      | type / CVs                                    | edges                         |
  |-------------------------------|-----------|-----------------------------------------------|-------------------------------|
  | walls + corner walls          | primary   | planes + extruded quintics (6 CV)             | G2 wall/corner; G2 to rolls   |
  | front / back edge rolls       | secondary | Bezier 6x2 straights, 6x6 corners: each row a | G2 to face, wall, each other  |
  |                               |           | corner quintic of the offset outline          |                               |
  | band A, band B, frame         | primary   | planes trimmed by G2 rounded rects            | G0 steps                      |
  | label seat, label cavity      | secondary | planes                                        | G0                            |
  | card seat, inner frame, well  | secondary | planes                                        | G0                            |
  | rails (4)                     | tertiary  | planes, notched into the well outline         | G0                            |
  | card lid, label lid           | parts     | plates in their seats                         | G0                            |

Frame: origin at the assembly centre (the viewer's pivot). X right, Y up (label end at +Y), Z out of the front
toward the viewer (digital render: no process direction). Units mm.

Measured (r04): body 92 faces: 8 Bezier 6x6 corner rolls + 8 Bezier 6x2 edge rolls + 12 extruded quintic walls
(528 CVs); 72 G2 joins (worst 0.0000 deg, curvature diff 9.7e-14), 154 G0 edges (planned crisp terraces); 16 plan
quintics, 0 inflections. Card lid 4 G2 joins. Edge overlay on the bible photo: psa_slab_r04_overlay.jpg.
Zebra: stripes continuous along the straight rolls; at the 0.8 mm corner rolls the stripe frequency aliases into
speckle at render resolution (measured G2 there is exact).

checks.md — production method: digital render only (no process section applies). Three parts, each checked:
  | check                  | target                                  | measured (r04)                         | result |
  |------------------------|-----------------------------------------|----------------------------------------|--------|
  | C1 valid solid         | each part one closed valid solid        | body, card lid, label lid: all valid   | pass   |
  | C2 origin/orientation  | meaningful datum, axes documented       | assembly centre, axes above            | pass   |
  | C3 units/scale         | 80.25 x 134.0 x 6.68 mm                 | 80.25 x 134.00 x 6.68 mm               | pass   |
  | C4 parameter extremes  | rebuild at every min/max, C1 + G2 hold  | 10 rebuilds pass                       | pass   |
  | C5 clean topology      | no face < 0.5 mm, no edge < 0.1 mm      | narrowest band 0.5, shortest edge 0.20 | pass   |
  | C6 revision            | rNN + changelog, rNN exports            | r04                                    | pass   |
  | C7 export round-trip   | STEP same volume; STL watertight        | STEP 3 solids same vol; 3 STLs closed  | pass   |

Changelog:
  r01  outline + sealed label and card pockets.
  r02  two shells, raised frame, recessed label window, divider groove, four rail grooves.
  r03  CGTrader layout: body + lids, rolled edges, lid seats, card well, raised rails.
  r04  rebuilt line-for-line from the user's slab photo: 80.25 x 134.0, 2 mm corners, steps A/B/C2, card opening
       on S1, notched rails on the well walls, Japanese card size; rolled-corner rows are per-offset quintics.
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, "/Volumes/T7/Work/:Github/Devin/3d")
from build123d import *
from surfcheck import budget, inflections, joins, no_degeneracy, render, sew_faces, sew_regions

HERE = Path(__file__).parent
REV = "r04"

# ---------------------------------------------------------------- parameters (value, min, max)  C4
P = dict(
    W=(80.25, 79.5, 81.5), H=(134.0, 133.0, 136.0), T=(6.68, 6.4, 7.0),
    SETBACK=(2.8, 2.2, 4.0),          # outer plan corner: quintic leaves each wall here (~2 mm radius look, bible)
    ROLL=(0.8, 0.6, 1.0),             # rolled outer edge
)
# insets from the outer edge: (left, right, top, bottom) — bible table in the header
STEP_A = (1.7, 1.7, 2.0, 1.65)
STEP_B = (2.7, 2.7, 2.6, 3.1)
INNER = (4.2, 4.2, 28.0, 4.6)                 # C2, top measured from the top edge
WELL = (7.4, 7.4, 33.2, 9.6)
LABEL_POCKET = (3.85, 3.85, 3.1, 24.1)        # (left, right, top, bottom-from-top)
LABEL_CAVITY_REBATE = (1.0, 1.0, 0.5, 0.5)
OPENING_TOP = 26.4                            # card opening / divider underside, from the top edge
RAIL_SIDE = (7.4, 8.3, 39.5, 117.9)           # x from the side wall line .. inner edge; y range from the top
RAIL_TB_IN = 13.75                            # top / bottom rails start this far in from each side
RAIL_TOP = (33.2, 34.25)
RAIL_BOTTOM_W = 1.1                           # bottom rail depth off the well's bottom wall (bible 123.3..124.4 from the top)
# heights below the frame top (z = T)
Z_A, Z_B = 0.6, 0.3                           # band A, band B
SEAT_C = 1.1                                  # card lid seat; card lid 0.8 thick -> flush with band B
INNER_D, WELL_D, RAIL_D = 1.5, 2.5, 1.3       # inner frame, well floor, rail tops
SEAT_L, CAVITY_L = 0.6, 1.0                   # label lid seat; label cavity floor
LID_C, LID_L = 0.8, 0.4
CARD = (63.0, 88.0, 0.9, 8.42, 34.33)         # w, h, t, x, y (Japanese card, bible position)
LABEL = (68.7, 19.5, 5.3, 3.9)                # w, h, x, y (bible)
F = (1.0, 0.6, 0.25)                          # CV spacing for every corner quintic and the roll section


def build(W, H, T, SETBACK, ROLL):
    """Returns (body, card lid, label lid, plan curves, CV nets), origin at the assembly centre."""
    nets = []
    CORNERS = [((W, 0), (-1, 0), (0, 1), (0, -1), (1, 0)), ((W, H), (0, -1), (-1, 0), (1, 0), (0, 1)),
               ((0, H), (1, 0), (0, -1), (0, 1), (-1, 0)), ((0, 0), (0, 1), (1, 0), (-1, 0), (0, -1))]

    def corner_cvs(c, a, b, sb):
        cx, cy = c
        return ([(cx + a[0] * sb * f, cy + a[1] * sb * f) for f in F] +
                [(cx + b[0] * sb * f, cy + b[1] * sb * f) for f in reversed(F)])

    def offset_corner(k, d):
        """Corner quintic of the outline pulled in by d: corner point moved in along both normals, setback - d.
        Its first/last 3 CVs lie on the offset walls, so it is G2 to them."""
        c, a, b, na, nb = CORNERS[k]
        cd = (c[0] - (na[0] + nb[0]) * d, c[1] - (na[1] + nb[1]) * d)
        return corner_cvs(cd, a, b, SETBACK - d)

    def outline_at(d, z=0.0):
        cvs = [offset_corner(k, d) for k in range(4)]
        edges = []
        for k in range(4):
            edges.append(Edge.make_line((*cvs[k - 1][-1], z), (*cvs[k][0], z)))
            edges.append(Edge.make_bezier(*[Vector(x, y, z) for x, y in cvs[k]]))
        return edges

    def rounded(l, r, t, b, sb):  # rounded rect from insets (left, right, top, bottom), G2 quintic corners
        x0, x1, y0, y1 = l, W - r, b, H - t
        cq = lambda c, a, bb: Edge.make_bezier(*[Vector(x, y, 0) for x, y in corner_cvs(c, a, bb, sb)])
        return [Edge.make_line((x0 + sb, y0), (x1 - sb, y0)), cq((x1, y0), (-1, 0), (0, 1)),
                Edge.make_line((x1, y0 + sb), (x1, y1 - sb)), cq((x1, y1), (0, -1), (-1, 0)),
                Edge.make_line((x1 - sb, y1), (x0 + sb, y1)), cq((x0, y1), (1, 0), (0, -1)),
                Edge.make_line((x0, y1 - sb), (x0, y0 + sb)), cq((x0, y0), (0, 1), (1, 0))]

    def poly(pts):
        return Wire.make_polygon(pts, close=True)

    def rect(x0, x1, top, bottom):  # bible coordinates (from the top-left corner) -> plan wire
        return poly([(x0, H - bottom), (x1, H - bottom), (x1, H - top), (x0, H - top)])

    # ------------------------------------------------------------ layout curves
    outline = outline_at(0.0)
    trim = outline_at(ROLL)
    sb_a, sb_b = max(SETBACK - STEP_A[0], 0.8), max(SETBACK - STEP_B[0], 0.6)
    step_a = rounded(*STEP_A, sb_a)
    step_b = rounded(*STEP_B, sb_b)
    # S1 split at the card opening top: frame (upper part) and card opening (lower part)
    l, r, t, b = STEP_B
    x0, x1, y0, y1, yo = l, W - r, b, H - t, H - OPENING_TOP
    cq = lambda c, a, bb: Edge.make_bezier(*[Vector(x, y, 0) for x, y in corner_cvs(c, a, bb, sb_b)])
    frame_outer = Wire([Edge.make_line((x1, yo), (x1, y1 - sb_b)), cq((x1, y1), (0, -1), (-1, 0)),
                        Edge.make_line((x1 - sb_b, y1), (x0 + sb_b, y1)), cq((x0, y1), (1, 0), (0, -1)),
                        Edge.make_line((x0, y1 - sb_b), (x0, yo)), Edge.make_line((x0, yo), (x1, yo))])
    opening = Wire([Edge.make_line((x0, yo), (x0, y0 + sb_b)), cq((x0, y0), (0, 1), (1, 0)),
                    Edge.make_line((x0 + sb_b, y0), (x1 - sb_b, y0)), cq((x1, y0), (-1, 0), (0, 1)),
                    Edge.make_line((x1, y0 + sb_b), (x1, yo)), Edge.make_line((x1, yo), (x0, yo))])
    # step B with its sides split at the opening top, matching the frame / opening regions
    step_b_split = Wire([e for e in frame_outer.edges() if abs(e.position_at(0.5).Y - yo) > 1e-6] +
                        [e for e in opening.edges() if abs(e.position_at(0.5).Y - yo) > 1e-6])
    inner = rect(INNER[0], W - INNER[1], INNER[2], H - INNER[3])
    lp_l, lp_r, lp_t, lp_b = LABEL_POCKET
    label_pocket = rect(lp_l, W - lp_r, lp_t, lp_b)
    rl, rr, rt, rb = LABEL_CAVITY_REBATE
    label_cavity = rect(lp_l + rl, W - lp_r - rr, lp_t + rt, lp_b - rb)

    # well floor outline with the four rails notched in along its walls (bible: rails sit on the walls)
    wl, wr, wt, wb = WELL
    X0, X1, Yt, Yb = wl, W - wr, H - wt, wb               # plan coords of the well
    sx0, sx1, sy0, sy1 = RAIL_SIDE                        # side rails: x wall..inner edge, y from the top
    tb0, tb1 = RAIL_TB_IN, W - RAIL_TB_IN
    rt0, rt1 = H - RAIL_TOP[0], H - RAIL_TOP[1]           # top rail plan y (wall, inner)
    rb0, rb1 = wb, wb + RAIL_BOTTOM_W                     # bottom rail plan y (wall, inner)
    ys0, ys1 = H - sy1, H - sy0                           # side rail plan y range
    xin_l, xin_r = sx1, W - sx1                           # side rail inner edges
    well_floor = poly([
        (X0, Yb), (tb0, Yb), (tb0, rb1), (tb1, rb1), (tb1, Yb), (X1, Yb),          # bottom wall + bottom rail notch
        (X1, ys0), (xin_r, ys0), (xin_r, ys1), (X1, ys1), (X1, Yt),               # right wall + right rail
        (tb1, Yt), (tb1, rt1), (tb0, rt1), (tb0, Yt), (X0, Yt),                   # top wall + top rail
        (X0, ys1), (xin_l, ys1), (xin_l, ys0), (X0, ys0)])                        # left wall + left rail
    rails = [rect(tb0, tb1, RAIL_TOP[0], RAIL_TOP[1]), rect(tb0, tb1, H - rb1, H - rb0),
             rect(X0, xin_l, sy0, sy1), rect(xin_r, X1, sy0, sy1)]
    # well outline split at the rail ends, so each wall piece has exactly one neighbour (sew_regions)
    well = poly([(X0, Yb), (tb0, Yb), (tb1, Yb), (X1, Yb), (X1, ys0), (X1, ys1), (X1, Yt),
                 (tb1, Yt), (tb0, Yt), (X0, Yt), (X0, ys1), (X0, ys0)])

    # ------------------------------------------------------------ terraces
    terraces = sew_regions([
        ("band A", Face(Wire(trim), [Wire(step_a)]), T - Z_A),
        ("band B", Face(Wire(step_a), [step_b_split]), T - Z_B),
        ("frame", Face(frame_outer, [label_pocket]), T),
        ("label seat", Face(label_pocket, [label_cavity]), T - SEAT_L),
        ("label cavity", Face(label_cavity), T - CAVITY_L),
        ("card seat", Face(opening, [inner]), T - SEAT_C),
        ("inner frame", Face(inner, [well]), T - INNER_D),
        ("well floor", Face(well_floor), T - WELL_D),
        *[(f"rail {i}", Face(r), T - RAIL_D) for i, r in enumerate(rails)],
    ], (W, H), 0.0)

    def on_trim(f):  # the temporary walls sew_regions put up along the roll trim line
        c = f.center()
        return abs(f.normal_at(c).Z) < 1e-3 and min(e.distance_to(Vector(c.X, c.Y, 0)) for e in trim) < 1e-6
    keep = [f for f in terraces.faces() if not on_trim(f)]
    assert len(keep) == len(terraces.faces()) - 8, "expected to replace the 8 trim-line walls"

    # ------------------------------------------------------------ rolled edges + walls
    sec_d = [ROLL * f for f in F] + [0.0] * 3                 # inward offset of the 6 section CVs
    sec_h = [0.0] * 3 + [ROLL * f for f in reversed(F)]       # distance from the face, along the wall

    def rolls(z_face, sgn):
        faces = []
        for k, (c, a, b, na, nb) in enumerate(CORNERS):
            rows = [offset_corner(k, d) for d in sec_d]          # one corner quintic per section CV
            grid = [[(*rows[j][i], z_face + sgn * sec_h[j]) for j in range(6)] for i in range(6)]
            faces.append(Face.make_bezier_surface([[Vector(*p) for p in row] for row in grid]))
            nets.append([[(x - W / 2, y - H / 2, z - T / 2) for x, y, z in row] for row in grid])
            prev = [offset_corner(k - 1, d)[-1] for d in sec_d]  # straight run into this corner
            here = [rows[j][0] for j in range(6)]
            strip = [[(*p[j], z_face + sgn * sec_h[j]) for j in range(6)] for p in (prev, here)]
            faces.append(Face.make_bezier_surface([[Vector(*p) for p in row] for row in strip]))
        return faces

    rim = T - Z_A
    walls = [Face.extrude(e.moved(Location((0, 0, ROLL))), (0, 0, rim - 2 * ROLL)) for e in outline]
    body = sew_faces(keep + rolls(rim, -1) + rolls(0.0, +1) + walls)
    assert body.is_valid

    # ------------------------------------------------------------ lids
    card_lid = sew_regions([("lid", Face(opening), T - SEAT_C + LID_C)], (W, H), T - SEAT_C)
    label_lid = sew_regions([("lid", Face(label_pocket), T - SEAT_L + LID_L)], (W, H), T - SEAT_L)

    shift = Pos(-W / 2, -H / 2, -T / 2)
    curves = [e for e in outline + trim + step_a + step_b if e.geom_type == GeomType.BEZIER]
    return shift * body, shift * card_lid, shift * label_lid, curves, nets


G2_BODY = 2 * (8 + 8) + 16 + 8 + 8 + 8   # rolls (blend-blend + blend-face, x2), 16 roll-wall, 8 outer walls, 8 step A walls, 8 step B walls


def verify(name, part, g2_expected, quiet=False):
    say = (lambda *a: None) if quiet else print
    assert isinstance(part, Solid) and part.is_valid, f"C1: {name} is not one valid solid"
    grids, wall_cvs = budget(part)
    no_degeneracy(part)
    g2, g0, wa, wk = joins(part)
    assert g2 == g2_expected, f"{name}: {g2} G2 joins, expected {g2_expected}"
    min_edge = min(e.length for e in part.edges())
    assert min_edge >= 0.1, f"C5: {name} edge under 0.1 mm ({min_edge})"
    say(f"{name}: {len(part.faces())} faces, Bezier {sorted(set(grids))} x{len(grids)}, extruded walls {len(wall_cvs)} "
        f"(total CVs {sum(a * b for a, b in grids) + sum(wall_cvs) * 2}), {g2} G2 joins (worst {wa:.4f} deg, dk {wk:.1e}), "
        f"{g0} G0 edges, shortest edge {min_edge:.2f} mm, volume {part.volume:.0f} mm3")


if __name__ == "__main__":
    nominal = {k: v[0] for k, v in P.items()}
    W, H, T = nominal["W"], nominal["H"], nominal["T"]
    body, card_lid, label_lid, curves, nets = build(**nominal)
    verify("body", body, G2_BODY)
    verify("card lid", card_lid, 2 * 2)   # its rounded bottom corners (step B quintics) meet the sides G2
    verify("label lid", label_lid, 0)
    for e in curves:
        assert inflections(e) == 0, "plan curves have no inflections"
    print(f"R9.4 plan curves: {len(curves)} quintics, 0 inflections each")
    # C5 narrowest bands (mm) and card / label fit
    bands = {"band A": min(a - ROLLv for a, ROLLv in zip(STEP_A, [nominal["ROLL"]] * 4)),
             "band B": min(b - a for a, b in zip(STEP_A, STEP_B)),
             "frame above label pocket": LABEL_POCKET[2] - STEP_B[2], "card seat": min(i - s for i, s in zip(INNER[:2], STEP_B[:2])),
             "label seat": min(LABEL_CAVITY_REBATE), "rails": min(RAIL_SIDE[1] - RAIL_SIDE[0], RAIL_TOP[1] - RAIL_TOP[0], RAIL_BOTTOM_W)}
    assert min(bands.values()) >= 0.5 - 1e-9, f"C5: {bands}"
    print("C5 narrowest bands (mm):", {k: round(v, 2) for k, v in bands.items()})
    cw, ch, ct, cx, cy = CARD
    assert cx > RAIL_SIDE[1] and cx + cw < W - RAIL_SIDE[1] and cy > RAIL_TOP[1] and cy + ch < H - WELL[3] - RAIL_BOTTOM_W, "card between rails"
    assert WELL_D - INNER_D >= ct - 1e-9 and RAIL_D > SEAT_C, "card sits in the well, rails clear the lid"
    lw, lh, lx, ly = LABEL
    assert lx > LABEL_POCKET[0] + LABEL_CAVITY_REBATE[0] and lx + lw < W - LABEL_POCKET[1] - LABEL_CAVITY_REBATE[1], "label fits (x)"
    assert ly > LABEL_POCKET[2] + LABEL_CAVITY_REBATE[2] and ly + lh < LABEL_POCKET[3] - LABEL_CAVITY_REBATE[3], "label fits (y)"
    assembly = Compound([body, card_lid, label_lid])
    bb = assembly.bounding_box()
    print(f"C3 bounding box {bb.size.X:.2f} x {bb.size.Y:.2f} x {bb.size.Z:.2f} mm (target {W} x {H} x {T}), "
          f"centre ({bb.center().X:.3f}, {bb.center().Y:.3f}, {bb.center().Z:.3f})")
    assert max(abs(bb.size.X - W), abs(bb.size.Y - H), abs(bb.size.Z - T)) < 1e-3 and bb.center().length < 1e-6
    for lid in (card_lid, label_lid):
        ov = body & lid
        assert body.distance_to(lid) < 1e-6 and (ov is None or ov.volume < 1e-6), "lids sit in their seats without overlap"
    print("lids sit in their seats, no overlap")

    for k, (v, lo, hi) in P.items():  # C4
        for x in (lo, hi):
            b, l1, l2, _, _ = build(**{**nominal, k: x})
            verify("body", b, G2_BODY, quiet=True)
    print(f"C4 parameter extremes: {2 * len(P)} rebuilds pass ({', '.join(f'{k} {lo}-{hi}' for k, (v, lo, hi) in P.items())})")

    views = [((0, 0, 400), (0, 0, 0), (0, 1, 0), 75),
             ((150, -110, 130), (14, 30, 0), (0, 0, 1), 38),
             ((60, -75, 30), (30, -56, 0), (0, 0, 1), 13)]
    render([body, card_lid, label_lid], nets, str(HERE / f"psa_slab_{REV}"), views)
    render([body], [], str(HERE / f"psa_slab_{REV}_interior"), views[1:])   # lids off: well, rails, seats

    step = HERE / f"psa_slab_{REV}.step"
    export_step(assembly, str(step))
    rt = import_step(str(step))
    assert len(rt.solids()) == 3 and all(s.is_valid for s in rt.solids()), "C7: STEP round-trip"
    assert abs(rt.volume - assembly.volume) < 1e-3 * assembly.volume, "C7: STEP round-trip changed the volume"
    print("C7 STEP round-trip: 3 valid solids, same volume")

    to_plan = lambda x, y: [x - W / 2, H / 2 - y]          # bible (from top-left) -> centred plan
    layout = {
        "card": [*to_plan(cx + cw / 2, cy + ch / 2), (T - WELL_D) + ct / 2 - T / 2], "card_px": [cw * 10, ch * 10],
        "label": [*to_plan(lx + lw / 2, ly + lh / 2), (T - CAVITY_L) + 0.05 - T / 2], "label_px": [lw * 10, lh * 10],
        # body faces frosted inside the frame (step B) except under the lids
        "frost": [*to_plan(STEP_B[0], STEP_B[2]), *to_plan(W - STEP_B[1], OPENING_TOP)],
        "clear": [[*to_plan(LABEL_POCKET[0], LABEL_POCKET[2]), *to_plan(W - LABEL_POCKET[1], LABEL_POCKET[3])]],
    }
    (HERE / f"psa_slab_{REV}.json").write_text(json.dumps(layout))
    if "--stl" in sys.argv:
        import pyvista as pv
        for name, part in (("body", body), ("card_lid", card_lid), ("label_lid", label_lid)):
            stl = HERE / f"psa_slab_{REV}_{name}.stl"
            export_stl(part, str(stl), tolerance=0.01, angular_tolerance=0.1)
            mesh = pv.read(str(stl))
            assert mesh.n_open_edges == 0, f"C7: {stl.name} has {mesh.n_open_edges} open edges"
            print(f"C7 {stl.name} watertight: {mesh.n_cells} triangles, 0 open edges")
