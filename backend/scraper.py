import requests
from bs4 import BeautifulSoup
import re
import logging
from typing import List, Dict

logger = logging.getLogger(__name__)

MFINANTE_BASE = "https://mfinante.gov.ro/apps"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "ro-RO,ro;q=0.9,en;q=0.8",
}

COUNTY_CODES = {
    "40": "BUCURESTI", "01": "ALBA", "02": "ARAD", "03": "ARGES", "04": "BACAU",
    "05": "BIHOR", "06": "BISTRITA-NASAUD", "07": "BOTOSANI", "08": "BRASOV",
    "09": "BRAILA", "10": "BUZAU", "11": "CARAS-SEVERIN", "12": "CLUJ",
    "13": "CONSTANTA", "14": "COVASNA", "15": "DAMBOVITA", "16": "DOLJ",
    "17": "GALATI", "18": "GORJ", "19": "HARGHITA", "20": "HUNEDOARA",
    "21": "IALOMITA", "22": "IASI", "23": "ILFOV", "24": "MARAMURES",
    "25": "MEHEDINTI", "26": "MURES", "27": "NEAMT", "28": "OLT",
    "29": "PRAHOVA", "30": "SATU MARE", "31": "SALAJ", "32": "SIBIU",
    "33": "SUCEAVA", "34": "TELEORMAN", "35": "TIMIS", "36": "TULCEA",
    "37": "VASLUI", "38": "VALCEA", "39": "VRANCEA", "51": "CALARASI", "52": "GIURGIU",
}

# CAEN codes requested by the user (printing, publishing, textiles, advertising)
CAEN_CODES = {
    "1721": {
        "description_ro": "Fabricarea hârtiei și cartonului ondulat și a ambalajelor din hârtie și carton",
        "description_en": "Manufacture of corrugated paper and paperboard and of containers of paper and paperboard",
        "keywords": ["HARTIE", "CARTON", "ONDULAT", "AMBALAJ", "CUTIE", "SACI", "PUNGI", "BIBLIORAFT"],
    },
    "1722": {
        "description_ro": "Fabricarea produselor de uz gospodăresc și sanitar, din hârtie sau carton",
        "description_en": "Manufacture of household and sanitary goods and of toilet requisites",
        "keywords": ["GOSPODARESC", "SANITAR", "HARTIE", "TISUE", "SERVETELE", "PROSOP"],
    },
    "1723": {
        "description_ro": "Fabricarea articolelor de papetărie",
        "description_en": "Manufacture of paper stationery",
        "keywords": ["PAPETARIE", "CAIETE", "PLICURI", "REGISTRE", "BIROU", "PAPET"],
    },
    "1724": {
        "description_ro": "Fabricarea tapetului",
        "description_en": "Manufacture of wallpaper",
        "keywords": ["TAPET", "TAPETURI", "PERETE", "DECORATIV"],
    },
    "1725": {
        "description_ro": "Fabricarea altor articole din hârtie și carton n.c.a.",
        "description_en": "Manufacture of other articles of paper and paperboard n.e.c.",
        "keywords": ["HARTIE", "CARTON", "ALTE", "TURNARE", "PRESARE"],
    },
    "1811": {
        "description_ro": "Tiparirea ziarelor",
        "description_en": "Printing of newspapers",
        "keywords": ["TIPAR", "TIPOGRAF", "PRINT", "ZIAR", "PRESS", "EDITORIAL", "IMPRIM"],
    },
    "1812": {
        "description_ro": "Alte activitati de tiparire",
        "description_en": "Other printing activities",
        "keywords": ["TIPAR", "TIPOGRAF", "PRINT", "GRAFICA", "IMPRIM", "OFFSET", "LITOGRAF"],
    },
    "1813": {
        "description_ro": "Servicii pregatitoare pentru pretiparire",
        "description_en": "Pre-press and pre-media services",
        "keywords": ["PRETIPAR", "PREPRESS", "CLICHE", "GRAFICA", "DESKTOP", "LITOGR"],
    },
    "1814": {
        "description_ro": "Legatorie si servicii conexe",
        "description_en": "Binding and related services",
        "keywords": ["LEGATOR", "CARTE", "BROSUR", "BIND", "FINISARE"],
    },
    "5811": {
        "description_ro": "Editarea cartilor",
        "description_en": "Book publishing",
        "keywords": ["EDITUR", "CARTE", "BOOK", "PUBLISH", "AUTOR", "LIBRARI"],
    },
    "5812": {
        "description_ro": "Editarea directoarelor si a listelor de adrese",
        "description_en": "Publishing of directories and mailing lists",
        "keywords": ["DIRECTOR", "CATALOG", "LIST", "GHID", "REGISTR"],
    },
    "5813": {
        "description_ro": "Editarea ziarelor",
        "description_en": "Publishing of newspapers",
        "keywords": ["ZIAR", "PRESS", "JURNAL", "GAZET", "NEWS", "EDITORIAL"],
    },
    "5814": {
        "description_ro": "Editarea revistelor si a periodicelor",
        "description_en": "Publishing of journals and periodicals",
        "keywords": ["REVIST", "PERIODIC", "MAGAZIN", "PUBLICATI"],
    },
    "5819": {
        "description_ro": "Alte activitati de editare",
        "description_en": "Other publishing activities",
        "keywords": ["EDITUR", "PUBLISH", "EDIT", "TIPAR"],
    },
    "7311": {
        "description_ro": "Activitati ale agentiilor de publicitate",
        "description_en": "Advertising agencies",
        "keywords": ["PUBLICITAR", "ADVERTIS", "RECLAM", "MEDIA", "CREATIV", "AGENTI"],
    },
    "7312": {
        "description_ro": "Servicii de reprezentare media",
        "description_en": "Media representation services",
        "keywords": ["MEDIA", "REPRESENT", "PUBLICITAR", "AGENTI", "RECLAM"],
    },
    "1330": {
        "description_ro": "Finisarea materialelor textile",
        "description_en": "Finishing of textiles",
        "keywords": ["TEXTIL", "FINISAJ", "VOPSITOR", "IMPRIM", "TESATUR"],
    },
    "1392": {
        "description_ro": "Fabricarea articolelor textile finite, cu exceptia imbracamintei",
        "description_en": "Manufacture of made-up textile articles, except apparel",
        "keywords": ["TEXTIL", "CONFECTI", "PERDEA", "DRAPERI", "PATURA", "LENJERI"],
    },
    "1395": {
        "description_ro": "Fabricarea tesaturilor netesute si a articolelor din acestea",
        "description_en": "Manufacture of non-wovens and articles made from non-wovens",
        "keywords": ["NETES", "NONWOVEN", "TEXTIL", "FIBR", "GEOTEXTIL"],
    },
    "1396": {
        "description_ro": "Fabricarea altor textile tehnice si industriale",
        "description_en": "Manufacture of other technical and industrial textiles",
        "keywords": ["TEXTIL", "TEHNIC", "INDUSTRIAL", "BANDA", "FILTR", "CORDON"],
    },
    "1399": {
        "description_ro": "Fabricarea altor articole textile n.c.a.",
        "description_en": "Manufacture of other textiles n.e.c.",
        "keywords": ["TEXTIL", "DANTELA", "TUL", "PASAMAN", "BRODERI"],
    },
}


