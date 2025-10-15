import requests
import pandas as pd

dataset = "moncompteformation_catalogueformation"
base_url = "https://opendata.caissedesdepots.fr/api/records/1.0/search/"
rows_per_page = 100
max_records = 500
all_records = []
start = 0

print("Démarrage de la récupération des données...")

while start < max_records:
    print(f"Téléchargement des enregistrements {start} à {start + rows_per_page - 1}...")
    params = {
        "dataset": dataset,
        "rows": rows_per_page,
        "start": start
    }
    try:
        response = requests.get(base_url, params=params)
        response.raise_for_status()
        data = response.json()
        records = data.get("records", [])
        if not records:
            print("Aucun enregistrement trouvé, fin de la récupération.")
            break
        all_records.extend(records)
        start += rows_per_page
    except requests.RequestException as e:
        print(f"Erreur requête API: {e}")
        break

print("Récupération terminée, traitement des données...")

fields_list = [rec["fields"] for rec in all_records]
df = pd.DataFrame(fields_list)
df.to_csv("formations_cpf_paginated.csv", index=False, encoding="utf-8-sig")

print(f"{len(df)} formations exportées dans formations_cpf_paginated.csv")
