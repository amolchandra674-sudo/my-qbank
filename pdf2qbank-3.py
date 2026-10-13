#!/usr/bin/env python3
"""
pdf2qbank.py - turn a question-bank PDF into an offline quiz app (index.html + img/).

Expected PDF layout, repeated per section:
  <Title>  ->  Question 1: ... a) b) c) d)  ->  Answer Key table  ->
  Detailed Explanations  ->  Solution to Question 1: ...

Setup:  pip install pdfplumber pypdfium2 pytesseract pillow   (+ install the Tesseract OCR program)
Usage:  python pdf2qbank.py book.pdf -o out --name "My QBank"
        python pdf2qbank.py book.pdf -o out --pages 1-40      (quick test on a slice)
        python pdf2qbank.py book.pdf -o out --embed           (one single .html, small PDFs only)
OCR results are cached in out/work, so you can stop and re-run to resume.
"""
import argparse, base64, hashlib, html, json, os, re
from multiprocessing import Pool, cpu_count

import pdfplumber, pypdfium2 as pdfium, pytesseract
from PIL import ImageDraw

DPI = 200
S = DPI / 72
_pl = _pd = None


def _init(pdf):
    global _pl, _pd
    _pl, _pd = pdfplumber.open(pdf), pdfium.PdfDocument(pdf)


def ocr_page(args):
    i, out = args
    cache = f"{out}/work/p{i:05d}.json"
    if os.path.exists(cache):
        return i
    items, masks, regions = [], [], []
    try:
        pg = _pl.pages[i]
        img = _pd[i].render(scale=S).to_pil().convert("RGB")
        # headings + answer-key rows are real text in the PDF, read them directly
        for ln in pg.extract_text_lines(return_chars=True):
            t = ln["text"].strip()
            ch = [c for c in ln["chars"] if c["text"].strip()]
            box = (ln["x0"], ln["top"], ln["x1"], ln["bottom"])
            if ch and all("Bold" in c["fontname"] for c in ch) and not re.fullmatch(r"[a-dA-D]\)?", t):
                items.append(dict(y=ln["top"], k="h", t=t)); masks.append(box)
            elif re.fullmatch(r"\d+\s+[a-dA-D]", t):
                items.append(dict(y=ln["top"], k="key", t=t)); masks.append(box)
        # pictures and ruled tables are saved as images (so tables stay readable)
        for im in pg.images:
            regions.append((im["x0"], im["top"], im["x1"], im["bottom"]))
        try:
            regions += [t.bbox for t in pg.find_tables()]
        except Exception:
            pass
        n = 0
        os.makedirs(f"{out}/img", exist_ok=True)
        for (x0, y0, x1, y1) in regions:
            if x1 - x0 < 40 or y1 - y0 < 20:
                continue
            crop = img.crop((int(x0 * S) - 2, int(y0 * S) - 2, int(x1 * S) + 2, int(y1 * S) + 2))
            if crop.width > 1000:
                crop = crop.resize((1000, int(crop.height * 1000 / crop.width)))
            name = f"{i + 1:05d}_{n}.jpg"; n += 1
            crop.save(f"{out}/img/{name}", quality=78, optimize=True)
            items.append(dict(y=y0, k="img", f=name)); masks.append((x0, y0, x1, y1))
        # OCR the body text with pictures/headings/tables whited out
        d = ImageDraw.Draw(img)
        for (x0, y0, x1, y1) in masks:
            d.rectangle((x0 * S - 3, y0 * S - 3, x1 * S + 3, y1 * S + 3), fill="white")
        r = pytesseract.image_to_data(img, output_type=pytesseract.Output.DICT, config="--psm 3")
        pars = {}
        for j, w in enumerate(r["text"]):
            if not w.strip() or float(r["conf"][j]) < 0:
                continue
            p = pars.setdefault((r["block_num"][j], r["par_num"][j]), dict(top=r["top"][j], lines={}))
            p["top"] = min(p["top"], r["top"][j])
            p["lines"].setdefault(r["line_num"][j], []).append(w)
        for p in pars.values():
            lines = [" ".join(ws) for _, ws in sorted(p["lines"].items())]
            if len(lines) == 1 and re.fullmatch(r"\d{1,4}", lines[0]) and p["top"] > img.height * 0.9:
                continue  # page number
            items.append(dict(y=p["top"] / S, k="p", lines=lines))
        pg.flush_cache()
    except Exception as e:
        print(f"page {i + 1}: {e}")
    json.dump(items, open(cache, "w"))
    return i


