# Coletor de dados da B3 (Fundamentus) para o Motor de Dividendos B3.
# Roda no GitHub Actions e grava CSVs em data/ (separador ";" e decimal ",", padrão pt-BR).
import html as htmlmod, os, re, sys, time, datetime as dt
from concurrent.futures import ThreadPoolExecutor
import requests

H = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36",
     "Accept-Language": "pt-BR,pt;q=0.9"}
BASE = "https://www.fundamentus.com.br/"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "data")
os.makedirs(OUT, exist_ok=True)
S = requests.Session(); S.headers.update(H)
TAG = re.compile(r"<[^>]+>")

def get(url, tries=3):
    for i in range(tries):
        try:
            r = S.get(url, timeout=30)
            if r.status_code == 200:
                return r.content.decode("latin-1")
        except Exception:
            pass
        time.sleep(2 + 3 * i)
    return None

def clean(s):
    return re.sub(r"\s+", " ", htmlmod.unescape(TAG.sub("", s))).strip()

def table(h, n=0):
    """Linhas (lista de células em texto) da n-ésima <table> da página."""
    tabs = re.findall(r"<table.*?</table>", h, flags=re.S | re.I)
    if len(tabs) <= n:
        return [], []
    t = tabs[n]
    head = [clean(x) for x in re.findall(r"<th[^>]*>(.*?)</th>", t, flags=re.S | re.I)]
    rows = []
    for tr in re.findall(r"<tr[^>]*>(.*?)</tr>", t, flags=re.S | re.I):
        cells = [clean(x) for x in re.findall(r"<td[^>]*>(.*?)</td>", tr, flags=re.S | re.I)]
        if cells:
            rows.append(cells)
    return head, rows

def num(s):
    """'6,50%' -> 0.065 ; '2.608.290.000,00' -> 2608290000.0 ; '-0,96' -> -0.96"""
    s = (s or "").strip()
    if s in ("", "-"):
        return None
    pct = s.endswith("%")
    s = s.rstrip("%").replace(".", "").replace(",", ".")
    try:
        x = float(s)
    except ValueError:
        return None
    return x / 100 if pct else x

def br(x, dec=8):
    if x is None:
        return ""
    s = f"{x:.{dec}f}".rstrip("0").rstrip(".")
    return s.replace(".", ",")

def write(name, header, rows):
    with open(os.path.join(OUT, name), "w", encoding="utf-8", newline="") as f:
        f.write(";".join(header) + "\n")
        for r in rows:
            f.write(";".join("" if c is None else str(c).replace(";", ",") for c in r) + "\n")
    print(name, len(rows), "linhas")

# 1) Mercado: indicadores de todas as ações
page = get(BASE + "resultado.php")
if not page:
    sys.exit("Falha ao baixar resultado.php")
head, rows = table(page)
rows = [r for r in rows if len(r) == len(head)]
if len(rows) < 300:
    sys.exit("Poucas linhas em resultado.php, abortando para não sobrescrever dados bons")
merc = [[r[0]] + [br(num(v)) for v in r[1:]] for r in rows]
write("mercado.csv", head, merc)

# 2) Universo para proventos e setores: ações com cotação e DY > 0
uni = [r[0] for r in rows if (num(r[1]) or 0) > 0 and (num(r[5]) or 0) > 0]
print("universo", len(uni))
limite = dt.date(dt.date.today().year - 7, 1, 1)

def proventos(t):
    h = get(f"{BASE}proventos.php?papel={t}&tipo=2")
    if not h:
        return []
    _, rs = table(h)
    out = []
    for r in rs:
        if len(r) < 5:
            continue
        try:
            d = dt.datetime.strptime(r[0], "%d/%m/%Y").date()
        except ValueError:
            continue
        if d < limite:
            continue
        pag = r[3] if re.match(r"^\d{2}/\d{2}/\d{4}$", r[3]) else ""
        q = int(num(r[4]) or 1)
        out.append([t, r[0], br(num(r[1])), r[2], pag, q])
    return out

def setor(t):
    h = get(f"{BASE}detalhes.php?papel={t}")
    d = {}
    if h:
        _, rs = table(h)
        for r in rs:
            for i in range(0, len(r) - 1, 2):
                d[r[i].lstrip("?").strip()] = r[i + 1]
    return [t, d.get("Empresa", ""), d.get("Setor", ""), d.get("Subsetor", "")]

with ThreadPoolExecutor(6) as ex:
    prov = list(ex.map(proventos, uni))
    sets = list(ex.map(setor, uni))
prow = [r for lst in prov for r in lst]
prow.sort(key=lambda r: (r[0], dt.datetime.strptime(r[1], "%d/%m/%Y")))
if len(prow) < 500:
    sys.exit("Poucos proventos, abortando para não sobrescrever dados bons")
write("proventos.csv", ["Ticker", "Data-com", "Valor bruto", "Tipo", "Pagamento", "Por ações"], prow)
write("setores.csv", ["Ticker", "Empresa", "Setor", "Subsetor"], sets)
agora = dt.datetime.now(dt.timezone.utc) - dt.timedelta(hours=3)
write("meta.csv", ["Atualizado em", "Ações", "Proventos"], [[agora.strftime("%d/%m/%Y %H:%M"), len(merc), len(prow)]])
