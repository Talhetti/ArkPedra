#!/usr/bin/env python3
"""Coleta e normaliza leads públicos de Londrina/PR.

O script usa páginas públicas de diretórios, com requisições sequenciais e
limitadas. Ele não contorna CAPTCHA, autenticação ou bloqueios. Os arquivos
brutos são preservados em data/raw para auditoria.
"""

from __future__ import annotations

import argparse
import hashlib
import html
import json
import re
import subprocess
import time
import unicodedata
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from urllib.parse import quote_plus, urljoin, urlparse


ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = ROOT / "data" / "raw"
DATA_DIR = ROOT / "data"
VERIFY_DATE = date.today().isoformat()


@dataclass(frozen=True)
class Source:
    niche: str
    url: str
    filename: str


SOURCES = [
    Source("Marmorarias", "https://www.encontralondrina.com.br/m/marmoraria-em-londrina.shtml", "marmorarias_encontra.html"),
    Source("Vidraçarias", "https://www.encontralondrina.com.br/v/vidracaria-em-londrina.shtml", "vidracarias_encontra.html"),
    Source("Marcenarias e móveis planejados", "https://www.encontralondrina.com.br/m/marceneiro-em-londrina.shtml", "marcenarias_encontra.html"),
    Source("Oficinas mecânicas", "https://www.encontralondrina.com.br/o/oficina-mecanica-em-londrina.shtml", "oficinas_encontra.html"),
    Source("Serralherias", "https://www.encontralondrina.com.br/s/serralheria-em-londrina.shtml", "serralherias_encontra.html"),
]

MARBLE_LIST_URL = "https://marmorebrasil.com.br/londrina/"

# Verificações complementares feitas em 18/10/2026. O valor "NÃO" para site
# só é usado quando o perfil setorial não informa domínio próprio e uma busca
# exata pelo nome/cidade não encontrou domínio da empresa. A justificativa e a
# URL de apoio ficam registradas no lead para revisão posterior.
MANUAL_VERIFICATIONS = {
    "Império do Mármore": {
        "website": "http://www.imperiodomarmore.com.br/",
        "site_status": "SIM",
        "source": "https://www.yellowpages.net/phone-55-4333374545-marble-supplier-Londrina-BREN108430.html",
        "note": "Domínio localizado em diretório empresarial; disponibilidade técnica testada separadamente.",
    },
    "Loja do Mármore": {
        "website": "http://lojadomarmorelondrina.com.br/",
        "site_status": "SIM",
        "source": "https://www.guiaking.com.br/empresa/loja%2Bdo%2Bmarmore_londrina_pr_597705.html",
        "note": "Domínio localizado em diretório empresarial; disponibilidade técnica testada separadamente.",
    },
    "Marmoraria Siena - Marmoraria em Londrina": {
        "site_status": "NÃO",
        "whatsapp_status": "SIM",
        "whatsapp": "(43) 98405-7320",
        "source": "https://www.econodata.com.br/consulta-empresa/39381430000136-edson-e-isabelle-marmoraria-ltda",
        "note": "Somente Instagram e WhatsApp foram encontrados no perfil setorial, no cadastro empresarial e na busca exata; nenhum domínio próprio foi localizado.",
    },
    "MARMORARIA ELEGANCE": {
        "site_status": "NÃO",
        "source": "https://marmorebrasil.com.br/londrina/marmoraria-elegance/",
        "note": "O perfil setorial não informa site e a busca exata pelo nome em Londrina não retornou domínio próprio.",
    },
    "Graniart Marmoraria": {
        "site_status": "NÃO",
        "source": "https://www.econodata.com.br/consulta-empresa/07655559000107-grepacol-comercio-de-produtos-decorativos-ltda",
        "note": "O domínio homônimo encontrado pertence a Camboriú/SC; para a empresa de Londrina, perfis públicos e busca exata não indicaram domínio próprio.",
    },
    "Marmoraria Classe A": {
        "site_status": "NÃO",
        "whatsapp_status": "SIM",
        "whatsapp": "(43) 99995-1781",
        "source": "https://casadosdados.com.br/solucao/cnpj/marmoraria-classe-a-ltda-45614980000150",
        "note": "Cadastro público e busca exata indicaram WhatsApp, mas nenhum domínio próprio.",
    },
    "Marmoraria Revestindo Londrina": {
        "site_status": "NÃO",
        "instagram": "https://www.instagram.com/revestindolondrina1/",
        "source": "https://br.linkedin.com/in/camila-pinheiro-286121293",
        "note": "Perfis públicos e busca exata indicaram presença social, mas nenhum domínio próprio.",
    },
}


