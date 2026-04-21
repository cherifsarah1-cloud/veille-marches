"""
Script de diagnostic — explore la vraie structure de l'API BOAMP OpenDataSoft.
Lance : python diagnose_boamp.py
"""

import requests
import json

BASE_URL = "https://boamp-datadila.opendatasoft.com/api/explore/v2.1/catalog/datasets/boamp/records"

print("=== Test 1 : récupération de 2 avis sans filtre ===\n")
try:
    r = requests.get(BASE_URL, params={"limit": 2}, timeout=30)
    print(f"Status : {r.status_code}")
    data = r.json()
    records = data.get("results", [])
    if records:
        print(f"\nNombre de champs disponibles : {len(records[0])}")
        print("\nNoms des champs :")
        for k in sorted(records[0].keys()):
            val = records[0][k]
            apercu = str(val)[:80] if val else "None"
            print(f"  {k:40s} = {apercu}")
    else:
        print("Aucun résultat.")
        print("Réponse brute :", json.dumps(data, indent=2)[:500])
except Exception as e:
    print(f"Erreur : {e}")

print("\n\n=== Test 2 : filtre par date uniquement ===\n")
try:
    params = {
        "where": "dateparution >= '2026-03-01'",
        "limit": 2,
    }
    r = requests.get(BASE_URL, params=params, timeout=30)
    print(f"Status : {r.status_code}")
    if r.status_code == 400:
        print("Erreur 400 :", r.text[:300])
    else:
        data = r.json()
        print(f"Résultats : {data.get('total_count', '?')} avis trouvés")
except Exception as e:
    print(f"Erreur : {e}")

print("\n\n=== Test 3 : explorer les datasets disponibles ===\n")
try:
    r = requests.get(
        "https://boamp-datadila.opendatasoft.com/api/explore/v2.1/catalog/datasets",
        params={"limit": 10},
        timeout=30
    )
    print(f"Status : {r.status_code}")
    data = r.json()
    for ds in data.get("datasets", []):
        print(f"  {ds.get('dataset_id')} — {ds.get('metas', {}).get('default', {}).get('title', '')}")
except Exception as e:
    print(f"Erreur : {e}")