def flow(lines):
    """join wrapped lines into paragraphs, keeping bullets / numbered items on their own line"""
    out = []
    for ln in lines:
        ln = re.sub(r"^[•·¢°«*]\s*", "• ", ln)
        if out and not re.match(r"^(•|\d{1,2}\s*[-–.):]\s+[A-Za-z(])", ln):
            out[-1] += " " + ln
        else:
            out.append(ln)
    return out


def label(l):
    return re.compile(rf"(?:(?<=\s)|^)[\(\[]?[A-Za-z]?[{l}{l.upper()}][A-Za-z]?[\)\]]\s*")


def repair(q):
    """short options like 'A','B' can lose their bracket: 'B dA' -> C='B', D='A'"""
    if 0 < len(q["opts"]) < 4 and q["last"]:
        l = chr(97 + len(q["opts"]))
        txt = q["opts"][q["last"]]
        m = re.search(rf"\s[{l}{l.upper()}][\)\]]?\s*(\S{{1,3}})$", txt)
        if m and len(txt[:m.start()].strip()) <= 3:
            q["opts"][q["last"]] = txt[:m.start()].strip()
            q["opts"][l.upper()] = m[1]
            q["last"] = l.upper()


def esc(s):
    return html.escape(html.unescape(s), quote=False)