def slugify(value: str) -> str:
    value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode()
    value = re.sub(r"[^a-zA-Z0-9]+", "-", value).strip("-").lower()
    return value


def fetch(url: str, dest: Path, refresh: bool) -> str:
    dest.parent.mkdir(parents=True, exist_ok=True)
    if dest.exists() and not refresh:
        return dest.read_text(encoding="utf-8", errors="replace")
    cmd = [
        "curl", "-L", "--fail", "--silent", "--show-error", "--max-time", "30",
        "-A", "Mozilla/5.0 (compatible; PesquisaComercialLondrina/1.0)", url,
    ]
    result = subprocess.run(cmd, check=True, capture_output=True)
    text = result.stdout.decode("utf-8", errors="replace")
    dest.write_text(text, encoding="utf-8")
    return text


def strip_tags(fragment: str) -> str:
    fragment = re.sub(r"<br\s*/?>", "\n", fragment, flags=re.I)
    fragment = re.sub(r"<[^>]+>", " ", fragment)
    fragment = html.unescape(fragment).replace("\xa0", " ")
    lines = [re.sub(r"\s+", " ", x).strip(" -") for x in fragment.splitlines()]
    return "\n".join(x for x in lines if x)


def block_to_records(page: str) -> list[dict]:
    # Cada empresa começa por um span style4. Alguns anúncios têm mais de um
    # registro dentro do mesmo <p>, por isso o corte é feito pelo próximo span.
    page = re.sub(r'<span\s+class=["\']style4["\'][^>]*>\s*</span>', '', page, flags=re.I)
    pattern = re.compile(
        r'<span\s+class=["\']style4["\'][^>]*>(.*?)</span>(.*?)(?=<span\s+class=["\']style4["\']|</p>)',
        re.I | re.S,
    )
    records = []
    for name_html, body_html in pattern.findall(page):
        name = strip_tags(name_html).strip()
        body = strip_tags(body_html)
        if not name or len(name) < 3:
            continue
        phone_match = re.search(r"\(?43\)?\s*\d{4,5}[-\s]?\d{4}", body)
        phone = phone_match.group(0).strip() if phone_match else ""
        site_match = re.search(r"(?:Site|Website)\s*:\s*(https?://\S+|www\.\S+)", body, re.I)
        facebook_match = re.search(r"Facebook\s*:\s*@?([\w.\-/]+)", body, re.I)
        instagram_match = re.search(r"Instagram\s*:\s*@?([\w.\-/]+)", body, re.I)
        # Endereço: use a linha que contém Londrina, juntando a anterior quando
        # ela termina antes do campo Bairro.
        body_lines = [x for x in body.splitlines() if x]
        address = ""
        for idx, line in enumerate(body_lines):
            if "Londrina" in line and ("Rua " in line or "Avenida " in line or "Rodovia " in line or "Bairro:" in line):
                address = line
                if line.startswith("Bairro:") and idx:
                    address = f"{body_lines[idx-1]} - {line}"
                break
        if not address:
            joined = " ".join(body_lines)
            addr_match = re.search(r"((?:Rua|Avenida|Rodovia|Travessa|Alameda)\s+.+?Londrina\s*-\s*(?:PR|Parque))", joined, re.I)
            address = addr_match.group(1).strip() if addr_match else ""
        bairro_match = re.search(r"Bairro\s*:\s*([^\n-]+)", body, re.I)
        bairro = bairro_match.group(1).strip() if bairro_match else "NÃO IDENTIFICADO"
        if not phone or not address:
            # Mantém somente registros com ao menos nome, telefone e endereço,
            # reduzindo o risco de misturar textos promocionais com empresas.
            continue
        website = site_match.group(1).rstrip(".,)") if site_match else ""
        if website and website.startswith("www."):
            website = "https://" + website
        facebook = ""
        if facebook_match:
            fb = facebook_match.group(1).rstrip(".,)")
            facebook = fb if fb.startswith("http") else "https://facebook.com/" + fb.lstrip("@/")
        instagram = ""
        if instagram_match:
            ig = instagram_match.group(1).rstrip(".,)")
            instagram = ig if ig.startswith("http") else "https://instagram.com/" + ig.lstrip("@/")
        records.append({
            "name": name,
            "address": address,
            "bairro": bairro,
            "phone": phone,
            "website": website,
            "instagram": instagram,
            "facebook": facebook,
            "whatsapp_confirmed": "fa-whatsapp" in body_html.lower() or "whatsapp" in body.lower(),
            "raw_text": body,
        })
    return records


