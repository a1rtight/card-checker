"""Track one card's market: pricecharting (value + history + sales) and 130point (sales + live listings) -> index.html"""
import html, json, os, re, statistics, sys, urllib.parse, urllib.request
from datetime import datetime, timedelta, timezone

CARD = {
    "name": "Mew #151 Holo — Japanese Fossil (1997)",
    "grade": "PSA 9",
    "pricecharting": "https://www.pricecharting.com/game/pokemon-japanese-mystery-of-the-fossils/mew-151",
    "query": "fossil mew psa 9 japanese",          # 130point search
    "must": [r"\bmew\b", r"japan|\bjp\b|jpn", r"fossil"],  # every title must match all of these
}
# pricecharting reuses video-game field names for card grades
PC_GRADE = {"ungraded": ("used", "used"), "7": ("cib", "cib"), "8": ("new", "new"),
            "9": ("graded", "graded"), "9.5": ("boxonly", "box-only"), "10": ("manualonly", "manual-only")}
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0 Safari/537.36"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "index.html")
PROFILE = os.path.expanduser("~/.venvs/card-checker/profile")
FX = {"rate": None, "date": ""}  # USD -> GBP, filled per run


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
    e = html.escape
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
<title>Card Price Tracker</title><style>
:root{{--bg:#f6f5f2;--card:#fff;--text:#1d1d1b;--muted:#6b6b66;--line:#e4e2dc;--accent:#2f6fde;--up:#1a7f45;--down:#c2352b}}
@media (prefers-color-scheme:dark){{:root{{--bg:#151514;--card:#1f1f1d;--text:#ecebe6;--muted:#9a9993;--line:#33332f;--accent:#6c9cf0;--up:#4cc27c;--down:#f0675b}}}}
*{{box-sizing:border-box}}body{{margin:0;background:var(--bg);color:var(--text);font:15px/1.45 system-ui,-apple-system,sans-serif}}
main{{max-width:1200px;margin:0 auto;padding:24px 16px;display:grid;grid-template-columns:minmax(220px,340px) 1fr;gap:28px}}
main>*{{min-width:0}}@media (max-width:760px){{main{{grid-template-columns:1fr}}aside{{position:static}}aside img{{max-width:260px}}}}
aside img{{width:100%;border-radius:12px;display:block;background:var(--card)}}aside{{position:sticky;top:24px;align-self:start}}
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
<aside>{f'<img src="{e(pc["image"] or "")}" alt="{e(CARD["name"])}">' if pc["image"] else ""}
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
</script></body></html>"""


if __name__ == "__main__":
    build()
    os._exit(0)  # ponytail: Playwright's persistent Chrome sometimes hangs on shutdown; hard exit once the page is written