def assemble(out, pages, embed, keep_broken=False):
    secs, sec, mode, q, sol, tpos = [], None, None, None, None, (-1, 0)

    def add_text(q, t):
        t = t.strip()
        if t and q["last"]:
            q["opts"][q["last"]] = (q["opts"][q["last"]] + " " + t).strip()
        elif t:
            q["paras"][-1].append(t)

    def new(title):
        s = dict(title=title, qs={}, key={}, sol={})
        secs.append(s)
        return s

    for i in pages:
        for it in sorted(json.load(open(f"{out}/work/p{i:05d}.json")), key=lambda x: x["y"]):
            k = it["k"]
            if k == "h":
                t = it["t"]
                m = re.match(r"Question\s+(\d+)\s*:?$", t)
                s2 = re.match(r"Solution to Question\s+(\d+)", t)
                if m:
                    sec = sec or new("Untitled")
                    mode = "q"
                    q = dict(paras=[], opts={}, last=None, img=None)
                    sec["qs"][int(m[1])] = q
                elif s2:
                    sec = sec or new("Untitled")
                    mode, sol = "x", int(s2[1])
                    sec["sol"].setdefault(sol, [])
                elif t.startswith("Question No"):
                    pass
                elif re.match(r"Answer Key", t, re.I):
                    mode = "key"
                elif re.match(r"Detailed Expl", t, re.I):
                    mode, sol = "x", None
                elif mode == "t" and tpos[0] == i and it["y"] - tpos[1] < 40:
                    sec["title"] += " " + t  # title wrapped onto a second line
                    tpos = (i, it["y"])
                else:
                    sec, mode, tpos = new(t), "t", (i, it["y"])
            elif k == "key" and sec:
                n, l = it["t"].split()
                sec["key"][int(n)] = l.upper()
            elif k == "img":
                src = f"img/{it['f']}"
                if mode == "q" and q and not q["img"]:
                    q["img"] = src
                elif mode == "x" and sol is not None:
                    sec["sol"][sol].append(f'<img src="{src}">')
            elif k == "p":
                if mode == "q" and q:
                    q["paras"].append([])
                    for ln in it["lines"]:
                        pos = 0
                        while chr(97 + len(q["opts"])) <= "d":
                            m = label(chr(97 + len(q["opts"]))).search(ln, pos)
                            if not m or (not q["last"] and m.start() > 0):
                                break
                            add_text(q, ln[pos:m.start()])
                            q["last"] = chr(97 + len(q["opts"])).upper()
                            q["opts"][q["last"]] = ""
                            pos = m.end()
                        add_text(q, ln[pos:])
                elif mode == "x" and sol is not None:
                    blocks = sec["sol"][sol]
                    prev = blocks[-1] if blocks else None
                    first = it["lines"][0]
                    if isinstance(prev, list) and not first.startswith(("•", "·", "*")) and (
                            not re.search(r"[.:?!;)\]”]$", prev[-1]) or first[:1].islower()):
                        prev.extend(it["lines"])  # sentence continues (line/page break)
                    else:
                        blocks.append(list(it["lines"]))

    def src(s):
        if not embed:
            return s
        return "data:image/jpeg;base64," + base64.b64encode(open(f"{out}/{s}", "rb").read()).decode()

    def expl(blocks):
        parts = []
        for b in blocks:
            if isinstance(b, str):
                parts.append((False, re.sub(r'src="([^"]+)"', lambda m: f'src="{src(m[1])}"', b)))
            else:
                ls = flow(b)
                parts.append((ls[0].startswith("•"), "<br>".join(esc(x) for x in ls)))
        res = ""
        for n, (bul, t) in enumerate(parts):
            res += ("" if n == 0 else "<br>" if bul and parts[n - 1][0] else "<br><br>") + t
        return res

    folders, review = {}, []
    split = re.compile(r"^(.*?)\s+((?:AIIMS|NEET|INI|FMGE|JIPMER|PGI|NBE|DNB)\b.*)$", re.I)
    for s in secs:
        if not s["qs"]:
            continue  # contents pages, chapter covers, etc.
        m = split.match(s["title"].strip())
        fold, les = m.groups() if m else (s["title"], s["title"])
        qs = []
        for n in sorted(s["qs"]):
            q = s["qs"][n]
            repair(q)
            text = "<br>".join(esc(x) for para in q["paras"] if para for x in flow(para))
            ans, ex = s["key"].get(n), expl(s["sol"].get(n, []))
            probs = [p for p, bad in (("options!=4", len(q["opts"]) != 4), ("no answer", not ans),
                                      ("no explanation", not ex), ("no text", not text)) if bad]
            if ans and ans not in q["opts"]:
                probs.append("answer letter not in options")
            broken = any(p in probs for p in ("options!=4", "no answer", "answer letter not in options"))
            if probs:
                review.append(f"{s['title']} Q{n}: {', '.join(probs)}" + (" -> LEFT OUT of the app" if broken and not keep_broken else ""))
            if broken and not keep_broken:
                continue  # a question with missing options/answer would mark people wrong
            qs.append(dict(id=hashlib.sha1(f"{s['title']}|{n}".encode()).hexdigest()[:16], text=text,
                           img=src(q["img"]) if q["img"] else None, options=q["opts"], ans=ans or "A", expl=ex))
        fkey = re.sub(r"\s+", " ", fold.strip()).lower()  # "Community medicine" == "Community Medicine"
        folders.setdefault(fkey, dict(title=fold.strip(), lessons=[]))["lessons"].append(dict(title=les, questions=qs))
    data = list(folders.values())
    open(f"{out}/review.txt", "w").write("\n".join(review) or "No problems detected.")
    return data, review


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("pdf"); ap.add_argument("-o", "--out", default="out")
    ap.add_argument("--name", default="MCQ Bank"); ap.add_argument("--pages", help="e.g. 1-40")
    ap.add_argument("--workers", type=int, default=cpu_count()); ap.add_argument("--embed", action="store_true")
    ap.add_argument("--keep-broken", action="store_true", help="keep questions whose options/answer could not be read")
    ap.add_argument("--template", default=os.path.join(os.path.dirname(os.path.abspath(__file__)), "template.html"))
    a = ap.parse_args()
    os.makedirs(f"{a.out}/work", exist_ok=True)
    total = len(pdfium.PdfDocument(a.pdf))
    lo, hi = (map(int, a.pages.split("-")) if a.pages else (1, total))
    pages = list(range(lo - 1, min(hi, total)))
    with Pool(a.workers, _init, (a.pdf,)) as pool:
        for n, _ in enumerate(pool.imap_unordered(ocr_page, [(i, a.out) for i in pages]), 1):
            if n % 25 == 0 or n == len(pages):
                print(f"OCR {n}/{len(pages)} pages", flush=True)
    data, review = assemble(a.out, pages, a.embed, a.keep_broken)
    js = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")
    page = open(a.template, encoding="utf-8").read().replace("/*APP_DATA*/[]", js).replace("/*NAME*/", a.name)
    open(f"{a.out}/index.html", "w", encoding="utf-8").write(page)
    nq = sum(len(l["questions"]) for f in data for l in f["lessons"])
    print(f"Done: {nq} questions -> {a.out}/index.html ; {len(review)} flagged in {a.out}/review.txt")


if __name__ == "__main__":
    main()