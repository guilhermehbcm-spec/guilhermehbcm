#!/usr/bin/env python3
"""Gera um QualCID off-line em arquivo HTML único, com os dados da SIGTAP embutidos.

Uso:
    python3 build.py TabelaUnificada_202610_v2610XXXXXX.zip [CID-10-SUBCATEGORIAS.CSV] [-o qualcid-offline.html]

O ZIP é o da "Tabela Unificada" baixado em http://sigtap.datasus.gov.br (Download).
O CSV opcional (tabela CID-10 do DATASUS) adiciona classificação, excluídos e referências.
"""
import argparse
import json
import pathlib
import re
import zipfile

HERE = pathlib.Path(__file__).resolve().parent

DEFAULT_LAYOUT = {
    "tb_cid": "CO_CID,4,1,4\nNO_CID,100,5,104\nTP_AGRAVO,1,105,105\nTP_SEXO,1,106,106",
    "tb_procedimento": "CO_PROCEDIMENTO,10,1,10\nNO_PROCEDIMENTO,250,11,260\nTP_COMPLEXIDADE,1,261,261\n"
    "TP_SEXO,1,262,262\nQT_MAXIMA_EXECUCAO,4,263,266\nQT_DIAS_PERMANENCIA,4,267,270\nQT_PONTOS,4,271,274\n"
    "VL_IDADE_MINIMA,4,275,278\nVL_IDADE_MAXIMA,4,279,282",
    "rl_procedimento_cid": "CO_PROCEDIMENTO,10,1,10\nCO_CID,4,11,14\nST_PRINCIPAL,1,15,15\nDT_COMPETENCIA,6,16,21",
}


def read_zip(path):
    files = {}
    with zipfile.ZipFile(path) as z:
        for info in z.infolist():
            base = info.filename.rsplit("/", 1)[-1].lower()
            if re.fullmatch(r"(tb_cid|tb_procedimento|rl_procedimento_cid)(_layout)?\.txt", base):
                files[base] = z.read(info)
    return files


def parse_layout(txt):
    cols = {}
    for line in txt.splitlines():
        f = [s.strip() for s in line.split(",")]
        if len(f) >= 4 and f[2].isdigit():
            cols[f[0].upper()] = (int(f[2]) - 1, int(f[3]))
    return cols


def parse_table(files, name, wanted):
    if name + ".txt" not in files:
        raise SystemExit(f"Arquivo {name}.txt não encontrado no ZIP.")
    lay_bytes = files.get(name + "_layout.txt")
    lay = parse_layout(lay_bytes.decode("cp1252", "replace") if lay_bytes else DEFAULT_LAYOUT[name])
    pos = [lay.get(w) for w in wanted]
    rows = []
    for line in files[name + ".txt"].decode("cp1252", "replace").splitlines():
        if line.strip():
            rows.append([line[p[0]:p[1]].strip() if p else "" for p in pos])
    return rows


def parse_cid10_csv(path):
    lines = pathlib.Path(path).read_bytes().decode("cp1252", "replace").splitlines()
    head = [h.strip().upper() for h in lines[0].split(";")]
    ix = {h: i for i, h in enumerate(head)}
    out = {}
    for line in lines[1:]:
        if not line.strip():
            continue
        f = line.split(";")
        get = lambda k: f[ix[k]].strip() if k in ix and ix[k] < len(f) else ""
        out[get("SUBCAT")] = (get("CLASSIF"), get("REFER"), get("EXCLUIDOS"))
    return out


def build(zip_path, csv_path=None):
    files = read_zip(zip_path)
    tb_cid = parse_table(files, "tb_cid", ["CO_CID", "NO_CID", "TP_SEXO"])
    tb_proc = parse_table(files, "tb_procedimento",
                          ["CO_PROCEDIMENTO", "NO_PROCEDIMENTO", "TP_SEXO", "VL_IDADE_MINIMA", "VL_IDADE_MAXIMA", "DT_COMPETENCIA"])
    rel = parse_table(files, "rl_procedimento_cid", ["CO_PROCEDIMENTO", "CO_CID", "ST_PRINCIPAL", "DT_COMPETENCIA"])
    extra = parse_cid10_csv(csv_path) if csv_path else {}

    cids = sorted(([c, n, s, *(extra[c] if c in extra else (None, "", ""))] for c, n, s in tb_cid), key=lambda r: r[0])
    procs = sorted(([c, n, s, int(mi or 0), int(ma or 9999)] for c, n, s, mi, ma, _ in tb_proc), key=lambda r: r[0])
    ci = {c[0]: i for i, c in enumerate(cids)}
    pi = {p[0]: i for i, p in enumerate(procs)}
    comp = max((r[5] for r in tb_proc), default="")
    R = {}
    for p, c, st, dt in rel:
        if c in ci and p in pi:
            R.setdefault(str(ci[c]), []).append(pi[p] * 2 + (1 if st == "P" else 0))
            comp = max(comp, dt)
    for v in R.values():
        v.sort()
    return {"comp": comp, "cids": cids, "procs": procs, "rel": R}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("zip", help="ZIP da Tabela Unificada SIGTAP")
    ap.add_argument("csv", nargs="?", help="CID-10-SUBCATEGORIAS.CSV (opcional)")
    ap.add_argument("-o", "--out", default="qualcid-offline.html")
    a = ap.parse_args()

    data = build(a.zip, a.csv)
    payload = json.dumps(data, ensure_ascii=False, separators=(",", ":")).replace("</", "<\\/")
    html = (HERE / "index.html").read_text(encoding="utf-8")
    marker = '<script id="sigtap-data" type="application/json"></script>'
    if marker not in html:
        raise SystemExit("Marcador de dados não encontrado em index.html.")
    # Arquivo único: sem manifest/service worker (que dependem de arquivos ao lado).
    html = html.replace('<link rel="manifest" href="manifest.webmanifest">\n', "")
    html = html.replace(marker, f'<script id="sigtap-data" type="application/json">{payload}</script>')
    pathlib.Path(a.out).write_text(html, encoding="utf-8")
    n_rel = sum(len(v) for v in data["rel"].values())
    size = pathlib.Path(a.out).stat().st_size / 1e6
    print(f"OK: {a.out} ({size:.1f} MB) — competência {data['comp']}, {len(data['cids'])} CIDs, "
          f"{len(data['procs'])} procedimentos, {n_rel} vínculos.")


if __name__ == "__main__":
    main()