def search_mfinante_by_name(name: str, county_code: str = "40") -> List[Dict]:
    """Search companies on mfinante.gov.ro by name and county."""
    try:
        session = requests.Session()
        session.headers.update(HEADERS)
        session.get(f"{MFINANTE_BASE}/agentinume.html?pagina=domenii", timeout=12)
        resp = session.post(
            f"{MFINANTE_BASE}/numeCod.html",
            data={"judet": county_code, "name": name, "submit": "VIZUALIZARE"},
            timeout=12,
        )
        if resp.status_code != 200:
            return []
        return _parse_name_results(resp.text, county_code)
    except Exception as e:
        logger.error(f"mfinante search error: {e}")
        return []


def search_by_caen_code(caen_code: str, county_code: str = "40") -> List[Dict]:
    """Search companies by CAEN code using mapped keywords on mfinante.gov.ro."""
    caen = CAEN_CODES.get(caen_code)
    if not caen:
        return []
    all_results = []
    seen_cuis = set()
    session = requests.Session()
    session.headers.update(HEADERS)
    for keyword in caen["keywords"]:
        try:
            session.get(f"{MFINANTE_BASE}/agentinume.html?pagina=domenii", timeout=12)
            resp = session.post(
                f"{MFINANTE_BASE}/numeCod.html",
                data={"judet": county_code, "name": keyword, "submit": "VIZUALIZARE"},
                timeout=12,
            )
            if resp.status_code != 200:
                continue
            companies = _parse_name_results(resp.text, county_code)
            for c in companies:
                if c["cui"] not in seen_cuis:
                    c["caen_code"] = caen_code
                    c["caen_description"] = caen["description_ro"]
                    seen_cuis.add(c["cui"])
                    all_results.append(c)
        except Exception as e:
            logger.warning(f"CAEN keyword search error for {keyword}: {e}")
            continue
    return all_results


