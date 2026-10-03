"""psa_slab — PSA-style holder housing the user's card on the tracker page.

Revision: r13

Purpose: slab for the web viewer (index.html, three.js) with the proportions the user marked up in Illustrator.
Digital render only, never manufactured.

Source of truth (r07): reference-image/slab-proportions.png — the user's red guide lines over their slab photo
(3456 x 2234 screenshot; slab outline 1014..2064 x 349..2114 px = 80 x 135 mm -> 13.125 px/mm across, 13.074 down).
Red lines measured to the pixel (continuous runs), left/right averaged (the drawing sits ~2 px left of centre):
  | line                                     | sides | top    | bottom (from top) | notes                         |
  |------------------------------------------|-------|--------|-------------------|-------------------------------|
  | step: rim -> frame                       | 2.78  | 2.68   | 131.17            | square corners                |
  | divider top = label compartment bottom   |       |        | 28.22             | spans the full step width     |
  | card compartment (card lid opening)      | 4.15* | 29.75  | 129.72            | *r08: photo line (was 4.46)   |
  | rails' outer edges = clear window        | 7.35  | 34.65  | 124.90            | frosting stops here           |
  | rails' inner edges (touch the card)      | 8.30  | 35.64  | 123.83            | -> rails 1.0 thick            |
  | side rails run                           |       | 41.0   | 118.9             |                               |
  | top / bottom rails run                   | 13.7 in from each side       |                   |                               |
  | outer corner                             | ~1.1 mm straight-to-corner (quintic setback 2.4)                             |
  Card 63 x 88 (Japanese) + 0.15 clearance + 1.0 rails reproduces the window to within 0.05 mm on every side.
Depths are not visible in a front view: rim 0.8 below the frame (eBay 800482929766 side view), seats/pockets as r03.

Plan (crisp terraces approved 2026-10-03; rolled outer edge G2; r07 layout = the user's drawing):
  | patch                          | role      | type / CVs                                    | edges                        |
  |--------------------------------|-----------|-----------------------------------------------|------------------------------|
  | walls + corner walls           | primary   | planes + extruded quintics (6 CV)             | G2 wall/corner; G2 to rolls  |
  | front / back edge bevel (r12)  | secondary | Bezier 6x2 straights, 6x6 corners; each row a | G2 to face, wall, each other |
  |                                |           | corner quintic of the offset outline (r04)    |                              |
  | rim band                       | primary   | plane, trim line -> step                      | G0 at the step               |
  | frame (divider + side + bottom)| primary   | plane, U around the card compartment          | G0                           |
  | label seat, label pocket       | secondary | planes; seat fills the step above the divider | G0                           |
  | card seat, card well           | secondary | planes                                        | G0                           |
  | rails (4, 1.0 -> 0.5 trapezoid)| tertiary  | frustums: top + 4 sloped planes, raised 0.9   | G0, square corners (user)    |
  | internal corner walls (r10)    | secondary | extruded quintics (6 CV), setback 0.6         | G2 to both straight walls    |
  | label lid, card lid            | parts     | plates in their seats                         | G0                           |
  | card lid top: ring + window    | finish    | coplanar, seam on the rails' outer edges      | 0 deg seam (measured as G2)  |

Frame: origin at the assembly centre (the viewer's pivot). X right, Y up (label end at +Y), Z out of the front
toward the viewer (digital render: no process direction). Units mm.

Measured (r13): body 88 faces, 648 CVs, 92 G2 joins (worst 0.0000 deg), 124 G0 edges; 4 arms rebuilt as frustums
(20 faces replaced, asserted): base 1.0, top 0.5, sides at 15.5 deg; end-on render psa_slab_r13_arms_shaded.png.

checks.md — production method: digital render only (no process section applies). Three parts, each checked:
  | check                  | target                                  | measured                               | result |
  |------------------------|-----------------------------------------|----------------------------------------|--------|
  | C1 valid solid         | each part one closed valid solid        | body, label lid, card lid: all valid   | pass   |
  | C2 origin/orientation  | meaningful datum, axes documented       | assembly centre, axes above            | pass   |
  | C3 units/scale         | 80 x 135 x 6.68 mm                      | 80.00 x 135.00 x 6.68 mm               | pass   |
  | C4 parameter extremes  | rebuild at every min/max, C1 + G2 hold  | 12 rebuilds pass                       | pass   |
  | C5 clean topology      | no face < 0.5 mm, no edge < 0.1 mm      | narrowest 0.5 (arm top, seat drop), edge 0.50 | pass |
  | C6 revision            | rNN + changelog, rNN exports            | r13                                    | pass   |
  | C7 export round-trip   | STEP same volume; STL watertight        | STEP 3 solids same vol; 3 STLs closed  | pass   |

Changelog:
  r01  outline + sealed label and card pockets.
  r02  two shells, raised frame, recessed label window, divider groove, four rail grooves.
  r03  CGTrader layout: body + lids, rolled edges, lid seats, card well, raised rails.
  r04  (psa_slab_r04.py) line-for-line from the user's slab photo.
  r05  rails all 0.7 thick, 0.1 clear of the Japanese card.
  r06  card lid top split into frosted ring + clear window at the rails' outer edges.
  r07  every line from the user's red mark-up: square step at 2.78/2.68/3.83, label compartment = full step width
       down to the divider (28.22), card compartment 4.46 / 29.75..129.72, rails 1.0 thick 0.15 clear of the card
       (card centre 79.76 from the top), window 7.35 / 34.6..124.9, tighter outer corner; rolls use r04's
       offset-corner rows so tight corners stay G2.
  r08  from the full-res photo (reference-image/slab-bible-crop.jpg): label lid split into a frosted ring + a clear
       window exactly the label (68.7 x 19.5, centred across, 3.95..23.59 down) so the label has no gap above or below;
       card compartment side 4.46 -> 4.15 (photo highlight line), narrowing the groove and widening the frosted band
       beside the card to 3.2 mm (photo 3.1); outer groove (rim band) left clear, frame + lid rings frosted.
  r10  per user: slight round on all internal plan corners except the 4 arms — step (4), divider ends (2), label
       pocket (4), card compartment (4), card well (4); G2 quintic corners, setback R_IN 0.6; lids follow.
  r11  per user: the card section's inner groove (lid-seat rebate) set equal to the label section's: 0.8 -> 0.6.
  r13  per user: the 4 arms get a trapezoid profile — frustums with the base unchanged (0.15 off the card) and the
       top inset 0.25 all round (1.0 -> 0.5), four sloped planar faces at 15.5 deg; built as designed planes, not
       chamfer() (rules.md 1.5); the arms' crisp G0 edges were approved with their square corners (r05/r10).
  r12  per user ("very slightest chamfer" on the outermost edge; designed bevel chosen over a flat chamfer, which
       rules.md 1.5 bans): outer-edge section CVs re-spaced (1, .88, .76) so the roll reads as a crisp 45 deg bevel,
       still G2 to face and wall by construction; same patch count and CVs.
  r09  per user: label window centred vertically in the label compartment (centre 15.45; 3.02 frosted above and below).
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, "/Volumes/T7/Work/:Github/Devin/3d")
from build123d import *
from surfcheck import budget, inflections, joins, no_degeneracy, render, sew_faces, sew_regions

HERE = Path(__file__).parent
REV = "r13"

# ---------------------------------------------------------------- parameters (value, min, max)  C4
P = dict(
    W=(80.0, 79.0, 82.0), H=(135.0, 134.0, 137.0), T=(6.68, 6.4, 7.0),
    SETBACK=(2.4, 2.0, 3.0),          # outer plan corner (drawing: ~1.1 mm straight-to-corner)
    ROLL=(0.8, 0.5, 1.0),             # outer edge bevel size (face -> wall)
    R_IN=(0.6, 0.4, 0.8),             # r10: slight round on internal plan corners (quintic setback; arms stay square)
)
STEP = (2.78, 2.78, 2.68, 3.83)       # rim -> frame step: left, right, top, bottom insets (drawing)
DIVIDER_TOP = 28.22                   # label compartment bottom / divider top, from the top edge
FRAME_H = 0.8                         # frame above the rim
SEAT_D = 0.8                          # card lid seat below the frame top
LABEL_SEAT_D = 0.5                    # label seat below the rim (keeps the step line round the label compartment)
LID_T = 0.6
LABEL = dict(rebate=0.6, pocket=0.6)  # label compartment = the step rect above the divider
LABEL_WIN = (68.7, 19.5)              # clear window = the PSA label itself (user: "no gap above or below")
LABEL_CENTRE = (STEP[2] + DIVIDER_TOP) / 2   # user r09: label centred vertically in its compartment
CARD = dict(side=4.15, top=29.75, bottom=129.72, rebate=LABEL["rebate"], well=1.6)   # r11: card groove = label groove   # side: photo highlight line 4.16 (r08, was 4.46)
CARD_SIZE = (63.0, 88.0, 0.9)         # the user's Japanese card
CARD_CY = 79.76                       # card centre from the top (drawing)
RAIL_H = 0.9                          # rails stand card-thick off the floor
RAIL_T = 1.0                          # drawing: window line -> rail line 0.95 / 0.99 / 1.07
RAIL_CLEAR = 0.15                     # drawing: rail lines bound 63.4 x 88.19 round the 63 x 88 card
RAIL_TAPER = 0.25                     # r13: trapezoid arms, top inset this much on every side (1.0 base -> 0.5 top)
RAIL_SIDE_Y = (41.0, 118.9)           # side rails run (from the top)
RAIL_TB_IN = 13.7                     # top / bottom rails start this far in from each side
F = (1.0, 0.6, 0.25)                  # CV spacing for every plan corner quintic
F_BEVEL = (1.0, 0.88, 0.76)           # r12 outer-edge section: CVs bunched to the middle -> near-flat 45 deg bevel
                                      # (middle third within +-5.4 deg of 45; ends G2 to face and wall, 0.17 tightest radius)


def rails_for(W):
    cw, ch = CARD_SIZE[:2]
    l, r = W / 2 - cw / 2 - RAIL_CLEAR, W / 2 + cw / 2 + RAIL_CLEAR       # rail inner faces
    t, b = CARD_CY - ch / 2 - RAIL_CLEAR, CARD_CY + ch / 2 + RAIL_CLEAR
    return [(RAIL_TB_IN, W - RAIL_TB_IN, t - RAIL_T, t), (RAIL_TB_IN, W - RAIL_TB_IN, b, b + RAIL_T),
            (l - RAIL_T, l, *RAIL_SIDE_Y), (r, r + RAIL_T, *RAIL_SIDE_Y)]   # (x0, x1, top, bottom) from top-left


def build(W, H, T, SETBACK, ROLL, R_IN):
    """Returns (body, label lid, card lid, plan curves, CV nets), origin at the assembly centre."""
    nets = []
    rim, seat = T - FRAME_H, T - SEAT_D
    lseat = rim - LABEL_SEAT_D
    CORNERS = [((W, 0), (-1, 0), (0, 1), (0, -1), (1, 0)), ((W, H), (0, -1), (-1, 0), (1, 0), (0, 1)),
               ((0, H), (1, 0), (0, -1), (0, 1), (-1, 0)), ((0, 0), (0, 1), (1, 0), (-1, 0), (0, -1))]

    # ------------------------------------------------------------ layout curves
    def corner_cvs(c, a, b, sb):
        cx, cy = c
        return ([(cx + a[0] * sb * f, cy + a[1] * sb * f) for f in F] +
                [(cx + b[0] * sb * f, cy + b[1] * sb * f) for f in reversed(F)])

    def offset_corner(k, d):
        """Corner quintic of the outline pulled in by d (corner point moved in along both normals, setback - d);
        its first/last 3 CVs lie on the offset walls, so it is G2 to them for any d < setback."""
        c, a, b, na, nb = CORNERS[k]
        return corner_cvs((c[0] - (na[0] + nb[0]) * d, c[1] - (na[1] + nb[1]) * d), a, b, SETBACK - d)

    def outline_at(d):
        cvs = [offset_corner(k, d) for k in range(4)]
        edges = []
        for k in range(4):
            edges.append(Edge.make_line((*cvs[k - 1][-1], 0), (*cvs[k][0], 0)))
            edges.append(Edge.make_bezier(*[Vector(x, y, 0) for x, y in cvs[k]]))
        return edges

    def poly(pts):
        return Wire.make_polygon(pts, close=True)

    def rect(x0, x1, top, bottom):  # drawing coordinates (from the top-left corner) -> plan wire
        return poly([(x0, H - bottom), (x1, H - bottom), (x1, H - top), (x0, H - top)])

    outline, trim = outline_at(0.0), outline_at(ROLL)
    sl, sr, st, sb = STEP
    x0, x1, yt, yb, yd = sl, W - sr, H - st, sb, H - DIVIDER_TOP
    # internal plan corners: G2 quintics (same construction as the outline), setback R_IN; the 4 arms stay square
    r = R_IN
    qc = lambda c, a, b: Edge.make_bezier(*[Vector(x, y, 0) for x, y in corner_cvs(c, a, b, r)])
    ln = lambda p, q: Edge.make_line((*p, 0), (*q, 0))

    def rrect(x0, x1, y0, y1):  # rounded rect in plan coords
        return Wire([ln((x0 + r, y0), (x1 - r, y0)), qc((x1, y0), (-1, 0), (0, 1)),
                     ln((x1, y0 + r), (x1, y1 - r)), qc((x1, y1), (0, -1), (-1, 0)),
                     ln((x1 - r, y1), (x0 + r, y1)), qc((x0, y1), (1, 0), (0, -1)),
                     ln((x0, y1 - r), (x0, y0 + r)), qc((x0, y0), (0, 1), (1, 0))])

    # step outline, split at the divider into the label compartment (above) and the frame (below); the two
    # divider-end corners are rounded inside the label compartment, so the frame takes the small lens there
    e_br, e_tr, e_tl, e_bl = qc((x1, yb), (-1, 0), (0, 1)), qc((x1, yt), (0, -1), (-1, 0)), qc((x0, yt), (1, 0), (0, -1)), qc((x0, yb), (0, 1), (1, 0))
    d_r, d_l = qc((x1, yd), (-1, 0), (0, 1)), qc((x0, yd), (0, 1), (1, 0))      # label compartment's bottom corners
    r_lo, r_hi = ln((x1, yb + r), (x1, yd + r)), ln((x1, yd + r), (x1, yt - r))  # right side, split where the corner leaves it
    l_hi, l_lo = ln((x0, yt - r), (x0, yd + r)), ln((x0, yd + r), (x0, yb + r))
    top, bottom, div = ln((x1 - r, yt), (x0 + r, yt)), ln((x0 + r, yb), (x1 - r, yb)), ln((x0 + r, yd), (x1 - r, yd))
    step = Wire([bottom, e_br, r_lo, r_hi, e_tr, top, e_tl, l_hi, l_lo, e_bl])
    label_cmp = Wire([div, d_r, r_hi, e_tr, top, e_tl, l_hi, d_l])
    frame_out = Wire([bottom, e_br, r_lo, d_r, div, d_l, l_lo, e_bl])
    L, C = LABEL, CARD
    label_pocket = rrect(x0 + L["rebate"], x1 - L["rebate"], yd + L["rebate"], yt - L["rebate"])
    rb = C["rebate"]
    card_open = rrect(C["side"], W - C["side"], H - C["bottom"], H - C["top"])
    card_well = rrect(C["side"] + rb, W - C["side"] - rb, H - C["bottom"] + rb, H - C["top"] - rb)
    inner_curves = [e for w in (step, label_cmp, frame_out, label_pocket, card_open, card_well) for e in w.edges()
                    if e.geom_type == GeomType.BEZIER]
    RAILS = rails_for(W)
    rails = [rect(*r) for r in RAILS]

    # ------------------------------------------------------------ terraces
    terraces = sew_regions([
        ("rim", Face(Wire(trim), [step]), rim),
        ("label seat", Face(label_cmp, [label_pocket]), lseat),
        ("label pocket", Face(label_pocket), lseat - L["pocket"]),
        ("frame", Face(frame_out, [card_open]), T),
        ("card seat", Face(card_open, [card_well]), seat),
        ("card well", Face(card_well, rails), seat - C["well"]),
        *[(f"rail {i}", Face(r), seat - C["well"] + RAIL_H) for i, r in enumerate(rails)],
    ], (W, H), 0.0)

    def on_trim(f):  # the temporary walls sew_regions put up along the roll trim line
        c = f.center()
        return abs(f.normal_at(c).Z) < 1e-3 and min(e.distance_to(Vector(c.X, c.Y, 0)) for e in trim) < 1e-6
    keep = [f for f in terraces.faces() if not on_trim(f)]
    assert len(keep) == len(terraces.faces()) - 8, "expected to replace the 8 trim-line walls"

    # ------------------------------------------------------------ rolled edges + walls
    sec_d = [ROLL * f for f in F_BEVEL] + [0.0] * 3                 # inward offset of the 6 section CVs
    sec_h = [0.0] * 3 + [ROLL * f for f in reversed(F_BEVEL)]       # distance from the face, along the wall

    def rolls(z_face, sgn):
        faces = []
        for k in range(4):
            rows = [offset_corner(k, d) for d in sec_d]
            grid = [[(*rows[j][i], z_face + sgn * sec_h[j]) for j in range(6)] for i in range(6)]
            faces.append(Face.make_bezier_surface([[Vector(*p) for p in row] for row in grid]))
            nets.append([[(x - W / 2, y - H / 2, z - T / 2) for x, y, z in row] for row in grid])
            prev = [offset_corner(k - 1, d)[-1] for d in sec_d]
            here = [rows[j][0] for j in range(6)]
            strip = [[(*p[j], z_face + sgn * sec_h[j]) for j in range(6)] for p in (prev, here)]
            faces.append(Face.make_bezier_surface([[Vector(*p) for p in row] for row in strip]))
        return faces

    walls = [Face.extrude(e.moved(Location((0, 0, ROLL))), (0, 0, rim - 2 * ROLL)) for e in outline]
    # r13 trapezoid arms: drop the square rail columns (top + vertical walls), keep the floor's rail holes, and close
    # each hole with a frustum: top inset RAIL_TAPER all round, four sloped planar faces (approved crisp G0 edges)
    floor_z, top_z = T - SEAT_D - C["well"], T - SEAT_D - C["well"] + RAIL_H
    pl = [(x0, x1, H - b, H - t) for x0, x1, t, b in RAILS]          # rail footprints in plan coords
    def in_rail(f):
        bb = f.bounding_box()
        return bb.min.Z > floor_z - 1e-6 and bb.max.Z > floor_z + 1e-6 and any(
            bb.min.X > x0 - 1e-6 and bb.max.X < x1 + 1e-6 and bb.min.Y > y0 - 1e-6 and bb.max.Y < y1 + 1e-6 for x0, x1, y0, y1 in pl)
    dropped = [f for f in keep if in_rail(f)]
    assert len(dropped) == 4 * 5, f"expected 4 rails x (top + 4 walls), got {len(dropped)}"
    keep = [f for f in keep if not in_rail(f)]
    frusta = []
    for x0, x1, y0, y1 in pl:
        k = RAIL_TAPER
        b = [Vector(x0, y0, floor_z), Vector(x1, y0, floor_z), Vector(x1, y1, floor_z), Vector(x0, y1, floor_z)]
        u = [Vector(x0 + k, y0 + k, top_z), Vector(x1 - k, y0 + k, top_z), Vector(x1 - k, y1 - k, top_z), Vector(x0 + k, y1 - k, top_z)]
        frusta.append(Face(Wire.make_polygon(u, close=True)))
        frusta += [Face(Wire.make_polygon([b[i], b[(i + 1) % 4], u[(i + 1) % 4], u[i]], close=True)) for i in range(4)]
    body = sew_faces(keep + frusta + rolls(rim, -1) + rolls(0.0, +1) + walls)
    assert body.is_valid

    # ------------------------------------------------------------ lids
    # label lid: frosted ring + clear window exactly the label's size, centred across (bible photo, r08)
    lw, lh = LABEL_WIN
    lwin = rect(W / 2 - lw / 2, W / 2 + lw / 2, LABEL_CENTRE - lh / 2, LABEL_CENTRE + lh / 2)
    lplate = sew_regions([("lid", Face(label_cmp), lseat + LID_T)], (W, H), lseat)
    ltop = max(lplate.faces(), key=lambda f: f.center().Z)
    label_lid = sew_keep([f for f in lplate.faces() if not f.is_same(ltop)] +
                         [Face(label_cmp, [lwin]).moved(Location((0, 0, lseat + LID_T))),
                          Face(lwin).moved(Location((0, 0, lseat + LID_T)))])
    window = rect(RAILS[2][0], RAILS[3][1], RAILS[0][2], RAILS[1][3])   # rails' outer edges (frosting stops here)
    plate = sew_regions([("lid", Face(card_open), seat + LID_T)], (W, H), seat)
    top = max(plate.faces(), key=lambda f: f.center().Z)
    card_lid = sew_keep([f for f in plate.faces() if not f.is_same(top)] +
                        [Face(card_open, [window]).moved(Location((0, 0, seat + LID_T))),
                         Face(window).moved(Location((0, 0, seat + LID_T)))])

    shift = Pos(-W / 2, -H / 2, -T / 2)  # C2: origin at the assembly centre (the viewer's pivot)
    curves = [e for e in outline + trim if e.geom_type == GeomType.BEZIER] + inner_curves
    return shift * body, shift * label_lid, shift * card_lid, curves, nets


def sew_keep(faces):
    """surfcheck.sew_faces without its final .clean(), which would merge the coplanar ring/window back into one face."""
    from OCP.BRepBuilderAPI import BRepBuilderAPI_Sewing, BRepBuilderAPI_MakeSolid
    from OCP.TopAbs import TopAbs_SHELL
    from OCP.TopExp import TopExp_Explorer
    from OCP.TopoDS import TopoDS
    sew = BRepBuilderAPI_Sewing(1e-4)
    for f in faces:
        sew.Add(f.wrapped)
    sew.Perform()
    assert sew.NbFreeEdges() == 0, f"lid sewing left {sew.NbFreeEdges()} free edges"
    shell = TopoDS.Shell(TopExp_Explorer(sew.SewedShape(), TopAbs_SHELL).Current())
    solid = Solid(BRepBuilderAPI_MakeSolid(shell).Solid())
    return solid if solid.volume > 0 else Solid(solid.wrapped.Reversed())


G2_BODY = 2 * (8 + 8) + 16 + 8 + 18 * 2   # rolls + outer walls (56) + 18 internal corner walls x 2 straight-wall joins


def verify(name, part, g2_expected, quiet=False):
    """rules.md section 9 + checks.md C1/C5 for one part. Asserts; returns the shortest edge."""
    say = (lambda *a: None) if quiet else print
    assert isinstance(part, Solid) and part.is_valid, f"C1: {name} is not one valid solid"
    grids, wall_cvs = budget(part)
    no_degeneracy(part)
    g2, g0, wa, wk = joins(part)
    assert g2 == g2_expected, f"{name}: {g2} G2 joins, expected {g2_expected}"
    min_edge = min(e.length for e in part.edges())
    assert min_edge >= 0.1, f"C5: {name} edge under 0.1 mm ({min_edge})"
    say(f"{name}: {len(part.faces())} faces, Bezier patches {sorted(set(grids))} x{len(grids)}, extruded walls {len(wall_cvs)} "
        f"(total CVs {sum(a * b for a, b in grids) + sum(wall_cvs) * 2}), {g2} G2 joins (worst {wa:.4f} deg, dk {wk:.1e}), "
        f"{g0} G0 edges, shortest edge {min_edge:.2f} mm, volume {part.volume:.0f} mm3")
    return min_edge


if __name__ == "__main__":
    nominal = {k: v[0] for k, v in P.items()}
    body, label_lid, card_lid, curves, nets = build(**nominal)
    verify("body", body, G2_BODY)
    verify("label lid", label_lid, 4 + 8)   # 4 ring/window seams (0 deg) + 4 rounded corner walls x 2
    verify("card lid", card_lid, 4 + 8)   # 4 ring/window seams (0 deg) + 4 rounded corner walls x 2
    for e in curves:
        assert inflections(e) == 0, "plan curves have no inflections"
    print(f"R9.4 plan curves: {len(curves)} quintics, 0 inflections each")
    RAILS = rails_for(nominal["W"])
    W_, H_ = nominal["W"], nominal["H"]
    widths = {"rim band": min(STEP) - nominal["ROLL"], "frame side": CARD["side"] - STEP[0],
              "divider": CARD["top"] - DIVIDER_TOP, "frame bottom": H_ - STEP[3] - CARD["bottom"],
              "label seat": LABEL["rebate"], "card seat": CARD["rebate"], "label seat drop": LABEL_SEAT_D,
              "lid ring (min)": min(RAILS[2][0] - CARD["side"], RAILS[0][2] - CARD["top"], CARD["bottom"] - RAILS[1][3]),
              "label ring (min)": min(W_ / 2 - LABEL_WIN[0] / 2 - STEP[0], LABEL_CENTRE - LABEL_WIN[1] / 2 - STEP[2],
                                      DIVIDER_TOP - LABEL_CENTRE - LABEL_WIN[1] / 2),
              "rails": min(min(x1 - x0, b - t) for x0, x1, t, b in RAILS),
              "rail top (trapezoid)": min(min(x1 - x0, b - t) for x0, x1, t, b in RAILS) - 2 * RAIL_TAPER}
    above = LABEL_CENTRE - LABEL_WIN[1] / 2 - STEP[2]
    below = DIVIDER_TOP - LABEL_CENTRE - LABEL_WIN[1] / 2
    assert abs(above - below) < 1e-9, f"label not centred: {above} above vs {below} below"
    print(f"label centred: {above:.2f} mm frosted above and below")
    assert CARD["rebate"] == LABEL["rebate"], "card and label grooves must match (user, r11)"
    print(f"grooves: card {CARD['rebate']} mm = label {LABEL['rebate']} mm")
    print("C5 narrowest features (mm):", {k: round(v, 2) for k, v in widths.items()})
    widths = list(widths.values())
    assert min(widths) >= 0.5, f"C5: feature narrower than 0.5 mm ({min(widths)})"
    cw, ch, ct = CARD_SIZE
    assert RAILS[3][0] - RAILS[2][1] > cw and RAILS[1][2] - RAILS[0][3] > ch, "card must fit between the rails"
    gaps = (RAILS[3][0] - RAILS[2][1] - cw, RAILS[1][2] - RAILS[0][3] - ch)
    assert all(abs(g - 2 * RAIL_CLEAR) < 1e-9 for g in gaps), f"rails must sit {RAIL_CLEAR} off the card on all sides: {gaps}"
    assert len({round(min(x1 - x0, b - t), 9) for x0, x1, t, b in RAILS}) == 1, "all rails the same thickness"
    print(f"rails: all {RAIL_T} mm thick, {RAIL_CLEAR} mm clear of the {cw} x {ch} card on every side")
    assert CARD["well"] - ct > 0.5, "card must clear the lid"
    well = (CARD["side"] + CARD["rebate"], W_ - CARD["side"] - CARD["rebate"], CARD["top"] + CARD["rebate"], CARD["bottom"] - CARD["rebate"])
    assert all(well[0] <= x0 and x1 <= well[1] and well[2] <= t and b <= well[3] for x0, x1, t, b in RAILS), "rails inside the well"
    window = (RAILS[2][0], W_ - RAILS[3][1], RAILS[0][2], RAILS[1][3])
    print(f"window (rails' outer edges): sides {window[0]:.2f} / {window[1]:.2f}, top {window[2]:.2f}, bottom {window[3]:.2f} "
          f"(drawing 7.35 / 34.65 / 124.90)")
    assert abs(window[0] - 7.35) < 0.06 and abs(window[2] - 34.65) < 0.06 and abs(window[3] - 124.90) < 0.06, "window off the drawing"
    assembly = Compound([body, label_lid, card_lid])
    bb = assembly.bounding_box()
    print(f"C3 bounding box {bb.size.X:.2f} x {bb.size.Y:.2f} x {bb.size.Z:.2f} mm (target 80 x 135 x 6.68), "
          f"centre ({bb.center().X:.3f}, {bb.center().Y:.3f}, {bb.center().Z:.3f})")
    assert max(abs(bb.size.X - 80), abs(bb.size.Y - 135), abs(bb.size.Z - 6.68)) < 1e-3
    assert bb.center().length < 1e-6, "C2: origin must be the assembly centre"
    for lid in (label_lid, card_lid):
        ov = body & lid
        assert body.distance_to(lid) < 1e-6 and (ov is None or ov.volume < 1e-6), "lids must sit in their seats without overlap"
    print("lids sit in their seats, no overlap")

    for k, (v, lo, hi) in P.items():  # C4
        for x in (lo, hi):
            b, _, _, _, _ = build(**{**nominal, k: x})
            verify("body", b, G2_BODY, quiet=True)
    print(f"C4 parameter extremes: {2 * len(P)} rebuilds pass ({', '.join(f'{k} {lo}-{hi}' for k, (v, lo, hi) in P.items())})")

    views = [((0, 0, 400), (0, 0, 0), (0, 1, 0), 75),                 # front
             ((150, -110, 130), (14, 30, 0), (0, 0, 1), 38),          # three-quarter, close on the label end
             ((70, -60, 25), (34, -55, 0), (0, 0, 1), 14)]            # low and close on a corner: edge roll + rails
    render([body, label_lid, card_lid], nets, str(HERE / f"psa_slab_{REV}"), views,
           compare_ref=str(HERE.parent / "reference-image" / "slab-bible-front-crop.jpg"),
           compare_view=((0, 0, 400), (0, 0, 0), (0, 1, 0), 67.5))
    render([body], [], str(HERE / f"psa_slab_{REV}_interior"), views[1:])

    step = HERE / f"psa_slab_{REV}.step"
    export_step(assembly, str(step))
    rt = import_step(str(step))
    assert len(rt.solids()) == 3 and all(s.is_valid for s in rt.solids()), "C7: STEP round-trip"
    assert abs(rt.volume - assembly.volume) < 1e-3 * assembly.volume, "C7: STEP round-trip changed the volume"
    print("C7 STEP round-trip: 3 valid solids, same volume")

    H2, T2, seat = H_ / 2, nominal["T"] / 2, nominal["T"] - SEAT_D
    lseat = nominal["T"] - FRAME_H - LABEL_SEAT_D
    box = lambda x0, x1, top, bottom: [x0 - W_ / 2, H2 - bottom, x1 - W_ / 2, H2 - top]   # drawing -> centred plan
    layout = {
        "card": [0, H2 - CARD_CY, seat - CARD["well"] + CARD_SIZE[2] / 2 - T2],
        "label": [0, H2 - LABEL_CENTRE, lseat - LABEL["pocket"] + 0.15 - T2],
        # body: frosted inside the step (frame), clear in the outer groove and under the lids (bible photo)
        "frost": box(STEP[0], W_ - STEP[1], STEP[2], H_ - STEP[3]),
        "clear": [box(CARD["side"], W_ - CARD["side"], CARD["top"], CARD["bottom"]),
                  box(STEP[0], W_ - STEP[1], STEP[2], DIVIDER_TOP)],
        "label_clear": [box(W_ / 2 - LABEL_WIN[0] / 2, W_ / 2 + LABEL_WIN[0] / 2,
                            LABEL_CENTRE - LABEL_WIN[1] / 2, LABEL_CENTRE + LABEL_WIN[1] / 2)],
        "lid_clear": [box(RAILS[2][0], RAILS[3][1], RAILS[0][2], RAILS[1][3])],
    }
    (HERE / f"psa_slab_{REV}.json").write_text(json.dumps(layout))
    if "--stl" in sys.argv:  # web viewer meshes (requested: the browser can't load STEP)
        import pyvista as pv
        for name, part in (("body", body), ("label_lid", label_lid), ("card_lid", card_lid)):
            stl = HERE / f"psa_slab_{REV}_{name}.stl"
            export_stl(part, str(stl), tolerance=0.01, angular_tolerance=0.1)
            mesh = pv.read(str(stl))
            assert mesh.n_open_edges == 0, f"C7: {stl.name} has {mesh.n_open_edges} open edges"
            print(f"C7 {stl.name} watertight: {mesh.n_cells} triangles, 0 open edges")
