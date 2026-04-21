"""
Recuperation des avis TED (Tenders Electronic Daily).
API : https://tedweb.api.ted.europa.eu/v3/notices/search
Version avec auto-detection des champs supportes.
"""

import requests
from datetime import datetime, timedelta
from config import LOOKBACK_DAYS, MONTANT_MIN

TED_URL = "https://tedweb.api.ted.europa.eu/v3/notices/search"
TIMEOUT  = 30

CPV_PREFIXES = ["66171", "79400", "79410", "71241", "66000"]


def _build_query(date_min_str: str) -> str:
    date_formatted = date_min_str.replace("-", "")
    cpv_filter = " OR ".join(f"cpv~{cpv}" for cpv in CPV_PREFIXES)
    return (
        f"buyer-country=FR "
        f"AND publication-date >= {date_formatted} "
        f"AND ({cpv_filter})"
    )


def _detect_fields() -> list:
    """
    Appelle l'API sans filtre de champs pour detecter ce qui est disponible.
    Retourne une liste vide si l'API renvoie tout par defaut.
    """
    payload = {"query": "buyer-country=FR", "page": 1, "limit": 1}
    try:
        r = requests.post(TED_URL, json=payload, timeout=TIMEOUT)
        if r.status_code == 200:
            notices = r.json().get("notices", [])
            if notices:
                champs = list(notices[0].keys())
                print(f"  [TED] Champs disponibles : {champs}")
                return champs
    except Exception:
        pass
    return []


def fetch_avis_ted(lookback_days: int = LOOKBACK_DAYS) -> list[dict]:
    date_min = (datetime.today() - timedelta(days=lookback_days)).strftime("%Y-%m-%d")
    results  = []
    page     = 1

    print(f"  [TED] Recherche depuis {date_min}...")

    while True:
        # On n'envoie PAS de champs fixes - on laisse l'API renvoyer tout
        payload = {
            "query": _build_query(date_min),
            "page":  page,
            "limit": 100,
        }
        try:
            r = requests.post(TED_URL, json=payload, timeout=TIMEOUT)
            if r.status_code != 200:
                print(f"  [TED] HTTP {r.status_code}: {r.text[:400]}")
                break
            data = r.json()
        except Exception as e:
            print(f"  [TED] Erreur: {e}")
            break

        notices = data.get("notices", [])
        total   = data.get("total", 0)

        # Affiche la structure du premier avis pour debug
        if page == 1 and notices:
            print(f"  [TED] Champs reponse : {list(notices[0].keys())}")

        if not notices:
            break

        for notice in notices:
            n = _normalize(notice)
            if n:
                results.append(n)

        print(f"  [TED] Page {page} - {len(notices)} notices (total: {total})")

        if page * 100 >= min(total, 500):
            break
        page += 1

    print(f"  [TED] Total : {len(results)} avis recuperes")
    return results


def _get_text(field) -> str:
    """Extrait du texte depuis un champ potentiellement multilingue."""
    if not field:
        return ""
    if isinstance(field, dict):
        return (field.get("fra") or field.get("fre") or field.get("eng")
                or next(iter(field.values()), ""))
    if isinstance(field, list):
        first = field[0] if field else {}
        if isinstance(first, dict):
            return _get_text(first)
        return str(first)
    return str(field)


def _extract_value(tv) -> float | None:
    if not tv:
        return None
    if isinstance(tv, dict):
        v = tv.get("amount") or tv.get("value") or tv.get("totalValue")
        return float(v) if v else None
    if isinstance(tv, list) and tv:
        return _extract_value(tv[0])
    try:
        return float(tv)
    except (ValueError, TypeError):
        return None


def _normalize(notice: dict) -> dict | None:
    # Cherche l'identifiant dans plusieurs champs possibles
    pub_num = (notice.get("publication-number")
               or notice.get("ND")
               or notice.get("id")
               or "")

    objet = (_get_text(notice.get("notice-title"))
             or _get_text(notice.get("TI"))
             or _get_text(notice.get("title"))
             or "Sans titre")

    acheteur_nom = (_get_text(notice.get("buyer-name"))
                    or _get_text(notice.get("AC"))
                    or _get_text(notice.get("contracting-authority"))
                    or "N/C")

    montant = (_extract_value(notice.get("total-value"))
               or _extract_value(notice.get("TV"))
               or _extract_value(notice.get("estimated-value")))

    if montant and montant < MONTANT_MIN:
        return None

    deadline_raw = (notice.get("submission-deadline")
                    or notice.get("DT")
                    or notice.get("deadline"))
    deadline = _get_text(deadline_raw)[:10] if deadline_raw else ""

    cpv_raw = notice.get("cpv") or notice.get("PC") or []
    if isinstance(cpv_raw, str):
        cpv_raw = [cpv_raw]

    url = f"https://ted.europa.eu/en/notice/-/detail/{pub_num}" if pub_num else ""

    return {
        "idweb":               f"TED-{pub_num}",
        "objet":               objet,
        "acheteur": {
            "denominationSociale": acheteur_nom,
            "departement":         "EU",
        },
        "montant":             montant,
        "procedure":           _get_text(notice.get("procedure-type") or notice.get("PR")),
        "famille":             "TED",
        "datePublication":     "",
        "dateLimiteReception": deadline,
        "urlAvis":             url,
        "cpv":                 cpv_raw,
        "nature":              _get_text(notice.get("notice-type") or notice.get("TD")),
        "_source":             "TED",
    }