def fetch_company_detail(cui: str) -> Dict:
    """Try to fetch company details from mfinante.gov.ro. Returns what we can get."""
    detail = {
        "cui": cui,
        "mfinante_url": f"https://mfinante.gov.ro/apps/agenticod.html?cod={cui}",
    }
    return detail


ANAF_API_URL = "https://webservicesp.anaf.ro/api/PlatitorTvaRest/v9/tva"


def enrich_companies_with_anaf(companies: List[Dict], today_str: str = None) -> List[Dict]:
    """Batch-call ANAF API to get establishment dates and extra details for companies."""
    if not companies:
        return companies
    if not today_str:
        from datetime import date
        today_str = date.today().isoformat()

    import time

    enriched_map = {}
    cuis = [c["cui"] for c in companies if c.get("cui")]

    for i in range(0, len(cuis), 50):
        chunk = cuis[i:i + 50]
        payload = [{"cui": int(cui), "data": today_str} for cui in chunk if cui.isdigit()]
        if not payload:
            continue

        # Retry up to 2 times per batch with small delay
        for attempt in range(2):
            try:
                resp = requests.post(
                    ANAF_API_URL, json=payload,
                    headers={"Content-Type": "application/json"},
                    timeout=20,
                )
                if resp.status_code == 200 and resp.text.strip():
                    data = resp.json()
                    for item in data.get("found", []):
                        g = item.get("date_generale", {})
                        cui_str = str(g.get("cui", ""))
                        enriched_map[cui_str] = {
                            "data_inregistrare": g.get("data_inregistrare", ""),
                            "stare_inregistrare": g.get("stare_inregistrare", ""),
                            "phone_anaf": g.get("telefon", ""),
                            "address_anaf": g.get("adresa", ""),
                            "cod_caen_anaf": g.get("cod_CAEN", ""),
                            "nr_reg_com": g.get("nrRegCom", ""),
                            "forma_juridica": g.get("forma_juridica", ""),
                        }
                    break  # Success, move to next batch
                else:
                    logger.warning(f"ANAF API returned status {resp.status_code} for batch {i//50+1}")
            except Exception as e:
                logger.warning(f"ANAF API batch {i//50+1} attempt {attempt+1} error: {e}")

            if attempt < 1:
                time.sleep(1)  # Brief pause before retry

        # Small delay between batches to avoid rate limiting
        if i + 50 < len(cuis):
            time.sleep(0.5)

    # Merge ANAF data into companies
    for company in companies:
        anaf = enriched_map.get(company.get("cui", ""), {})
        if anaf:
            company["establishment_date"] = anaf.get("data_inregistrare", "")
            company["stare_inregistrare"] = anaf.get("stare_inregistrare", "")
            if anaf.get("phone_anaf"):
                company["phone"] = anaf["phone_anaf"]
            if anaf.get("address_anaf"):
                company["address"] = anaf["address_anaf"]
            if anaf.get("nr_reg_com"):
                company["j_number"] = anaf["nr_reg_com"]
            if anaf.get("cod_caen_anaf"):
                company["actual_caen"] = anaf["cod_caen_anaf"]

    return companies


def _parse_name_results(html: str, county_code: str) -> List[Dict]:
    soup = BeautifulSoup(html, "lxml")
    companies = []
    rows = soup.find_all("tr", align="center")
    county_name = COUNTY_CODES.get(county_code, "")
    for row in rows:
        cells = row.find_all("td")
        if len(cells) < 2:
            continue
        cui_input = row.find("input", {"type": "submit"})
        cui = cui_input.get("value", "").strip() if cui_input else ""
        name_text = cells[1].get_text(strip=True)
        if cui and name_text:
            companies.append({
                "company_name": name_text,
                "cui": cui,
                "county": county_name,
                "county_code": county_code,
                "address": f"Jud. {county_name}",
                "source_url": f"https://mfinante.gov.ro/apps/agenticod.html?cod={cui}",
                "source": "mfinante.gov.ro",
            })
    return companies


def get_counties() -> List[Dict]:
    return [{"code": code, "name": name} for code, name in sorted(COUNTY_CODES.items(), key=lambda x: x[1])]


def get_caen_codes() -> List[Dict]:
    return [
        {"code": code, "description_ro": info["description_ro"], "description_en": info["description_en"]}
        for code, info in CAEN_CODES.items()
    ]
