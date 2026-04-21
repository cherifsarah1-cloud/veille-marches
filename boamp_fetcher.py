"""
Récupération des avis BOAMP via l'API OpenDataSoft.
Champs réels confirmés par diagnostic du 14/04/2026.
"""

import requests
from datetime import datetime, timedelta
from config import MONTANT_MIN, LOOKBACK_DAYS

BASE_URL = "https://boamp-datadila.opendatasoft.com/api/explore/v2.1/catalog/datasets/boamp/records"
TIMEOUT  = 30

KEYWORD_GROUPS = [
    "AMO ingénierie financière",
    "PPP partenariat public privé",
    "SEM société économie mixte concession",
    "conseil structuration financière",
    "ENR solaire photovoltaïque énergie renouvelable",
    "fonds investissement territorial",
    "délégation service public DSP",
]


def fetch_avis(lookback_days: int = LOOKBACK_DAYS) -> list[dict]:
    date_max = datetime.today()
    date_min = date_max - timedelta(days=lookback_days)
    date_min_str = date_min.strftime("%Y-%m-%d")

    seen_ids: set = set()
    results:  list = []

    for keyword_group in KEYWORD_GROUPS:
        offset = 0
        while True:
            params = {
                "where":    f"dateparution >= '{date_min_str}' AND type_marche='SERVICES'",
                "q":        keyword_group,
                "limit":    100,
                "offset":   offset,
                "order_by": "dateparution DESC",
            }
            try:
                r = requests.get(BASE_URL, params=params, timeout=TIMEOUT)
                r.raise_for_status()
                data = r.json()
            except requests.exceptions.HTTPError as e:
                print(f"  [BOAMP] HTTP {e.response.status_code} — groupe: '{keyword_group}'")
                if e.response.status_code == 400:
                    print(f"           Détail: {e.response.text[:200]}")
                break
            except Exception as e:
                print(f"  [BOAMP] Erreur — groupe '{keyword_group}': {e}")
                break

            records = data.get("results", [])
            if not records:
                break

            for record in records:
                idweb = record.get("idweb") or record.get("id", "")
                if not idweb or idweb in seen_ids:
                    continue

                montant = _extract_montant(record)
                if montant and montant < MONTANT_MIN:
                    continue

                seen_ids.add(idweb)
                results.append(_normalize(record, montant))

            total = data.get("total_count", "?")
            print(f"  [BOAMP] '{keyword_group[:35]}...' → {len(records)} résultats (serveur: {total})")

            if len(records) < 100:
                break
            offset += 100

    print(f"  [BOAMP] Total : {len(results)} avis uniques (fenêtre : {lookback_days}j)")
    return results


def _extract_montant(record: dict):
    m = record.get("montant")
    if m:
        try:
            return float(str(m).replace(" ", "").replace(",", "."))
        except (ValueError, TypeError):
            pass
    donnees = record.get("donnees")
    if isinstance(donnees, str):
        import json
        try:
            d = json.loads(donnees)
            m = d.get("MONTANT") or d.get("montant")
            if m:
                return float(str(m).replace(" ", "").replace(",", "."))
        except Exception:
            pass
    return None


def _normalize(record: dict, montant) -> dict:
    idweb = record.get("idweb") or record.get("id", "")
    url = record.get("url_avis") or f"https://www.boamp.fr/pages/avis/?q=idweb:{idweb}"
    dept_raw = record.get("code_departement") or []
    dept = dept_raw[0] if isinstance(dept_raw, list) and dept_raw else str(dept_raw)
    type_marche_raw = record.get("type_marche") or []
    type_marche = ", ".join(type_marche_raw) if isinstance(type_marche_raw, list) else str(type_marche_raw)

    return {
        "idweb":               idweb,
        "objet":               record.get("objet") or "Sans objet",
        "acheteur": {
            "denominationSociale": record.get("nomacheteur") or "N/C",
            "departement":         dept,
        },
        "montant":             montant,
        "procedure":           record.get("procedure_libelle") or record.get("procedure_categorise") or "",
        "famille":             record.get("famille") or record.get("famille_libelle") or "",
        "datePublication":     (record.get("dateparution") or "")[:10],
        "dateLimiteReception": (record.get("datelimitereponse") or "")[:10],
        "urlAvis":             url,
        "cpv":                 record.get("descripteur_code") or [],
        "nature":              record.get("nature_libelle") or "",
    }
