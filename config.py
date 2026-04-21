import os
from dotenv import load_dotenv

load_dotenv()

# --- Filtres BOAMP ---
CPV_CODES = [
    "66171000",   # Conseil financier
    "79400000",   # Conseil en gestion
    "79410000",   # Conseil en affaires et management
    "71241000",   # Études de faisabilité / conseil
    "66000000",   # Services financiers (chapeau)
    "79110000",   # Services juridiques (concessions/DSP)
]

MONTANT_MIN = 20000
FAMILLES    = ["MARC", "CONCE", "AMI"]
LOOKBACK_DAYS = 15

# --- Mots-clés ---
KEYWORDS_POSITIFS = [
    "AMO", "assistance à maîtrise d'ouvrage", "assistance a maitrise d'ouvrage",
    "ingénierie financière", "ingenierie financiere",
    "structuration financière", "structuration financiere",
    "PPP", "partenariat public-privé", "partenariat public prive",
    "SEM", "société d'économie mixte",
    "concession", "DSP", "délégation de service public",
    "conseil stratégique", "aide à la décision",
    "énergie renouvelable", "ENR", "solaire", "photovoltaïque",
    "montage juridique", "modélisation financière",
    "fonds d'investissement", "fonds territorial",
]

KEYWORDS_NEGATIFS = [
    "travaux", "maîtrise d'œuvre technique", "maitrise d oeuvre",
    "BTP", "nettoyage", "gardiennage", "fournitures",
    "restauration collective", "téléphonie", "informatique",
    "véhicules", "maintenance bâtiment",
]

# --- Boost ENR (score majoré automatiquement) ---
KEYWORDS_ENR_BOOST = [
    "solaire", "photovoltaïque", "photovoltaique",
    "ENR", "énergie renouvelable", "centrale solaire",
    "éolien", "agrivoltaïque", "agrivoltaique",
    "CSPE", "CRE", "appel d'offres énergie",
    "autoconsommation", "ombrière",
]
# --- Claude ---
CLAUDE_MODEL      = "claude-haiku-4-5-20251001"
CLAUDE_MAX_TOKENS = 800
SCORE_SEUIL       = 6   # /10 minimum pour figurer dans le digest

# --- Email ---
DESTINATAIRES = os.getenv("EMAIL_DESTINATAIRES", "").split(",")
EXPEDITEUR    = os.getenv("EMAIL_EXPEDITEUR", "veille@cosygroup.fr")

# --- Paths ---
SEEN_IDS_FILE  = "data/seen_ids.json"
DASHBOARD_FILE = "output/index.html"
DASHBOARD_URL  = os.getenv("DASHBOARD_URL", "https://TON_ORG.github.io/veille-marches/")
