#!/usr/bin/env python3
"""Converte fórmulas HYPERLINK em hyperlinks nativos do XLSX.

O cálculo interno do gerador não renderiza HYPERLINK, embora o Excel aceite a
fórmula. Este pós-processamento usa hyperlinks nativos para preservar uma
pré-visualização limpa e links clicáveis.
"""

from __future__ import annotations

import json
from pathlib import Path

from openpyxl import load_workbook
from openpyxl.workbook.properties import CalcProperties


ROOT = Path(__file__).resolve().parents[1]
PATH = ROOT / "outputs" / "leads_londrina.xlsx"
DATA = json.loads((ROOT / "data" / "leads_londrina.json").read_text(encoding="utf-8"))


def link(cell, url: str | None, label: str) -> None:
    cell.value = label if url else ""
    if url:
        cell.hyperlink = url
        cell.style = "Hyperlink"


wb = load_workbook(PATH)
all_ws = wb["Todos os Leads"]
for row, lead in enumerate(DATA, start=5):
    link(all_ws[f"K{row}"], lead.get("maps_url"), "Abrir mapa")
    link(all_ws[f"N{row}"], lead.get("website"), "Abrir site")
    link(all_ws[f"S{row}"], lead.get("instagram"), "Instagram")
    link(all_ws[f"T{row}"], lead.get("facebook"), "Facebook")
    for col, idx in zip(("AF", "AG", "AH"), range(3)):
        sources = lead.get("sources") or []
        link(all_ws[f"{col}{row}"], sources[idx] if idx < len(sources) else None, f"Fonte {idx + 1}")

prioritized = sorted((x for x in DATA if x["score"] >= 60), key=lambda x: (-x["score"], x["name"]))
p_ws = wb["Leads Prioritários"]
for row, lead in enumerate(prioritized, start=5):
    link(p_ws[f"F{row}"], lead.get("website"), "Abrir site")
    link(p_ws[f"G{row}"], lead.get("instagram"), "Instagram")
    link(p_ws[f"M{row}"], lead.get("maps_url"), "Abrir mapa")
    sources = lead.get("sources") or []
    link(p_ws[f"O{row}"], sources[0] if sources else None, "Fonte")

wb.calculation = CalcProperties(calcMode="auto", fullCalcOnLoad=True, forceFullCalc=True)
wb.save(PATH)
print(PATH)