def load_marble_details(refresh: bool, max_items: int = 29) -> list[dict]:
    list_html = fetch(MARBLE_LIST_URL, RAW_DIR / "marmorebrasil_londrina.html", refresh)
    list_match = re.search(r'<script type="application/ld\+json">(\{"@context":"https://schema.org","@type":"ItemList".*?\})</script>', list_html, re.S)
    if not list_match:
        return []
    listing = json.loads(list_match.group(1))
    details = []
    for item in listing.get("itemListElement", [])[:max_items]:
        url = item.get("url", "")
        if not url:
            continue
        path = RAW_DIR / "marmorarias" / f"{slugify(item.get('name', 'empresa'))}.html"
        page = fetch(url, path, refresh)
        matches = re.findall(r'<script type="application/ld\+json">(.*?)</script>', page, re.S)
        business = None
        for raw in matches:
            try:
                obj = json.loads(raw)
            except json.JSONDecodeError:
                continue
            if obj.get("@type") == "LocalBusiness":
                business = obj
                break
        if not business:
            continue
        details.append({**business, "detail_source": url})
        if refresh:
            time.sleep(0.25)
    return details


def normalize_phone(phone: str) -> str:
    digits = re.sub(r"\D", "", phone)
    if len(digits) == 11 and digits.startswith("043"):
        digits = digits[1:]
    if len(digits) == 10:
        return f"({digits[:2]}) {digits[2:6]}-{digits[6:]}"
    if len(digits) == 11:
        return f"({digits[:2]}) {digits[2:7]}-{digits[7:]}"
    if len(digits) == 12 and digits.startswith("043"):
        digits = digits[1:]
        return f"({digits[:2]}) {digits[2:7]}-{digits[7:]}"
    return phone.strip()


def domain_kind(url: str) -> str:
    host = urlparse(url).netloc.lower().removeprefix("www.")
    if "instagram.com" in host or "instagran.com" in host:
        return "instagram"
    if "facebook.com" in host:
        return "facebook"
    if host:
        return "website"
    return ""


def services_for(niche: str) -> str:
    return {
        "Marmorarias": "Mármores, granitos, bancadas, pias e revestimentos (categoria pública; confirmar escopo diretamente).",
        "Vidraçarias": "Vidros, espelhos, boxes e esquadrias (categoria pública; confirmar escopo diretamente).",
        "Marcenarias e móveis planejados": "Marcenaria e móveis sob medida/planejados (categoria pública; confirmar escopo diretamente).",
        "Oficinas mecânicas": "Manutenção e reparação automotiva (categoria pública; confirmar especialidades diretamente).",
        "Serralherias": "Serralheria e estruturas metálicas (categoria pública; confirmar escopo diretamente).",
    }[niche]


def build_opportunity(lead: dict) -> tuple[str, str, str]:
    hypotheses = []
    solutions = []
    if lead["site_status"] == "NÃO":
        hypotheses.append("Ausência de domínio próprio confirmada nas verificações registradas.")
        solutions.append("Site institucional com portfólio e integração ao WhatsApp.")
    elif lead["site_status"] == "NÃO IDENTIFICADO":
        hypotheses.append("Domínio próprio não identificado; confirmar antes da abordagem.")
        solutions.append("Se confirmado, landing page/site institucional com portfólio.")
    if lead["catalog_status"] in ("NÃO", "NÃO IDENTIFICADO"):
        hypotheses.append("Catálogo digital não identificado; ausência não confirmada.")
        solutions.append("Catálogo visual com pedido de orçamento.")
    hypotheses.append("A captação pública encontrada privilegia telefone/diretório; há potencial de simplificar pedidos de orçamento.")
    solutions.append("Formulário qualificado e integração com WhatsApp/CRM.")
    if lead["niche"] == "Oficinas mecânicas":
        hypotheses.append("Agendamento online não identificado; ausência não confirmada.")
        solutions.append("Agenda digital com lembretes e pré-triagem do veículo.")
    approach = (
        f"Apresentar um protótipo curto para {lead['niche'].lower()}, destacar portfólio e orçamento no celular, "
        "e pedir confirmação do processo atual antes de afirmar qualquer problema interno."
    )
    return " ".join(hypotheses), " ".join(solutions), approach


