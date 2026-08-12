import logging
from typing import List, Dict
import requests
from datetime import date

logger = logging.getLogger(__name__)

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

CAEN_CODES = {
    "1721": {"description_ro": "Fabricarea hârtiei și cartonului ondulat și a ambalajelor din hârtie și carton"},
    "1722": {"description_ro": "Fabricarea produselor de uz gospodăresc și sanitar, din hârtie sau carton"},
    "1723": {"description_ro": "Fabricarea articolelor de papetărie"},
    "1811": {"description_ro": "Tiparirea ziarelor"},
    "1812": {"description_ro": "Alte activitati de tiparire"},
    "1813": {"description_ro": "Servicii pregatitoare pentru pretiparire"},
    "1814": {"description_ro": "Legatorie si servicii conexe"},
    "5811": {"description_ro": "Editarea cartilor"},
    "5813": {"description_ro": "Editarea ziarelor"},
    "5814": {"description_ro": "Editarea revistelor si a periodicelor"},
    "5819": {"description_ro": "Alte activitati de editare"},
    "7311": {"description_ro": "Activitati ale agentiilor de publicitate"},
    "7312": {"description_ro": "Servicii de reprezentare media"},
    "1330": {"description_ro": "Finisarea materialelor textile"},
    "1392": {"description_ro": "Fabricarea articolelor textile finite, cu exceptia imbracamintei"},
}

ANAF_API_URL = "https://webservicesp.anaf.ro/api/PlatitorTvaRest/v9/tva"


def search_mfinante_by_name(name: str, county_code: str = "40") -> List[Dict]:
    """Lightweight placeholder/search structure."""
    return []


def search_by_caen_code(caen_code: str, county_code: str = "40") -> List[Dict]:
    """Lightweight placeholder search structure."""
    return []


def fetch_company_detail(cui: str) -> Dict:
    return {
        "cui": cui,
        "mfinante_url": f"https://mfinante.gov.ro/apps/agenticod.html?cod={cui}",
    }


def enrich_companies_with_anaf(companies: List[Dict], today_str: str = None) -> List[Dict]:
    """Batch-call ANAF API to get establishment dates and extra details for companies."""
    if not companies:
        return companies
    if not today_str:
        today_str = date.today().isoformat()

    import time
    enriched_map = {}
    cuis = [c["cui"] for c in companies if c.get("cui")]

    for i in range(0, len(cuis), 50):
        chunk = cuis[i:i + 50]
        payload = [{"cui": int(cui), "data": today_str} for cui in chunk if cui.isdigit()]
        if not payload:
            continue

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
        except Exception as e:
            logger.warning(f"ANAF API error: {e}")

        time.sleep(0.5)

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


def get_counties() -> List[Dict]:
    return [{"code": code, "name": name} for code, name in sorted(COUNTY_CODES.items(), key=lambda x: x[1])]


def get_caen_codes() -> List[Dict]:
    return [{"code": code, "description_ro": info["description_ro"]} for code, info in CAEN_CODES.items()]