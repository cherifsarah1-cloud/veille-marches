"""
Point d'entrée production — exécuté par GitHub Actions.
Sources : BOAMP + TED
"""

from boamp_fetcher import fetch_avis
from ted_fetcher import fetch_avis_ted
from scorer import run_scoring
from renderer import render_dashboard
from mailer import send_digest


def main():
    print("\n━━━ Démarrage veille marchés ━━━\n")

    # 1. BOAMP
    print("1/5 Récupération BOAMP…")
    avis_boamp = fetch_avis()

    # 2. TED
    print("\n2/5 Récupération TED…")
    avis_ted = fetch_avis_ted()

    # 3. Fusion (dédoublonnage géré par seen_ids dans scorer)
    avis_bruts = avis_boamp + avis_ted
    print(f"\n     Total toutes sources : {len(avis_bruts)} avis")

    # 4. Scoring
    print("\n3/5 Scoring Claude…")
    avis_scores = run_scoring(avis_bruts, skip_seen=True)

    # 5. Dashboard
    print("\n4/5 Génération dashboard…")
    render_dashboard(avis_scores)

    # 6. Email
    print("\n5/5 Envoi email…")
    if avis_scores:
        send_digest(avis_scores)
    else:
        print("  [mailer] Aucune opportunité retenue — email non envoyé.")

    print("\n━━━ Terminé ━━━\n")


if __name__ == "__main__":
    main()