def score_lead(lead: dict) -> tuple[int, str]:
    parts = []
    score = 0
    if lead["site_status"] == "NÃO":
        score += 25; parts.append("25 site próprio ausente (confirmado)")
    else:
        parts.append("0 ausência de site não confirmada")
    if lead["catalog_status"] == "NÃO":
        score += 15; parts.append("15 catálogo ausente (confirmado)")
    else:
        parts.append("0 ausência de catálogo não confirmada")
    # A fonte pública mostra telefone/diretório como rota de contato. É uma
    # oportunidade observável, mas recebe pontuação parcial porque o processo
    # interno não foi investigado.
    score += 8; parts.append("8 captação pública concentrada em contato direto")
    if lead["niche"] == "Oficinas mecânicas" and lead["appointment_status"] == "NÃO":
        score += 10; parts.append("10 agendamento online ausente (confirmado)")
    elif lead["niche"] == "Oficinas mecânicas":
        parts.append("0 ausência de agendamento não confirmada")
    reviews = lead.get("review_count") or 0
    rating = lead.get("rating") or 0
    if reviews >= 30 and rating >= 4:
        score += 15; parts.append("15 atividade/reputação pública forte")
    elif reviews >= 10:
        score += 12; parts.append("12 atividade/reputação pública moderada")
    elif reviews > 0:
        score += 8; parts.append("8 reputação pública identificada")
    else:
        score += 5; parts.append("5 listagem pública com contato e endereço")
    score += 10; parts.append("10 protótipo reaproveitável no nicho")
    if lead.get("phone") and lead.get("address"):
        score += 10; parts.append("10 telefone e endereço públicos verificados na fonte")
    elif lead.get("phone"):
        score += 7; parts.append("7 telefone público verificado")
    return min(score, 100), "; ".join(parts)


def priority(score: int) -> str:
    if score >= 80: return "Prioridade A — Muito alta"
    if score >= 60: return "Prioridade B — Alta"
    if score >= 40: return "Prioridade C — Média"
    return "Prioridade D — Baixa"


def make_lead(record: dict, source: Source) -> dict:
    name = record["name"].strip()
    map_url = "https://www.google.com/maps/search/?api=1&query=" + quote_plus(f"{name} {record['address']}")
    lead = {
        "id": hashlib.sha1(f"{name}|{record['address']}".encode()).hexdigest()[:12],
        "name": name,
        "niche": source.niche,
        "address": record["address"],
        "bairro": record["bairro"],
        "city": "Londrina",
        "state": "PR",
        "phone": normalize_phone(record["phone"]),
        "whatsapp_status": "SIM" if record.get("whatsapp_confirmed") else "NÃO IDENTIFICADO",
        "whatsapp": normalize_phone(record["phone"]) if record.get("whatsapp_confirmed") else "",
        "maps_url": map_url,
        "rating": None,
        "review_count": None,
        "website": record.get("website", ""),
        "instagram": record.get("instagram", ""),
        "facebook": record.get("facebook", ""),
        "site_status": "SIM" if record.get("website") else "NÃO IDENTIFICADO",
        "ecommerce_status": "NÃO IDENTIFICADO",
        "catalog_status": "NÃO IDENTIFICADO",
        "appointment_status": "NÃO IDENTIFICADO",
        "services": services_for(source.niche),
        "sources": [source.url],
        "verified_at": VERIFY_DATE,
        "observed_facts": "Nome, endereço e telefone publicados no diretório indicado em Fontes.",
        "commercial_status": "não contatado",
        "commercial_notes": "",
    }
    opp, solutions, approach = build_opportunity(lead)
    lead["opportunities"] = opp
    lead["recommended_solutions"] = solutions
    lead["suggested_approach"] = approach
    lead["score"], lead["score_justification"] = score_lead(lead)
    lead["priority"] = priority(lead["score"])
    return lead


