"""
Génération du dashboard HTML statique à partir des avis scorés.
"""

import os
from datetime import datetime
from jinja2 import Environment, FileSystemLoader

from config import DASHBOARD_FILE

TEMPLATES_DIR = "templates"


def render_dashboard(avis_scores: list[dict]) -> str:
    """
    Génère output/index.html.
    Retourne le chemin du fichier généré.
    """
    env  = Environment(loader=FileSystemLoader(TEMPLATES_DIR))
    tmpl = env.get_template("dashboard.html")

    html = tmpl.render(
        avis     = avis_scores,
        date_run = datetime.today().strftime("%d/%m/%Y à %Hh%M"),
        total    = len(avis_scores),
    )

    os.makedirs(os.path.dirname(DASHBOARD_FILE), exist_ok=True)
    with open(DASHBOARD_FILE, "w", encoding="utf-8") as f:
        f.write(html)

    print(f"  [renderer] Dashboard généré : {DASHBOARD_FILE} ({len(avis_scores)} opportunités)")
    return DASHBOARD_FILE
