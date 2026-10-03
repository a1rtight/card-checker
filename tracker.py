"""Track one card's market: pricecharting (value + history + sales) and 130point (sales + live listings) -> index.html"""
import base64, html, json, os, re, statistics, sys, urllib.parse, urllib.request
from collections import deque
from datetime import datetime, timedelta, timezone

CARD = {
    "name": "Mew #151 Holo — Japanese Fossil (1997)",
    "grade": "PSA 9",
    "label": ["1996 P.M. JAPANESE FOSSIL", "MEW – HOLO", "#151"],  # as printed on the PSA label: set, card, number
    "cert": "43144250",
    "pricecharting": "https://www.pricecharting.com/game/pokemon-japanese-mystery-of-the-fossils/mew-151",
    "query": "fossil mew psa 9 japanese",          # 130point search
    "must": [r"\bmew\b", r"japan|\bjp\b|jpn", r"fossil"],  # every title must match all of these
    "foil": None,  # None = guess from name; or force one of FOILS' values, e.g. "rare holo cosmos"
}
# pricecharting reuses video-game field names for card grades
# card name keyword -> pokemon-cards-css data-rarity (first match wins)
FOILS = [(r"reverse holo", "common reverse holo"), (r"cosmos|galaxy", "rare holo cosmos"),
         (r"vmax", "rare holo vmax"), (r"vstar", "rare holo vstar"), (r"\bv\b", "rare holo v"),
         (r"radiant", "radiant rare"), (r"amazing rare", "amazing rare"), (r"rainbow", "rare rainbow"),
         (r"gold|secret", "rare secret"), (r"full art", "rare ultra"), (r"shiny", "rare shiny"), (r"holo", "rare holo")]
VINTAGE_UNTIL = 2002  # WotC / early Japanese: starry "galaxy" holo, art-box-only foil
ART_BOX = (.116, .135, .888, .522)  # vintage art window as fractions of the card (left, top, right, bottom)
SLAB = os.path.join(os.path.dirname(os.path.abspath(__file__)), "3d", "psa_slab_r13")  # built by 3d/psa_slab.py --stl
MASKS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "assets", "masks")


def card_year():
    y = re.search(r"\b(19[89]\d|20\d\d)\b", CARD["name"])
    return int(y.group(1)) if y else None


def foil():
    if CARD["foil"]:
        return CARD["foil"]
    name = CARD["name"].lower()
    rarity = next((r for pat, r in FOILS if re.search(pat, name)), "common")
    if rarity == "rare holo" and (card_year() or 9999) <= VINTAGE_UNTIL:
        return "rare holo cosmos"
    return rarity


def vintage():
    return (card_year() or 9999) <= VINTAGE_UNTIL


def blobs(px, w, h):
    """8-connected components of truthy pixels."""
    seen = set()
    for y0 in range(h):
        for x0 in range(w):
            if px[x0, y0] and (x0, y0) not in seen:
                blob, q = [], deque([(x0, y0)])
                seen.add((x0, y0))
                while q:
                    x, y = q.popleft()
                    blob.append((x, y))
                    for dx in (-1, 0, 1):
                        for dy in (-1, 0, 1):
                            n = (x + dx, y + dy)
                            if 0 <= n[0] < w and 0 <= n[1] < h and px[n] and n not in seen:
                                seen.add(n)
                                q.append(n)
                yield blob