def make_marble_lead(detail: dict) -> dict:
    name = detail.get("name", "").strip()
    address = detail.get("address", {}).get("streetAddress", "")
    bairro = "NÃO IDENTIFICADO"
    bairro_match = re.search(r"\s-\s([^,]+),\s*Londrina\s*-\s*PR", address, re.I)
    if bairro_match:
        bairro = bairro_match.group(1).strip()
    same_as = detail.get("sameAs", "")
    kind = domain_kind(same_as)
    website = same_as if kind == "website" else ""
    instagram = same_as if kind == "instagram" else ""
    facebook = same_as if kind == "facebook" else ""
    rating = detail.get("aggregateRating", {})
    lead = {
        "id": hashlib.sha1(f"{name}|{address}".encode()).hexdigest()[:12],
        "name": name,
        "niche": "Marmorarias",
        "address": address,
        "bairro": bairro,
        "city": detail.get("address", {}).get("addressLocality", "Londrina"),
        "state": "PR",
        "phone": normalize_phone(str(detail.get("telephone", ""))),
        "whatsapp_status": "NÃO IDENTIFICADO",
        "whatsapp": "",
        "maps_url": "https://www.google.com/maps/search/?api=1&query=" + quote_plus(f"{name} {address}"),
        "rating": rating.get("ratingValue"),
        "review_count": rating.get("reviewCount"),
        "website": website,
        "instagram": instagram,
        "facebook": facebook,
        "site_status": "SIM" if website else "NÃO IDENTIFICADO",
        "ecommerce_status": "NÃO IDENTIFICADO",
        "catalog_status": "NÃO IDENTIFICADO",
        "appointment_status": "NÃO IDENTIFICADO",
        "services": services_for("Marmorarias"),
        "sources": [MARBLE_LIST_URL, detail["detail_source"]],
        "verified_at": VERIFY_DATE,
        "observed_facts": "Nome, endereço, telefone, localização e nota/avaliações publicadas como dados do Google na fonte setorial.",
        "commercial_status": "não contatado",
        "commercial_notes": "",
        "latitude": detail.get("geo", {}).get("latitude"),
        "longitude": detail.get("geo", {}).get("longitude"),
    }
    opp, solutions, approach = build_opportunity(lead)
    lead["opportunities"], lead["recommended_solutions"], lead["suggested_approach"] = opp, solutions, approach
    lead["score"], lead["score_justification"] = score_lead(lead)
    lead["priority"] = priority(lead["score"])
    return lead


def apply_manual_verifications(leads: list[dict]) -> None:
    for lead in leads:
        override = MANUAL_VERIFICATIONS.get(lead["name"])
        if not override:
            continue
        for field in ("website", "site_status", "whatsapp_status", "whatsapp", "instagram", "facebook"):
            if field in override:
                lead[field] = override[field]
        lead["sources"].append(override["source"])
        lead["site_verification_note"] = override["note"]
        opp, solutions, approach = build_opportunity(lead)
        lead["opportunities"], lead["recommended_solutions"], lead["suggested_approach"] = opp, solutions, approach
        lead["score"], lead["score_justification"] = score_lead(lead)
        lead["priority"] = priority(lead["score"])


def technical_site_check(lead: dict) -> None:
    url = lead.get("website", "")
    if not url:
        lead["site_check_result"] = "NÃO APLICÁVEL"
        lead["site_http_status"] = None
        return
    cmd = [
        "curl", "-L", "--silent", "--show-error", "--max-time", "12",
        "-A", "Mozilla/5.0 (compatible; PesquisaComercialLondrina/1.0)",
        "-o", "/dev/null", "-w", "%{http_code}", url,
    ]
    try:
        result = subprocess.run(cmd, capture_output=True, timeout=15)
        status_text = result.stdout.decode(errors="replace").strip()
        status = int(status_text) if status_text.isdigit() else 0
        lead["site_http_status"] = status or None
        lead["site_check_result"] = "ACESSÍVEL" if 200 <= status < 400 else "INDISPONÍVEL NA VERIFICAÇÃO"
    except (subprocess.TimeoutExpired, ValueError):
        lead["site_http_status"] = None
        lead["site_check_result"] = "INDISPONÍVEL NA VERIFICAÇÃO"


def set_presence_status(lead: dict) -> None:
    if lead["site_status"] == "NÃO":
        lead["presence_status"] = "SEM SITE CONFIRMADO"
    elif lead["site_status"] == "SIM" and lead.get("site_check_result") != "ACESSÍVEL":
        lead["presence_status"] = "INCOMPLETA"
    elif lead["site_status"] == "SIM":
        lead["presence_status"] = "SITE CONFIRMADO"
    elif lead.get("instagram") or lead.get("facebook"):
        lead["presence_status"] = "INCOMPLETA"
    else:
        lead["presence_status"] = "NÃO IDENTIFICADA"


