"""
Envoi du digest email via SendGrid.
"""

import os
from datetime import datetime
from jinja2 import Environment, FileSystemLoader
import sendgrid
from sendgrid.helpers.mail import Mail

from config import DESTINATAIRES, EXPEDITEUR, DASHBOARD_URL, SCORE_SEUIL

TEMPLATES_DIR = "templates"


def send_digest(avis_scores: list[dict]) -> bool:
    """
    Envoie le digest bimensuel aux destinataires configurés.
    Retourne True si l'envoi a réussi.
    """
    api_key = os.getenv("SENDGRID_API_KEY")
    if not api_key:
        print("  [mailer] SENDGRID_API_KEY manquante — email non envoyé.")
        return False

    if not DESTINATAIRES or not DESTINATAIRES[0]:
        print("  [mailer] EMAIL_DESTINATAIRES non configuré — email non envoyé.")
        return False

    env  = Environment(loader=FileSystemLoader(TEMPLATES_DIR))
    tmpl = env.get_template("email.html")

    html_content = tmpl.render(
        avis          = avis_scores[:10],   # Top 10 dans l'email
        total         = len(avis_scores),
        dashboard_url = DASHBOARD_URL,
        date_run      = datetime.today().strftime("%d/%m/%Y"),
        score_seuil   = SCORE_SEUIL,
    )

    message = Mail(
        from_email   = EXPEDITEUR,
        to_emails    = DESTINATAIRES,
        subject      = f"🔍 Veille marchés — {len(avis_scores)} opportunité{'s' if len(avis_scores) > 1 else ''}",
        html_content = html_content,
    )

    try:
        sg       = sendgrid.SendGridAPIClient(api_key=api_key)
        response = sg.send(message)
        print(f"  [mailer] Email envoyé — status {response.status_code} → {DESTINATAIRES}")
        return True
    except Exception as e:
        print(f"  [mailer] Erreur envoi email : {e}")
        return False
