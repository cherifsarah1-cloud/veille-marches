"""
Runner local pour tester l'agent sans envoyer d'email ni polluer seen_ids.

Usage :
    python run_local.py                        # BOAMP + TED, fenêtre 15j
    python run_local.py --days 30              # Fenêtre élargie
    python run_local.py --no-score             # Avis bruts sans Claude
    python run_local.py --source boamp         # BOAMP uniquement
    python run_local.py --source ted           # TED uniquement
    python run_local.py --open                 # Ouvre le dashboard après génération
"""

import argparse, webbrowser
from pathlib import Path

from boamp_fetcher import fetch_avis
from ted_fetcher import fetch_avis_ted
from scorer import run_scoring, _pre_filtre
from renderer import render_dashboard
from config import SCORE_SEUIL, LOOKBACK_DAYS


def print_brut(avis_list: list[dict]):
    passes = [a for a in avis_list if _pre_filtre(a)]
    print(f"\n  {len(passes)} avis passent le pré-filtre (/{len(avis_list)} total) :\n")
    for a in passes:
        acheteur = (a.get("acheteur") or {}).get("denominationSociale", "?")
        montant  = a.get("montant") or "N/C"
        source   = a.get("_source", "BOAMP")
        print(f"  [{source}] [{a.get('idweb')}] {a.get('objet', '')[:75]}")
        print(f"           {acheteur} | {montant} € | Délai: {a.get('dateLimiteReception','?')}")
        print()


def main():
    parser = argparse.ArgumentParser(description="Veille marchés — test local")
    parser.add_argument("--days",     type=int, default=LOOKBACK_DAYS)
    parser.add_argument("--no-score", action="store_true")
    parser.add_argument("--open",     action="store_true")
    parser.add_argument("--source",   choices=["boamp", "ted", "all"], default="all")
    args = parser.parse_args()

    print(f"\n━━━ Veille marchés — test local (fenêtre: {args.days}j | source: {args.source}) ━━━\n")

    avis_bruts = []

    if args.source in ("boamp", "all"):
        print("1. Récupération BOAMP…")
        avis_bruts += fetch_avis(lookback_days=args.days)

    if args.source in ("ted", "all"):
        print("\n2. Récupération TED…")
        avis_bruts += fetch_avis_ted(lookback_days=args.days)

    if not avis_bruts:
        print("\n  Aucun avis récupéré.")
        return

    print(f"\n  Total : {len(avis_bruts)} avis toutes sources")

    if args.no_score:
        print_brut(avis_bruts)
        return

    print("\n3. Scoring Claude…")
    avis_scores = run_scoring(avis_bruts, skip_seen=False)

    print("\n4. Génération dashboard…")
    dashboard_path = render_dashboard(avis_scores)

    # Résumé
    print(f"\n{'─'*55}")
    print(f"  {len(avis_scores)} opportunités retenues (score ≥ {SCORE_SEUIL}/10)")
    if avis_scores:
        print(f"\n  Top 5 :")
        for a in avis_scores[:5]:
            source = a.get("_source", "BOAMP")
            print(f"  [{a.get('score')}/10][{source}] {a.get('objet','')[:60]}")
            print(f"         → {a.get('type_mission')} | {a.get('urgence')} | {(a.get('acheteur') or {}).get('denominationSociale','?')}")
    print(f"\n  Dashboard : {Path(dashboard_path).resolve()}")
    print(f"{'─'*55}\n")

    if args.open:
        webbrowser.open(f"file://{Path(dashboard_path).resolve()}")

    print("  Email non envoyé (mode test). Lance main.py pour le run complet.\n")


if __name__ == "__main__":
    main()
