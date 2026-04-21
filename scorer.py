import json, os, re
import anthropic
from config import (
    KEYWORDS_POSITIFS, KEYWORDS_NEGATIFS,
    CLAUDE_MODEL, CLAUDE_MAX_TOKENS,
    SCORE_SEUIL, SEEN_IDS_FILE,
)

client = anthropic.Anthropic()

# Mots-cles ENR qui donnent un bonus de +1 point
KEYWORDS_ENR_BOOST = [
    "solaire", "photovoltaique", "photovoltaïque",
    "ENR", "energie renouvelable", "énergie renouvelable",
    "centrale solaire", "eolien", "éolien",
    "agrivoltaique", "agrivoltaïque",
    "CRE", "CSPE", "autoconsommation",
    "ombriere", "ombrière", "parc solaire",
]

SYSTEM_PROMPT = """Tu es un assistant qui analyse des marches publics francais.
Tu reponds TOUJOURS et UNIQUEMENT avec un objet JSON valide sur une seule ligne.
Tu ne dis rien d'autre. Pas de texte avant, pas de texte apres, pas de markdown."""

def _build_prompt(avis: dict) -> str:
    acheteur = avis.get("acheteur") or {}
    return f"""Analyse ce marche public et reponds avec ce JSON exact (une seule ligne) :
{{"score":7,"type_mission":"AMO","resume":"Resume en 2 phrases.","points_attention":"Point de vigilance ou vide.","urgence":"moyenne"}}

Regles :
- score : entier 1-10 selon pertinence pour un cabinet specialise en AMO, ingenierie financiere, PPP, SEM, ENR
- type_mission : une valeur parmi AMO / Ingenierie financiere / PPP-Concession / SEM-Fonds / ENR-Conseil / Autre
- urgence : haute (delai < 3 semaines) / moyenne (3-6 semaines) / faible (> 6 semaines ou inconnue)

Marche a analyser :
Objet: {avis.get("objet", "N/A")}
Acheteur: {acheteur.get("denominationSociale", "N/A")}
Montant: {avis.get("montant", "N/C")} EUR
Procedure: {avis.get("procedure", "N/A")}
Date limite: {avis.get("dateLimiteReception", "N/A")}
Source: {avis.get("_source", "BOAMP")}

Reponds uniquement avec le JSON, rien d'autre."""


def _pre_filtre(avis: dict) -> bool:
    texte = " ".join([
        (avis.get("objet") or ""),
        str(avis.get("cpv") or ""),
    ]).lower()
    has_positive = any(kw.lower() in texte for kw in KEYWORDS_POSITIFS)
    has_negative = any(kw.lower() in texte for kw in KEYWORDS_NEGATIFS)
    return has_positive and not has_negative


def _enr_boost(avis: dict) -> bool:
    """True si l'avis concerne un projet ENR/solaire -> bonus +1."""
    objet = (avis.get("objet") or "").lower()
    return any(kw.lower() in objet for kw in KEYWORDS_ENR_BOOST)


def _extract_json(text: str) -> dict | None:
    text = text.strip()
    try:
        return json.loads(text)
    except Exception:
        pass
    match = re.search(r'\{[^{}]+\}', text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group())
        except Exception:
            pass
    return None


def _scorer_avis(avis: dict) -> dict | None:
    try:
        message = client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=CLAUDE_MAX_TOKENS,
            system=SYSTEM_PROMPT,
            messages=[{"role": "user", "content": _build_prompt(avis)}],
        )
        raw = message.content[0].text.strip() if message.content else ""
        if not raw:
            print(f"    [scorer] Reponse vide pour {avis.get('idweb')}")
            return None
        analyse = _extract_json(raw)
        if not analyse:
            print(f"    [scorer] JSON non parseable pour {avis.get('idweb')}: {raw[:80]}")
            return None
        return {**avis, **analyse}
    except Exception as e:
        print(f"    [scorer] Erreur Claude pour {avis.get('idweb')}: {e}")
        return None


def _load_seen_ids() -> set:
    if os.path.exists(SEEN_IDS_FILE):
        with open(SEEN_IDS_FILE) as f:
            return set(json.load(f))
    return set()


def _save_seen_ids(ids: set):
    os.makedirs(os.path.dirname(SEEN_IDS_FILE), exist_ok=True)
    with open(SEEN_IDS_FILE, "w") as f:
        json.dump(list(ids), f, indent=2)


def run_scoring(avis_list: list[dict], skip_seen: bool = True) -> list[dict]:
    seen_ids = _load_seen_ids() if skip_seen else set()
    scored   = []
    nb_total = len(avis_list)
    nb_new = nb_filtre = nb_claude = 0

    for avis in avis_list:
        idweb = avis.get("idweb")
        if skip_seen and idweb in seen_ids:
            continue
        nb_new += 1

        if not _pre_filtre(avis):
            seen_ids.add(idweb)
            continue
        nb_filtre += 1

        print(f"    [Claude] {idweb} - {avis.get('objet','')[:55]}...")
        result = _scorer_avis(avis)
        nb_claude += 1

        if result:
            score = result.get("score", 0)

            # Bonus ENR : +1 point si projet solaire/ENR, plafonne a 10
            is_enr = _enr_boost(avis)
            if is_enr:
                score = min(score + 1, 10)
                result["score"]     = score
                result["enr_boost"] = True
            else:
                result["enr_boost"] = False

            source = avis.get("_source", "BOAMP")
            boost_label = " [ENR+1]" if is_enr else ""
            print(f"             -> score={score}{boost_label} | {result.get('type_mission')} | {result.get('urgence')} | {source}")

            if score >= SCORE_SEUIL:
                scored.append(result)

        seen_ids.add(idweb)

    if skip_seen:
        _save_seen_ids(seen_ids)

    print(f"\n  [scorer] {nb_total} recus | {nb_new} nouveaux | {nb_filtre} pre-filtre | {nb_claude} Claude | {len(scored)} retenus")

    # Tri : score decroissant, ENR en priorite a score egal
    return sorted(scored, key=lambda x: (x.get("score", 0), x.get("enr_boost", False)), reverse=True)