def scan_crop(image_url):
    """CSS transform that crops the black border pricecharting scans have round the card (left, top, right, bottom
    fractions found per scan: rows/cols near black in the middle of each side), so it doesn't read as a shadow."""
    if not image_url:
        return ""
    from io import BytesIO
    from PIL import Image
    im = Image.open(BytesIO(urllib.request.urlopen(urllib.request.Request(image_url, headers={"User-Agent": UA}), timeout=30).read())).convert("L")
    w, h = im.size
    px = im.load()
    def run(get, n):  # how many leading pixels are near-black, sampled across the middle half of that side
        return max(next((i for i in range(n // 4) if get(i, k) > 40), 0) for k in range(int(0.25 * (w if n == h else h)), int(0.75 * (w if n == h else h)), 7))
    l = run(lambda i, k: px[i, k], w); r = run(lambda i, k: px[w - 1 - i, k], w)
    t = run(lambda i, k: px[k, i], h); b = run(lambda i, k: px[k, h - 1 - i], h)
    l, r, t, b = (l + 1) / w, (r + 1) / w, (t + 1) / h, (b + 1) / h   # +1 px for the anti-aliased edge
    sx, sy = 1 / (1 - l - r), 1 / (1 - t - b)
    return f"transform-origin:0 0;transform:scale({sx:.5f},{sy:.5f}) translate({-l * 100:.3f}%,{-t * 100:.3f}%)"


def foil_mask(image_url):
    """Opaque = foil. Vintage holos only foil the art background, the pokemon is printed over it in solid ink.
    Generated once per card; edit the PNG by hand if the guess is off and it won't be overwritten."""
    if not (image_url and vintage() and "holo" in foil()):
        return None
    path = os.path.join(MASKS, re.sub(r"\W+", "-", CARD["pricecharting"].rstrip("/").split("/game/")[-1]) + ".png")
    if not os.path.exists(path):
        from io import BytesIO
        from PIL import Image, ImageChops, ImageFilter
        im = Image.open(BytesIO(urllib.request.urlopen(urllib.request.Request(image_url, headers={"User-Agent": UA}), timeout=30).read())).convert("RGB")
        W, H = im.size
        box = (round(W * ART_BOX[0]), round(H * ART_BOX[1]), round(W * ART_BOX[2]), round(H * ART_BOX[3]))
        art = im.crop(box)
        w, h = art.size
        _, sat, val = art.convert("HSV").split()
        # ponytail: "pokemon = bright, low-saturation, big blob" suits pale pokemon on dark galaxy foil; dark pokemon need a hand-made mask
        raw = ImageChops.multiply(val.point(lambda x: 255 * (x > 150)), sat.point(lambda x: 255 * (x < 120))).filter(ImageFilter.MaxFilter(3))
        subject = Image.new("L", (w, h))
        sp = subject.load()
        for b in blobs(raw.load(), w, h):
            if len(b) > 0.02 * w * h:  # sparkles are tiny
                for p in b:
                    sp[p] = 255
        for b in blobs(ImageChops.invert(subject).load(), w, h):  # fill small holes (eye, line work), not tail loops
            if len(b) < 0.01 * w * h and not any(x in (0, w - 1) or y in (0, h - 1) for x, y in b):
                for p in b:
                    sp[p] = 255
        alpha = Image.new("L", (W, H))
        alpha.paste(ImageChops.invert(subject.filter(ImageFilter.MaxFilter(3))), box)  # grow over the ink outline
        mask = Image.new("RGBA", (W, H), (255, 255, 255, 0))
        mask.putalpha(alpha)  # CSS masks use alpha: opaque = foil shows
        os.makedirs(MASKS, exist_ok=True)
        mask.save(path)
    return "data:image/png;base64," + base64.b64encode(open(path, "rb").read()).decode()  # inline: Chrome blocks CSS masks from file:// pages


PC_GRADE = {"ungraded": ("used", "used"), "7": ("cib", "cib"), "8": ("new", "new"),
            "9": ("graded", "graded"), "9.5": ("boxonly", "box-only"), "10": ("manualonly", "manual-only")}
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0 Safari/537.36"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "index.html")
PROFILE = os.path.expanduser("~/.venvs/card-checker/profile")
FX = {"rate": None, "date": ""}  # USD -> GBP, filled per run


PSA_WORDS = {"10": "GEM MT", "9": "MINT", "8": "NM-MT", "7": "NM", "6": "EX-MT", "5": "EX", "4": "VG-EX", "3": "VG", "2": "GOOD", "1": "PR"}


def grade_num():
    return CARD["grade"].split()[-1]


def title_ok(t):
    grader, g = CARD["grade"].split()
    # exact grade only: "PSA 9" must not match "PSA 9.5" or "PSA 10"
    return (re.search(rf"\b{grader}\s*(?:[a-z-]+\s+){{0,2}}{re.escape(g)}(?![.\d])", t, re.I)  # "PSA 9", "PSA MINT 9"
            and all(re.search(p, t, re.I) for p in CARD["must"]))


def money(s):
    return float(s.replace("$", "").replace(",", ""))


def pricecharting():
    req = urllib.request.Request(CARD["pricecharting"], headers={"User-Agent": UA})
    h = urllib.request.urlopen(req, timeout=30).read().decode()
    chart_key, section = PC_GRADE[grade_num()]
    history = [(t / 1000, c / 100) for t, c in json.loads(re.search(r"VGPC\.chart_data = (\{.*?\});", h).group(1))[chart_key] if c]
    i = h.find(f'class="completed-auctions-{section}"')
    block = h[i:h.find("</table>", i)]
    sales = []
    for row in re.findall(r'<tr id="([^"]+)">(.*?)</tr>', block, re.S):
        rid, body = row
        cell = re.search(r'<td class="title">(.*?)</td>', body, re.S).group(1)
        title = html.unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>|\[[^\]]*\]\s*$", "", cell.strip()))).strip()
        link = re.search(r'href="([^"]+)"', cell)  # Goldin etc. rows have no link
        url = html.unescape(link.group(1)) if link else ""
        venue = re.search(r"\[([^\]]+)\]\s*$", cell.strip())
        prices = re.findall(r'class="js-price[^"]*"[^>]*>\s*(\$[\d,.]+)', body)  # first = sold / best-offer accepted
        date = re.search(r'class="date">([\d-]+)', body).group(1)
        sales.append({"id": rid.split("-")[-1], "title": title, "url": url, "price": money(prices[0]),
                      "date": datetime.fromisoformat(date).replace(tzinfo=timezone.utc), "src": f"pricecharting / {venue.group(1)}" if venue else "pricecharting",
                      "type": "Best offer" if "best offer accepted" in body else ""})
    img = re.search(r'src="(https://storage\.googleapis\.com/images\.pricecharting\.com/[^"]+)"', h)
    return {"history": history, "sales": sales, "image": img and img.group(1).replace("/240.jpg", "/1600.jpg")}


CARDS_JS = "els => els.map(e => ({...e.dataset, text: e.innerText.replace(/\\s+/g, ' ')}))"


def browser():
    from playwright.sync_api import sync_playwright
    # ponytail: headless is blocked by Cloudflare and eBay, so a real Chrome window is pushed off-screen instead
    c = sync_playwright().start().chromium.launch_persistent_context(
        PROFILE, channel="chrome", headless=False, args=["--disable-blink-features=AutomationControlled", "--window-position=-3000,-3000"])
    return c.new_page()


def point130(pg):
    pg.goto("https://130point.com/sales/", wait_until="load")
    for attempt in range(3):  # the page can wipe the box while it finishes loading, so retry
        pg.wait_for_timeout(3000)
        box = pg.get_by_placeholder("Search by player, set, year, etc").first
        box.fill(CARD["query"])
        box.press("Enter")
        try:
            pg.wait_for_selector("[data-sold-index]", timeout=25000)
            break
        except Exception:
            if attempt == 2:
                raise
    pg.wait_for_timeout(3000)
    sold_raw = pg.eval_on_selector_all("[data-sold-index]", CARDS_JS)
    sold = []
    for x in sold_raw:
        usd = re.findall(r"\$([\d,.]+) USD", x["text"])
        if not usd:
            continue
        sold.append({"id": x["itemId"].split("|")[1] if "|" in x["itemId"] else x["itemId"], "title": x["itemTitle"],
                     "url": x["itemUrl"], "price": money(usd[-1]),  # last USD figure = accepted best offer when shown
                     "date": datetime.fromisoformat(x["itemEndtime"].replace("Z", "+00:00")), "src": "130point",
                     "type": "Best offer" if "Best Offer" in x["text"] else "Auction" if "Auction" in x["text"] else "Fixed price"})
    return sold


EBAY_JS = """els => els.map(e => ({id: e.dataset.listingid, title: e.querySelector('.s-card__title')?.innerText || '',
    price: e.querySelector('.s-card__price')?.innerText || '', text: e.innerText.replace(/\\s+/g, ' ')}))"""


def ebay_live(pg, auctions):
    """Active eBay.com listings: auctions sorted ending soonest, or buy it now sorted cheapest."""
    q = urllib.parse.quote_plus(CARD["query"])
    pg.goto(f"https://www.ebay.com/sch/i.html?_nkw={q}&_ipg=120&" + ("LH_Auction=1&_sop=1" if auctions else "LH_BIN=1&_sop=15"),
            wait_until="domcontentloaded")
    pg.wait_for_selector("li.s-card[data-listingid]")
    now, out = datetime.now(timezone.utc), []
    for x in pg.eval_on_selector_all("li.s-card[data-listingid]", EBAY_JS):
        price = re.search(r"\$([\d,.]+)", x["price"])
        if not price:
            continue  # non-USD or missing price
        item = {"title": re.sub(r"^New listing|Opens in a new window or tab", "", x["title"], flags=re.I).strip(),
                "url": f"https://www.ebay.com/itm/{x['id']}", "price": money(price.group(1)), "type": "Buy it now", "ends": None}
        if auctions:
            bids = re.search(r"(\d+) bids?", x["text"])
            left = re.search(r"Time left\s*((?:\d+[dhms]\s*)+)", x["text"])
            if not left:
                continue
            parts = dict((u, int(n)) for n, u in re.findall(r"(\d+)([dhms])", left.group(1)))
            item.update(type=f"{bids.group(1) if bids else 0} bids",
                        ends=now + timedelta(days=parts.get("d", 0), hours=parts.get("h", 0), minutes=parts.get("m", 0), seconds=parts.get("s", 0)))
        out.append(item)
    return out


def pct(now, then):
    return None if not then else (now - then) / then * 100


def fx():
    try:
        d = json.load(urllib.request.urlopen(urllib.request.Request("https://api.frankfurter.dev/v1/latest?base=USD&symbols=GBP", headers={"User-Agent": UA}), timeout=15))
        FX.update(rate=d["rates"]["GBP"], date=d["date"])
    except Exception as e:  # no rate -> page stays in USD only
        print("FX failed:", e, file=sys.stderr)


def build():
    fx()
    pc = pricecharting()
    pg = browser()
    pg.set_default_timeout(60000)
    def attempt(name, fn, *a):  # one source failing shouldn't sink the page
        try:
            return fn(pg, *a)
        except Exception as e:
            print(f"{name} failed:", e, file=sys.stderr)
            return []
    sold130 = attempt("130point", point130)
    live = [l for l in attempt("eBay auctions", ebay_live, True) + attempt("eBay buy it now", ebay_live, False) if title_ok(l["title"])]

    seen, sales = set(), []
    for s in sorted(sold130 + pc["sales"], key=lambda s: s["date"], reverse=True):
        if s["id"] not in seen and title_ok(s["title"]):
            seen.add(s["id"])
            sales.append(s)

    now = datetime.now(timezone.utc)
    def window(days): return [s["price"] for s in sales if s["date"] >= now - timedelta(days=days)]
    def med(xs): return statistics.median(xs) if xs else None
    hist = pc["history"]
    def hist_ago(days):
        t = (now - timedelta(days=days)).timestamp()
        older = [v for ts, v in hist if ts <= t]
        return older[-1] if older else None
    pc_value = hist[-1][1] if hist else None

    stats = {
        "pc_value": pc_value,
        "med30": med(window(30)), "med90": med(window(90)),
        "n30": len(window(30)), "n90": len(window(90)), "n": len(sales),
        "last10": med([s["price"] for s in sales[:10]]),
        "changes": {k: pct(pc_value, hist_ago(d)) for k, d in (("1M", 30), ("3M", 91), ("6M", 182), ("1Y", 365))},
        # our own trend: median of last 30 days vs the 30 days before that
        "sales_trend": pct(med(window(30)), med([s["price"] for s in sales if now - timedelta(days=60) <= s["date"] < now - timedelta(days=30)])),
    }
    # ponytail: fixed 50% cut-off drops junk asks; auctions exempt since early bids are legitimately low
    floor = (stats["med90"] or 0) * 0.5
    bins = sorted((l for l in live if l["type"] == "Buy it now" and l["price"] >= floor), key=lambda l: l["price"])[:8]
    auctions = sorted((l for l in live if l["type"] != "Buy it now"), key=lambda l: l["ends"])[:8]
    stats["bin_low"] = bins[0]["price"] if bins else None
    open(OUT, "w").write(render(pc, sales, bins, auctions, stats, now))
    print(f"wrote {OUT}: {len(sales)} sales, {len(bins)} buy it now, {len(auctions)} auctions")


def fmt(v):
    """Default display: GBP when we have a rate. The page's toggle re-formats from data-usd."""
    sym, v = ("£", v * FX["rate"]) if FX["rate"] else ("$", v)
    return f"{sym}{v:,.0f}" if v >= 100 else f"{sym}{v:,.2f}"


# PSA label, measured from the user's slab photo (reference-image/slab-bible-upright.jpg, 24 px/mm); units mm,
# origin at the label's top-left. Rendered at 10 px/mm (CSS3D scales 0.1 -> mm).
LABEL_SPEC = {
    "size": (68.7, 19.5), "panel": (1.7, 1.6, 1.45, 1.75),        # red frame bands: left, top, right, bottom
    "font": "Arial, Helvetica, sans-serif",
    # text: (left or right edge, cap top, font size, letter spacing, align)
    "set":   (3.78, 4.04, 3.436, 0.049, "left"),
    "card":  (3.62, 7.41, 3.436, -0.082, "left"),
    "num":   (65.20, 4.20, 3.324, 0.196, "right"),
    "grade": (65.15, 7.46, 3.324, 0.109, "right"),
    "gnum":  (65.10, 11.04, 3.324, 0.0, "right"),
    "cert":  (65.05, 14.82, 3.97, -0.107, "right"),
    "bars":  (3.62, 14.08, 3.59, 0.2125),                         # left, top, height, narrow bar (wide = 3x)
    "logo":  (30.1, 13.95, 9.0, 5.05),                           # box left, top, width, height
    "logo_text": (30.9, 14.8, 3.56),                             # letters left, cap top, font size
}
LABEL_COLOURS = dict(red="#cf2a37", panel="#f3f5f5", ink="#22282b", navy="#1b2d6b", sred="#b8323a")
ITF = ["NNWWN", "WNNNW", "NWNNW", "WWNNN", "NNWNW", "WNWNN", "NWWNN", "NNNWW", "WNNWN", "NWNWN"]


def itf_bars(digits):
    """Interleaved 2 of 5 (what PSA prints: decoded from the photo as 43144250). Returns [(x, width)] in modules."""
    digits = digits if len(digits) % 2 == 0 else "0" + digits
    seq = "NNNN"                                     # start: bar, space, bar, space
    for a, b in zip(digits[::2], digits[1::2]):
        seq += "".join(x + y for x, y in zip(ITF[int(a)], ITF[int(b)]))
    seq += "WNN"                                     # stop: bar, space, bar
    out, x = [], 0
    for i, w in enumerate(seq):
        n = 3 if w == "W" else 1
        if i % 2 == 0:
            out.append((x, n))
        x += n
    return out


def psa_label(set_line, card_line, number, grade_word, grade, cert, spec=LABEL_SPEC, c=LABEL_COLOURS):
    e, mm = html.escape, (lambda v: f"{v * 10:.2f}px")
    w, h = spec["size"]
    pl, pt, pr, pb = spec["panel"]

    def text(key, s):
        x, top, fs, ls, align = spec[key]
        y = top - 0.1305 * fs                        # Arial cap top sits 0.1305 em below a line-height:1 box
        side = f"left:{mm(x)}" if align == "left" else f"right:{mm(w - x)}"
        return (f'<div style="position:absolute;{side};top:{mm(y)};font-size:{mm(fs)};letter-spacing:{mm(ls)};'
                f'line-height:1;white-space:pre;color:{c["ink"]}">{e(s)}</div>')

    bx, by, bh, nar = spec["bars"]
    bars = "".join(f'<i style="position:absolute;left:{mm(bx + x * nar)};top:{mm(by)};width:{mm(n * nar)};height:{mm(bh)};background:{c["ink"]}"></i>'
                   for x, n in itf_bars(cert)) if cert else ""
    lx, ly, lw, lh = spec["logo"]
    tx, ty, tfs = spec["logo_text"]
    logo = (f'<div style="position:absolute;left:{mm(lx)};top:{mm(ly)};width:{mm(lw)};height:{mm(lh)};'
            f'background:linear-gradient(160deg,#c3c7cc,#8f959c 55%,#b4b9bf);border-radius:{mm(0.25)}"></div>'
            f'<div style="position:absolute;left:{mm(tx)};top:{mm(ty - 0.1305 * tfs)};font:900 {mm(tfs)}/1 \'Arial Black\',Arial,sans-serif;'
            f'letter-spacing:{mm(-0.1)};color:{c["navy"]}">P<span style="color:{c["sred"]};font-style:italic">S</span>A</div>')
    return (f'<div class="psa-label" style="width:{mm(w)};height:{mm(h)};position:relative;background:{c["red"]};'
            f'border-radius:{mm(0.3)};font-family:{spec["font"]};font-weight:400;text-transform:uppercase" '
            f'aria-label="PSA label: {e(set_line)} {e(card_line)} {e(number)} {e(grade_word)} {e(grade)} {e(cert)}">'
            f'<div style="position:absolute;left:{mm(pl)};top:{mm(pt)};right:{mm(pr)};bottom:{mm(pb)};background:{c["panel"]}"></div>'
            + text("set", set_line) + text("card", card_line) + text("num", number) + text("grade", grade_word)
            + text("gnum", grade) + text("cert", cert) + bars + logo + '</div>')


SLAB_JS = """<script src="slab-settings.js"></script>
<script type="importmap">{"imports": {"three": "https://cdn.jsdelivr.net/npm/three@0.160.0/build/three.module.js",
  "three/addons/": "https://cdn.jsdelivr.net/npm/three@0.160.0/examples/jsm/"}}</script>
<script type="module">
// 3d/psa_slab_r04 (body + card lid + label lid) as acrylic (WebGL) over the live holo card + label (CSS3D, same camera, mm units)
import * as THREE from "three";
import { STLLoader } from "three/addons/loaders/STLLoader.js";
import { CSS3DRenderer, CSS3DObject } from "three/addons/renderers/CSS3DRenderer.js";
import { RoomEnvironment } from "three/addons/environments/RoomEnvironment.js";
const stage = document.querySelector(".stage"), LAYOUT = __LAYOUT__;
const stl = b64 => new STLLoader().parse(Uint8Array.from(atob(b64), c => c.charCodeAt(0)).buffer);
const body = stl("__BODY__"), lids = [stl("__LABEL_LID__"), stl("__CARD_LID__")];
body.computeBoundingBox();
const size = body.boundingBox.getSize(new THREE.Vector3());
stage.style.aspectRatio = `${size.x} / ${size.y}`;  // the stage takes the loaded slab's proportions
const scene = new THREE.Scene(), camera = new THREE.PerspectiveCamera(22, 80 / 135, 10, 2000);
const gl = new THREE.WebGLRenderer({ antialias: true, alpha: true }), css = new CSS3DRenderer();
gl.setPixelRatio(devicePixelRatio);
css.domElement.className = "css3d";
stage.append(css.domElement, gl.domElement);
scene.environment = new THREE.PMREMGenerator(gl).fromScene(new RoomEnvironment(), 0.04).texture;
const slab = new THREE.Group();
scene.add(slab);
const GLARE = window.SLAB_SETTINGS?.glare ?? 0.35;  // set in slab-settings.js (live, no rebuild)
const SET = window.SLAB_SETTINGS || {}, TINT = SET.tint ?? "#ffffff";
const clear = new THREE.MeshPhysicalMaterial({ color: TINT, roughness: 0.04, metalness: 0, transparent: true, opacity: SET.clearOpacity ?? 0.05,
  clearcoat: GLARE, clearcoatRoughness: 0.03, envMapIntensity: 1.2 * GLARE, depthWrite: false });
// frost texture: tileable fractal Perlin noise (32-cell period, 4 octaves) used as colour, roughness and bump map
const FROST = window.SLAB_SETTINGS?.frostNoise ?? 0.6, GRAIN = window.SLAB_SETTINGS?.frostGrain ?? 0.5;
function perlinTexture(px = 256, period = 32, octaves = 4) {
  const rnd = (i, j, p) => { const h = Math.sin(((i % p + p) % p) * 127.1 + ((j % p + p) % p) * 311.7) * 43758.5453; return (h - Math.floor(h)) * Math.PI * 2; };
  const fade = t => t * t * t * (t * (t * 6 - 15) + 10);
  const grad = (i, j, x, y, p) => { const a = rnd(i, j, p); return Math.cos(a) * (x - i) + Math.sin(a) * (y - j); };
  const noise = (x, y, p) => {
    const i = Math.floor(x), j = Math.floor(y), u = fade(x - i), v = fade(y - j);
    const a = grad(i, j, x, y, p) + u * (grad(i + 1, j, x, y, p) - grad(i, j, x, y, p));
    const b = grad(i, j + 1, x, y, p) + u * (grad(i + 1, j + 1, x, y, p) - grad(i, j + 1, x, y, p));
    return a + v * (b - a);
  };
  const c = document.createElement("canvas"); c.width = c.height = px;
  const ctx = c.getContext("2d"), img = ctx.createImageData(px, px), h = new Float32Array(px * px);
  for (let y = 0; y < px; y++) for (let x = 0; x < px; x++) {
    let n = 0, amp = 0.5, f = period / px;
    for (let o = 0; o < octaves; o++, amp *= 0.5, f *= 2) n += amp * noise(x * f, y * f, period * 2 ** o);
    const g = Math.round(255 * (1 - FROST * 0.35 * (0.5 - n)));   // bright base, darker speckle where n is low
    img.data.set([g, g, g, 255], (y * px + x) * 4); h[y * px + x] = n;
  }
  ctx.putImageData(img, 0, 0);
  // normal map from the same heights (wrapped slopes), so the grain lights up as if cut into the surface
  const cn = document.createElement("canvas"); cn.width = cn.height = px;
  const nctx = cn.getContext("2d"), nimg = nctx.createImageData(px, px), at = (x, y) => h[((y + px) % px) * px + (x + px) % px];
  for (let y = 0; y < px; y++) for (let x = 0; x < px; x++) {
    const dx = (at(x + 1, y) - at(x - 1, y)) * 6, dy = (at(x, y + 1) - at(x, y - 1)) * 6, l = Math.hypot(dx, dy, 1);
    nimg.data.set([128 - 127 * dx / l, 128 + 127 * dy / l, 128 + 127 / l, 255], (y * px + x) * 4);
  }
  nctx.putImageData(nimg, 0, 0);
  // speckle map: only the grain's peaks pass the glare, so it breaks into glitter instead of a flat sheet
  const cs = document.createElement("canvas"); cs.width = cs.height = px;
  const sctx = cs.getContext("2d"), simg = sctx.createImageData(px, px);
  for (let i = 0; i < px * px; i++) {
    const s = Math.min(1, Math.max(0, (h[i] - 0.05) / 0.25)), v = Math.round(255 * s * s);
    simg.data.set([v, v, v, 255], i * 4);
  }
  sctx.putImageData(simg, 0, 0);
  const tex = new THREE.CanvasTexture(c), normal = new THREE.CanvasTexture(cn), speckle = new THREE.CanvasTexture(cs);
  for (const t of [tex, normal, speckle]) t.wrapS = t.wrapT = THREE.RepeatWrapping;
  normal.colorSpace = speckle.colorSpace = THREE.NoColorSpace;
  return { tex, normal, speckle };
}
const DEPTH = SET.frostDepth ?? 0.6, SPARKLE = SET.frostSparkle ?? 0.5, RAINBOW = SET.frostRainbow ?? 0.3;
const { tex: frostTex, normal: frostNormal, speckle: frostSpeckle } = FROST > 0 ? perlinTexture() : {};
const frosted = new THREE.MeshPhysicalMaterial({ color: TINT, roughness: 0.55, metalness: 0, transparent: true, opacity: SET.frostOpacity ?? 0.32,
  envMapIntensity: SET.frostBrightness ?? 0.3, depthWrite: false, map: frostTex, roughnessMap: frostTex,
  normalMap: frostNormal, normalScale: new THREE.Vector2(DEPTH, DEPTH) });
// the frame inside step B above the card opening is frosted (bible photo), except the label window; the rest is clear
function split(geo, clear = LAYOUT.clear) {
  const pos = geo.attributes.position.array, nrm = geo.attributes.normal.array, out = [[], []];
  for (let i = 0; i < pos.length; i += 9) {
    const cx = (pos[i] + pos[i + 3] + pos[i + 6]) / 3, cy = (pos[i + 1] + pos[i + 4] + pos[i + 7]) / 3;
    const inside = ([x0, y0, x1, y1]) => cx > Math.min(x0, x1) && cx < Math.max(x0, x1) && cy > Math.min(y0, y1) && cy < Math.max(y0, y1);
    // front: frosted except the clear windows; outer edges (rolls + walls, outside the step): frosted; back: clear
    const nz = nrm[i + 2], outer = LAYOUT.frost && !inside(LAYOUT.frost);
    const frost = nz > 0.9 ? !clear.some(inside) : nz > -0.9 && outer;
    out[frost ? 1 : 0].push(...pos.slice(i, i + 9));
  }
  const tile = GRAIN * 32;  // mm covered by one noise tile (32 cells of GRAIN mm)
  return out.map(a => {
    const g = new THREE.BufferGeometry(); g.setAttribute("position", new THREE.Float32BufferAttribute(a, 3)); g.computeVertexNormals();
    const n = g.attributes.normal.array, uv = new Float32Array(a.length / 3 * 2);
    for (let v = 0; v < a.length / 3; v++) {  // box mapping: project each vertex on the plane facing its normal
      const ax = Math.abs(n[v * 3]), ay = Math.abs(n[v * 3 + 1]), az = Math.abs(n[v * 3 + 2]);
      const [s, q] = az >= ax && az >= ay ? [a[v * 3], a[v * 3 + 1]] : ax >= ay ? [a[v * 3 + 1], a[v * 3 + 2]] : [a[v * 3], a[v * 3 + 2]];
      uv[v * 2] = s / tile; uv[v * 2 + 1] = q / tile;
    }
    g.setAttribute("uv", new THREE.Float32BufferAttribute(uv, 2)); return g;
  });
}
const [bodyClear, bodyFrost] = split(body);
// card lid: frosted ring out to the arms' outer edges, clear window inside them (user's slab photo)
const [lidClear, lidFrost] = LAYOUT.lid_clear ? split(lids[1], LAYOUT.lid_clear) : [lids[1], new THREE.BufferGeometry()];
// label lid: frosted ring round a clear window exactly the label's size (user's slab photo)
const [labClear, labFrost] = LAYOUT.label_clear ? split(lids[0], LAYOUT.label_clear) : [lids[0], new THREE.BufferGeometry()];
slab.add(new THREE.Mesh(bodyClear, clear), new THREE.Mesh(bodyFrost, frosted), new THREE.Mesh(labClear, clear),
         new THREE.Mesh(labFrost, frosted), new THREE.Mesh(lidClear, clear), new THREE.Mesh(lidFrost, frosted));
// lighting: an additive layer (black base, so it only adds highlights + reflections) on every plastic mesh,
// glossy on clear plastic (tight reflections), rough on frost (broad, diffuse); reflections shift as the slab tilts
const sheen = rough => new THREE.MeshPhysicalMaterial({ color: 0x000000, roughness: rough, metalness: 0, envMapIntensity: 0.25,
  clearcoat: rough < 0.2 ? 1 : 0, clearcoatRoughness: 0.04, transparent: true, depthWrite: false, opacity: GLARE,
  // add colour only, keep the canvas alpha (else the canvas turns opaque over the CSS card underneath)
  blending: THREE.CustomBlending, blendSrc: THREE.SrcAlphaFactor, blendDst: THREE.OneFactor,
  blendSrcAlpha: THREE.ZeroFactor, blendDstAlpha: THREE.OneFactor });
// frost glints: a glossy, grain-normal-mapped reflection layer (optionally rainbow, like the card's holo) whose
// sparkles move across the grain as the slab tilts
const glint = sheen(0.12);
Object.assign(glint, { opacity: SPARKLE, envMapIntensity: 1.6, normalMap: frostNormal ?? null, normalScale: new THREE.Vector2(DEPTH * 2.5, DEPTH * 2.5),
  iridescence: RAINBOW, iridescenceIOR: 1.6, iridescenceThicknessRange: [200, 900] });
// frost glare: the glare setting on the frosted plastic, broken up by the grain (speckle mask + grain normals)
const frostGlare = sheen(0.15);
Object.assign(frostGlare, { envMapIntensity: 18, normalMap: frostNormal ?? null, normalScale: new THREE.Vector2(DEPTH * 2, DEPTH * 2),
  alphaMap: frostSpeckle ?? null });
// outer border (the band outside the step line, i.e. outside the frame round the card and label): its own frost glare
const frostGlareOuter = frostGlare.clone();
frostGlareOuter.opacity = SET.frostGlareOuter ?? GLARE;
const glintOuter = glint.clone();                     // ...and its own tilt glints
glintOuter.opacity = SET.frostSparkleOuter ?? SPARKLE;
function partition(geo, keep) {  // triangles whose centroid passes keep(x, y) -> [kept, rest]
  const pos = geo.attributes.position.array, uv = geo.attributes.uv?.array, out = [[[], []], [[], []]];
  for (let i = 0; i < pos.length; i += 9) {
    const k = keep((pos[i] + pos[i + 3] + pos[i + 6]) / 3, (pos[i + 1] + pos[i + 4] + pos[i + 7]) / 3) ? 0 : 1;
    out[k][0].push(...pos.slice(i, i + 9)); if (uv) out[k][1].push(...uv.slice(i / 3 * 2, i / 3 * 2 + 6));
  }
  return out.map(([p, u]) => { const g = new THREE.BufferGeometry(); g.setAttribute("position", new THREE.Float32BufferAttribute(p, 3));
    if (uv) g.setAttribute("uv", new THREE.Float32BufferAttribute(u, 2)); g.computeVertexNormals(); return g; });
}
const [fx0, fy0, fx1, fy1] = LAYOUT.frost ?? [-1e9, -1e9, 1e9, 1e9];
const outerBand = (x, y) => x < Math.min(fx0, fx1) || x > Math.max(fx0, fx1) || y < Math.min(fy0, fy1) || y > Math.max(fy0, fy1);
const sheenOf = new Map([[clear, [sheen(0.14)]], [frosted, [glint, frostGlare]]]);
for (const m of [...slab.children]) for (const s of sheenOf.get(m.material) ?? []) {
  const outerMat = m.geometry === bodyFrost && new Map([[frostGlare, frostGlareOuter], [glint, glintOuter]]).get(s);
  if (outerMat) {   // body frost: the outer band gets the *Outer settings, the rest the normal ones
    const [outer, inner] = partition(bodyFrost, outerBand);
    slab.add(new THREE.Mesh(outer, outerMat), new THREE.Mesh(inner, s));
  } else slab.add(new THREE.Mesh(m.geometry, s));
}
// frost backing: a flat, unlit colour layer under every frosted area (drawn first, so the frost, grain and glare sit on it)
const BACK = SET.frostBacking ?? {};
if ((BACK.opacity ?? 0) > 0) {
  const backing = new THREE.MeshBasicMaterial({ color: BACK.color ?? "#ffffff", transparent: true, opacity: BACK.opacity, depthWrite: false });
  for (const m of [...slab.children]) if (m.material === frosted) { const b = new THREE.Mesh(m.geometry, backing); b.renderOrder = -1; slab.add(b); }
}
// window backing: light behind the clear card window (on the well floor, under the card), so the gaps round the card's
// rounded corners don't show the page through as dark squares; the card covers the rest
{
  const WB = SET.windowBacking ?? {};
  if ((WB.opacity ?? 0) > 0 && LAYOUT.lid_clear) {
    const [wx0, wy0, wx1, wy1] = LAYOUT.lid_clear[0];   // exact window rect, just behind the card (the card's stand-in hides the rest)
    const wb = new THREE.Mesh(new THREE.PlaneGeometry(Math.abs(wx1 - wx0), Math.abs(wy1 - wy0)),
      new THREE.MeshBasicMaterial({ color: WB.color ?? "#d8d8d8", transparent: true, opacity: WB.opacity, depthWrite: false }));
    wb.position.set((wx0 + wx1) / 2, (wy0 + wy1) / 2, LAYOUT.card[2] - 0.5); wb.renderOrder = -1; slab.add(wb);
  }
}
// see-through plastic: render both sides, so the back face and far walls show through the near ones
// (three draws transparent double-sided meshes back faces first, then front)
for (const m of slab.children) if (m.isMesh) m.material.side = THREE.DoubleSide;

const dark = matchMedia("(prefers-color-scheme: dark)").matches;  // moulded lines: frame step, lid seats, well, rails, lid edges
const lines = new THREE.LineBasicMaterial({ color: dark ? 0xffffff : 0x8a94a3, transparent: true, opacity: dark ? 0.45 : 0.75 });
for (const g of [body, ...lids]) slab.add(new THREE.LineSegments(new THREE.EdgesGeometry(g, 30), lines));
for (const [sel, pos] of [[".card", LAYOUT.card], [".psa-label", LAYOUT.label]]) {
  const o = new CSS3DObject(stage.querySelector(sel));
  o.scale.setScalar(0.1);  // element px -> mm
  o.position.set(...pos);
  slab.add(o);
}
stage.classList.add("ready");
// card shadow (slab-settings cardShadow, in screen px): converted to the card element's own px (it is scaled by CSS3D)
{
  const rotEl = stage.querySelector(".card__rotator"), px = SET.cardShadow ?? 5;
  rotEl.style.setProperty("overflow", "hidden");            // clips the cropped scan to the card's rounded outline
  const k = rotEl.offsetWidth / Math.max(1, rotEl.getBoundingClientRect().width);
  rotEl.style.setProperty("box-shadow", px > 0 ? `0 ${px * 0.4 * k}px ${px * k}px rgba(0,0,0,.45)` : "none", "important");
}
// depth-only stand-ins for the card and label: the CSS layer sits under the WebGL canvas, so without these the slab's
// back face (behind the card) would paint over it now that back faces render
const occlude = new THREE.MeshBasicMaterial({ colorWrite: false });
// shaped like the element itself (its computed border-radius, elliptical), so no square corners show past a rounded card
function roundedPlane(el) {
  const w = el.offsetWidth * 0.1, h = el.offsetHeight * 0.1, r = getComputedStyle(el).borderTopLeftRadius.split(" ");
  const pct = (v, size) => (v.endsWith("%") ? parseFloat(v) / 100 * size : parseFloat(v)) * 0.1;   // element px -> mm
  const rx = Math.min(w / 2, pct(r[0], el.offsetWidth)), ry = Math.min(h / 2, pct(r[1] ?? r[0], el.offsetHeight));
  const x = w / 2, y = h / 2, pts = [], seg = 12;
  for (const [cx, cy, a0] of [[x - rx, y - ry, 0], [-x + rx, y - ry, 90], [-x + rx, -y + ry, 180], [x - rx, -y + ry, 270]])
    for (let i = 0; i <= seg; i++) { const a = (a0 + 90 * i / seg) * Math.PI / 180; pts.push(new THREE.Vector2(cx + rx * Math.cos(a), cy + ry * Math.sin(a))); }
  return new THREE.ShapeGeometry(new THREE.Shape(pts));
}
for (const [sel, shapeSel, pos] of [[".card", ".card__rotator", LAYOUT.card], [".psa-label", ".psa-label", LAYOUT.label]]) {
  const m = new THREE.Mesh(roundedPlane(stage.querySelector(shapeSel)), occlude);
  m.position.set(...pos); m.renderOrder = -10; slab.add(m);
}
const fit = () => {
  const w = stage.clientWidth, h = stage.clientHeight;
  camera.aspect = w / h;
  camera.position.z = size.y * 1.12 / (2 * Math.tan(THREE.MathUtils.degToRad(camera.fov / 2)));
  camera.updateProjectionMatrix();
  gl.setSize(w, h);
  css.setSize(w, h);
};
new ResizeObserver(fit).observe(stage);
fit();
const rad = THREE.MathUtils.degToRad;
(function loop() {  // ponytail: renders every frame; pause when idle if battery use matters
  const t = window.cardTilt;
  if (t) {
    slab.rotation.y = rad(t.rx) * 1.4; slab.rotation.x = -rad(t.ry) * 1.4;
  }
  gl.render(scene, camera);
  css.render(scene, camera);
  requestAnimationFrame(loop);
})();
</script>"""


def slab_viewer():
    b64 = lambda part: base64.b64encode(open(f"{SLAB}_{part}.stl", "rb").read()).decode()
    return (SLAB_JS.replace("__BODY__", b64("body")).replace("__LABEL_LID__", b64("label_lid")).replace("__CARD_LID__", b64("card_lid"))
            .replace("__LAYOUT__", open(SLAB + ".json").read()))


def usd(v):
    return "—" if v is None else f'<span data-usd="{v}">{fmt(v)}</span>'


def chg(v):
    if v is None:
        return '<span class="muted">—</span>'
    return f'<span class="{"up" if v >= 0 else "down"}">{"▲" if v >= 0 else "▼"} {abs(v):.1f}%</span>'


def spark(points, w=560, h=140):
    if len(points) < 2:
        return ""
    xs, ys = [p[0] for p in points], [p[1] for p in points]
    x0, x1, y0, y1 = min(xs), max(xs), min(ys), max(ys)
    sx = lambda x: 8 + (x - x0) / ((x1 - x0) or 1) * (w - 16)
    sy = lambda y: h - 18 - (y - y0) / ((y1 - y0) or 1) * (h - 36)
    d = " ".join(f"{'M' if i == 0 else 'L'}{sx(x):.1f},{sy(y):.1f}" for i, (x, y) in enumerate(points))
    first, last = datetime.fromtimestamp(x0).strftime("%b %Y"), datetime.fromtimestamp(x1).strftime("%b %Y")
    return (f'<svg viewBox="0 0 {w} {h}" role="img" aria-label="Value history {first} to {last}">'
            f'<path d="{d}" fill="none" stroke="var(--accent)" stroke-width="2" stroke-linejoin="round"/>'
            f'<circle cx="{sx(xs[-1]):.1f}" cy="{sy(ys[-1]):.1f}" r="3.5" fill="var(--accent)"/>'
            f'<text x="8" y="{h - 2}" class="axis">{first}</text><text x="{w - 8}" y="{h - 2}" class="axis" text-anchor="end">{last}</text>'
            f'<text x="8" y="12" class="axis" data-usd="{y1}">{fmt(y1)}</text><text x="8" y="{h - 20}" class="axis" data-usd="{y0}">{fmt(y0)}</text></svg>')


def render(pc, sales, bins, auctions, st, now):
    mask = foil_mask(pc["image"])
    l, t, r, b = (round(v * 100, 1) for v in ART_BOX)
    e = html.escape
    slab = CARD["grade"].startswith("PSA") and pc["image"] and os.path.exists(SLAB + "_body.stl")
    label = ""
    if slab:
        set_line, card_line, number = ((CARD.get("label") or [CARD["name"]]) + ["", ""])[:3]
        g = grade_num()
        label = psa_label(set_line, card_line, number, PSA_WORDS.get(g, ""), g, CARD.get("cert", ""))
    tiles = [("Est. value (pricecharting)", usd(st["pc_value"])), ("Median, last 10 sales", usd(st["last10"])),
             ("Median, 30 days", f'{usd(st["med30"])} <small>({st["n30"]} sales)</small>'),
             ("Median, 90 days", f'{usd(st["med90"])} <small>({st["n90"]} sales)</small>'),
             ("Lowest buy it now", usd(st["bin_low"])), ("Sales tracked", str(st["n"]))]
    sale_rows = "".join(
        f'<tr><td class="date">{s["date"]:%d %b %y}</td><td><a href="{e(s["url"])}" target="_blank" rel="noopener">{e(s["title"])}</a></td>'
        f'<td>{e(s["type"])}</td><td class="src">{s["src"]}</td><td class="num">{usd(s["price"])}</td></tr>' for s in sales[:60])
    def live_table(rows, auction):
        body = "".join(
            f'<tr><td><a href="{e(l["url"])}" target="_blank" rel="noopener">{e(l["title"])}</a></td>'
            + (f'<td>{e(l["type"])}</td><td class="date">{l["ends"].astimezone():%d %b %H:%M}</td>' if auction else "")
            + f'<td class="num">{usd(l["price"])}</td></tr>' for l in rows)
        head = "<th>Bids</th><th>Ends</th><th class=num>Current bid</th>" if auction else "<th class=num>Price</th>"
        return (f'<div class="scroll"><table><tr><th>Listing</th>{head}</tr>'
                f'{body or f"<tr><td colspan=4 class=muted>None on eBay right now</td></tr>"}</table></div>')
    return f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Card Price Tracker</title><link rel="stylesheet" href="assets/holo.css"><style>
:root{{--pointer-x:50%;--pointer-y:50%;--card-scale:1;--card-opacity:0;--translate-x:0px;--translate-y:0px;--rotate-x:0deg;--rotate-y:0deg;
--background-x:var(--pointer-x);--background-y:var(--pointer-y);--pointer-from-center:0;--pointer-from-top:var(--pointer-from-center);--pointer-from-left:var(--pointer-from-center)}}
:root{{--bg:#f6f5f2;--card:#fff;--text:#1d1d1b;--muted:#6b6b66;--line:#e4e2dc;--accent:#2f6fde;--up:#1a7f45;--down:#c2352b}}
@media (prefers-color-scheme:dark){{:root{{--bg:#151514;--card:#1f1f1d;--text:#ecebe6;--muted:#9a9993;--line:#33332f;--accent:#6c9cf0;--up:#4cc27c;--down:#f0675b}}}}
*{{box-sizing:border-box}}body{{margin:0;background:var(--bg);color:var(--text);font:15px/1.45 system-ui,-apple-system,sans-serif}}
main{{max-width:1200px;margin:0 auto;padding:24px 16px;display:grid;grid-template-columns:minmax(220px,340px) 1fr;gap:28px}}
main>*{{min-width:0}}@media (max-width:760px){{main{{grid-template-columns:1fr}}aside{{position:static}}aside .card,aside .stage{{max-width:260px}}}}
aside .card{{width:100%;margin-bottom:18px}}
.stage{{position:relative;width:100%;aspect-ratio:80/135;margin-bottom:22px;touch-action:pan-y}}.stage>canvas,.stage>.css3d{{position:absolute;inset:0}}
.stage>canvas{{pointer-events:none}}.stage:not(.ready) .psa-label{{display:none}}.stage.ready .card{{width:630px;--card-aspect:0.715909}}
.stage .card__translater,.stage .card__rotator{{transform:none!important;box-shadow:none!important}}
.card[data-era=vintage]{{--clip:inset({t}% {round(100 - r, 1)}% {round(100 - b, 1)}% {l}%);--clip-stage:var(--clip);--clip-invert:polygon(0 0,100% 0,100% 100%,0 100%,0 {b}%,{r}% {b}%,{r}% {t}%,{l}% {t}%,{l}% {b}%,0 {b}%)}}.card.masked .card__shine,.card.masked .card__shine:before,.card.masked .card__shine:after{{-webkit-mask-size:100% 100%;mask-size:100% 100%}}aside{{position:sticky;top:24px;align-self:start}}
h1{{font-size:22px;margin:0 0 4px}}.grade{{display:inline-block;background:var(--accent);color:#fff;border-radius:6px;padding:2px 8px;font-weight:600;font-size:13px}}
.muted,small{{color:var(--muted)}}section{{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:16px;margin-bottom:18px}}
h2{{font-size:14px;text-transform:uppercase;letter-spacing:.04em;color:var(--muted);margin:0 0 12px}}
.tiles{{display:grid;grid-template-columns:repeat(auto-fit,minmax(170px,1fr));gap:12px}}.tile b{{display:block;font-size:24px;font-variant-numeric:tabular-nums}}
.tile>span{{font-size:12px;color:var(--muted)}}.chg{{display:flex;gap:22px;flex-wrap:wrap;margin-bottom:10px}}.chg div span:first-child{{display:block;font-size:12px;color:var(--muted)}}
.up{{color:var(--up);font-weight:600}}.down{{color:var(--down);font-weight:600}}svg{{width:100%;height:auto}}.axis{{font-size:11px;fill:var(--muted)}}
.scroll{{overflow-x:auto}}table{{width:100%;border-collapse:collapse;font-size:13.5px}}td,th{{padding:7px 8px;border-bottom:1px solid var(--line);text-align:left;vertical-align:top}}
th{{color:var(--muted);font-weight:500}}.num{{text-align:right;font-variant-numeric:tabular-nums;white-space:nowrap}}.src{{color:var(--muted);font-size:12px}}
.cur{{display:inline-flex;margin:14px 0 0;border:1px solid var(--line);border-radius:999px;padding:3px;background:var(--card)}}.cur button{{border:0;background:none;color:var(--text);font:600 13px system-ui;padding:6px 14px;border-radius:999px;cursor:pointer}}.cur button[aria-pressed=true]{{background:var(--accent);color:#fff}}.fx{{font-size:12px;margin:6px 0 0}}a{{color:inherit}}a:hover{{color:var(--accent)}}.date{{white-space:nowrap}}
</style></head><body><main>
<aside>{'<div class="stage">' if slab else ""}{f'''<div class="card interactive{" masked" if mask else ""}" data-rarity="{foil()}" data-subtypes="basic" data-supertype="pokémon"
 data-era="{"vintage" if vintage() else "modern"}"{f' style="--mask:url({e(mask)})"' if mask else ""}><div class="card__translater"><div class="card__rotator">
 <div class="card__front" style="{scan_crop(pc["image"])}"><img src="{e(pc["image"])}" alt="{e(CARD["name"])}" width="660" height="921"><div class="card__shine"></div><div class="card__glare"></div></div>
</div></div></div>''' if pc["image"] else ""}{label + "</div>" if slab else ""}
<h1>{e(CARD["name"])}</h1><span class="grade">{e(CARD["grade"])}</span>
{f'''<div class="cur" role="group" aria-label="Currency"><button data-cur="GBP" aria-pressed="true">£ GBP</button><button data-cur="USD" aria-pressed="false">$ USD</button></div>
<p class="muted fx">$1 = £{FX["rate"]:.4f} (ECB, {FX["date"]})</p>''' if FX["rate"] else ""}
<p class="muted">Updated {now.astimezone():%d %b %Y, %H:%M}<br>Sources: <a href="{e(CARD["pricecharting"])}" target="_blank" rel="noopener">pricecharting</a>, 130point (eBay, Goldin, Fanatics…)</p></aside>
<div>
<section><h2>Value</h2><div class="tiles">{"".join(f'<div class="tile"><span>{k}</span><b>{v}</b></div>' for k, v in tiles)}</div></section>
<section><h2>Change over time</h2><div class="chg">{"".join(f'<div><span>{k}</span>{chg(v)}</div>' for k, v in st["changes"].items())}
<div><span>Sales: last 30d vs prior 30d</span>{chg(st["sales_trend"])}</div></div>{spark(pc["history"])}</section>
<section><h2>eBay buy it now — cheapest {len(bins)}</h2>{live_table(bins, False)}</section>
<section><h2>eBay auctions — ending soonest {len(auctions)}</h2>{live_table(auctions, True)}</section>
<section><h2>Recent sales ({len(sales)})</h2><div class="scroll"><table><tr><th>Date</th><th>Title</th><th>Format</th><th>Source</th><th class="num">Price</th></tr>{sale_rows}</table></div></section>
</div></main>
<script>
// card tilt + shine: vanilla port of pokemon-cards-css Card.svelte springs
(() => {{
  const card = document.querySelector(".card.interactive");
  if (!card) return;
  card.style.setProperty("--seedx", Math.random());
  card.style.setProperty("--seedy", Math.random());
  card.style.setProperty("--cosmosbg", `${{Math.floor(Math.random() * 734)}}px ${{Math.floor(Math.random() * 1280)}}px`);
  if (matchMedia("(prefers-reduced-motion: reduce)").matches) return;
  const rot = card.closest(".stage") || card.querySelector(".card__rotator"), cur = {{rx: 0, ry: 0, gx: 50, gy: 50, o: 0, bx: 50, by: 50}}, vel = {{}}, target = {{...cur}};
  for (const k in cur) vel[k] = 0;
  window.cardTilt = cur;  // the slab viewer reads the same spring
  const clamp = (v, a = 0, b = 100) => Math.min(Math.max(v, a), b), adjust = (v, a, b, c, d) => c + (d - c) * (v - a) / (b - a);
  let stiff = 0.066, damp = 0.25, raf = 0, timer;
  function tick() {{
    let moving = false;
    for (const k in cur) {{
      vel[k] += stiff * (target[k] - cur[k]) - damp * vel[k];
      cur[k] += vel[k];
      if (Math.abs(vel[k]) > 0.01 || Math.abs(target[k] - cur[k]) > 0.01) moving = true;
    }}
    const set = (k, v) => card.style.setProperty(k, v);
    set("--pointer-x", cur.gx + "%"); set("--pointer-y", cur.gy + "%");
    set("--pointer-from-center", clamp(Math.hypot(cur.gx - 50, cur.gy - 50) / 50, 0, 1));
    set("--pointer-from-top", cur.gy / 100); set("--pointer-from-left", cur.gx / 100);
    set("--card-opacity", cur.o); set("--rotate-x", cur.rx + "deg"); set("--rotate-y", cur.ry + "deg");
    set("--background-x", cur.bx + "%"); set("--background-y", cur.by + "%");
    raf = moving ? requestAnimationFrame(tick) : 0;
  }}
  const go = () => raf || (raf = requestAnimationFrame(tick));
  rot.addEventListener("pointermove", ev => {{
    clearTimeout(timer); stiff = 0.066; damp = 0.25;
    const r = rot.getBoundingClientRect(), x = clamp(100 * (ev.clientX - r.left) / r.width), y = clamp(100 * (ev.clientY - r.top) / r.height);
    Object.assign(target, {{bx: adjust(x, 0, 100, 37, 63), by: adjust(y, 0, 100, 33, 67), rx: -(x - 50) / 3.5, ry: (y - 50) / 3.5, gx: x, gy: y, o: 1}});
    card.classList.add("interacting"); go();
  }});
  rot.addEventListener("pointerleave", () => {{
    timer = setTimeout(() => {{
      stiff = 0.01; damp = 0.06;  // slow settle back, as in the original
      Object.assign(target, {{rx: 0, ry: 0, gx: 50, gy: 50, o: 0, bx: 50, by: 50}});
      card.classList.remove("interacting"); go();
    }}, 500);
  }});
}})();
const RATE = {FX["rate"] or "null"};
function setCur(c) {{
  if (!RATE) return;
  document.querySelectorAll("[data-usd]").forEach(el => {{
    const v = +el.dataset.usd * (c === "GBP" ? RATE : 1), dp = v >= 100 ? 0 : 2;
    el.textContent = (c === "GBP" ? "£" : "$") + v.toLocaleString("en-GB", {{minimumFractionDigits: dp, maximumFractionDigits: dp}});
  }});
  document.querySelectorAll("[data-cur]").forEach(b => b.setAttribute("aria-pressed", b.dataset.cur === c));
  try {{ localStorage.setItem("cur", c); }} catch (e) {{}}
}}
document.querySelectorAll("[data-cur]").forEach(b => b.onclick = () => setCur(b.dataset.cur));
try {{ const c = localStorage.getItem("cur"); if (c) setCur(c); }} catch (e) {{}}
</script>""" + (slab_viewer() if slab else "") + "</body></html>"


if __name__ == "__main__":
    build()
    os._exit(0)  # ponytail: Playwright's persistent Chrome sometimes hangs on shutdown; hard exit once the page is written