def enrich_marble(leads: list[dict], details: list[dict]) -> None:
    def key(s: str) -> str:
        return re.sub(r"[^a-z0-9]", "", unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower())
    for lead in leads:
        if lead["niche"] != "Marmorarias":
            continue
        lk = key(lead["name"])
        best = None
        best_score = 0
        for detail in details:
            dk = key(detail.get("name", ""))
            common = len(set(re.findall(r"[a-z0-9]{4,}", slugify(lead["name"]).replace("-", " "))) & set(re.findall(r"[a-z0-9]{4,}", slugify(detail.get("name", "")).replace("-", " "))))
            exactish = lk in dk or dk in lk
            candidate_score = 100 if exactish else common
            if candidate_score > best_score:
                best_score, best = candidate_score, detail
        if not best or best_score == 0:
            continue
        addr = best.get("address", {}).get("streetAddress")
        if addr:
            lead["address"] = addr
            parts = [p.strip() for p in addr.split(",")]
            for p in parts:
                if p and not re.search(r"\d", p) and p not in ("Londrina - PR", "Londrina"):
                    if p.lower() not in ("av.", "rua"):
                        lead["bairro"] = p
        if best.get("telephone"):
            lead["phone"] = normalize_phone(str(best["telephone"]))
        rating = best.get("aggregateRating", {})
        lead["rating"] = rating.get("ratingValue")
        lead["review_count"] = rating.get("reviewCount")
        same_as = best.get("sameAs", "")
        kind = domain_kind(same_as)
        if kind == "website":
            lead["website"] = same_as
            lead["site_status"] = "SIM"
        elif kind == "instagram":
            lead["instagram"] = same_as
        elif kind == "facebook":
            lead["facebook"] = same_as
        geo = best.get("geo", {})
        lead["latitude"] = geo.get("latitude")
        lead["longitude"] = geo.get("longitude")
        lead["maps_url"] = "https://www.google.com/maps/search/?api=1&query=" + quote_plus(f"{lead['name']} {lead['address']}")
        lead["sources"].append(best["detail_source"])
        lead["observed_facts"] = "Nome, endereço, telefone e presença no diretório; nota e avaliações publicadas como dados do Google na fonte setorial."
        opp, solutions, approach = build_opportunity(lead)
        lead["opportunities"], lead["recommended_solutions"], lead["suggested_approach"] = opp, solutions, approach
        lead["score"], lead["score_justification"] = score_lead(lead)
        lead["priority"] = priority(lead["score"])


def deduplicate(leads: list[dict]) -> list[dict]:
    seen = set()
    output = []
    for lead in leads:
        key = (slugify(lead["name"]), re.sub(r"\D", "", lead["phone"]), slugify(lead["address"]))
        if key in seen:
            continue
        seen.add(key)
        output.append(lead)
    return output


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--refresh", action="store_true", help="Baixa novamente as fontes públicas")
    parser.add_argument("--limit", type=int, default=20, help="Máximo de empresas por nicho")
    args = parser.parse_args()
    details = load_marble_details(args.refresh, max_items=max(args.limit, 29))
    london_details = [
        detail for detail in details
        if detail.get("address", {}).get("addressLocality", "").strip().lower() == "londrina"
        and "Londrina - PR" in detail.get("address", {}).get("streetAddress", "")
    ]
    leads = [make_marble_lead(detail) for detail in london_details[: args.limit]]
    for source in SOURCES:
        if source.niche == "Marmorarias":
            continue
        page = fetch(source.url, RAW_DIR / source.filename, args.refresh)
        records = block_to_records(page)
        for record in records[: args.limit]:
            leads.append(make_lead(record, source))
    apply_manual_verifications(leads)
    if args.refresh:
        # Verificação técnica apenas dos URLs identificados; não mede velocidade
        # nem qualidade visual e não autoriza inferências além de acessibilidade.
        from concurrent.futures import ThreadPoolExecutor
        with ThreadPoolExecutor(max_workers=5) as pool:
            list(pool.map(technical_site_check, leads))
    else:
        for lead in leads:
            technical_site_check(lead)
    for lead in leads:
        set_presence_status(lead)
    leads = deduplicate(leads)
    leads.sort(key=lambda x: (SOURCES.index(next(s for s in SOURCES if s.niche == x["niche"])), -x["score"], x["name"]))
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    (DATA_DIR / "leads_londrina.json").write_text(json.dumps(leads, ensure_ascii=False, indent=2), encoding="utf-8")
    counts = {s.niche: sum(1 for x in leads if x["niche"] == s.niche) for s in SOURCES}
    print(json.dumps({"total": len(leads), "por_nicho": counts}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
