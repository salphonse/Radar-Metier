import requests
from datetime import datetime
import re
import os
import zipfile
import tempfile
import unicodedata
from colorama import init, Fore, Style
from supabase import create_client, Client
from dotenv import load_dotenv

load_dotenv()

# === Configuration Supabase ===
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
SUPABASE_BUCKET = os.getenv("SUPABASE_BUCKET")
SUPABASE_FOLDER = os.getenv("SUPABASE_FOLDER")

# A supprimer
print(f"DEBUG -> SUPABASE_URL: {SUPABASE_URL}, SUPABASE_KEY: {SUPABASE_KEY}, SUPABASE_BUCKET: {SUPABASE_BUCKET}, SUPABASE_FOLDER: {SUPABASE_FOLDER}")

# === Connexion à Supabase ===
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# === Fonction pour supprimer les accents ===
def remove_accents(input_str):
    return ''.join(
        c for c in unicodedata.normalize('NFD', input_str)
        if unicodedata.category(c) != 'Mn'
    )

# === Récupération du dernier ZIP disponible ===
API_URL = "https://www.data.gouv.fr/api/1/datasets/repertoire-national-des-certifications-professionnelles-et-repertoire-specifique/"
resp = requests.get(API_URL)
resp.raise_for_status()
data = resp.json()

resources = data.get("resources", [])
zips = [
    r for r in resources
    if r["format"].lower() == "zip"
    and r["url"].split("/")[-1].startswith("export-fiches-csv")
]

if not zips:
    raise RuntimeError("Aucun fichier ZIP 'export-fiches-csv' trouvé.")

def extract_date(res):
    if res.get("last_modified"):
        return datetime.fromisoformat(res["last_modified"])
    m = re.search(r"(\d{4}-\d{2}-\d{2})", res["url"])
    return datetime.fromisoformat(m.group(1)) if m else datetime.min

latest = max(zips, key=extract_date)
url = latest["url"]
fname = url.split("/")[-1]
print("Zip sélectionné :", fname)

# === Téléchargement et traitement dans un dossier temporaire ===
with tempfile.TemporaryDirectory() as temp_dir:
    zip_path = os.path.join(temp_dir, fname)

    print("Téléchargement du ZIP...")
    dl = requests.get(url, stream=True)
    dl.raise_for_status()
    with open(zip_path, "wb") as f:
        for chunk in dl.iter_content(chunk_size=8192):
            f.write(chunk)
    print("Téléchargé :", zip_path)

    # === Extraction ===
    extract_dir = os.path.join(temp_dir, "extracted")
    os.makedirs(extract_dir, exist_ok=True)

    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(extract_dir)
    print("Extraction terminée.")

    # === Traitement des fichiers CSV (Enlever la date pour un meilleur traitement et les accents pour SUPABASE) ===
    for root, dirs, files in os.walk(extract_dir):
        for fichier in files:
            if fichier.endswith('.csv'):
                # Nettoyage du nom : suppression de la date
                nouveau_nom = re.sub(r'[-_]\d{4}[-_]\d{2}[-_]\d{2}(?=\.csv$)', '', fichier)

                # Supprimer les accents pour Supabase
                nom_sans_accents = remove_accents(nouveau_nom)
                storage_path = f"RNCP/{nom_sans_accents}"

                chemin_fichier = os.path.join(root, fichier)
                print(Fore.BLUE + f"Envoi : {fichier} → {nom_sans_accents}")

                with open(chemin_fichier, "rb") as file_data:
                    try:
                        supabase.storage.from_(SUPABASE_BUCKET).update(
                            storage_path,
                            file_data,
                            file_options={"content-type": "text/csv"}
                        )
                        print(Fore.GREEN +"Fichier envoyé : {storage_path}")
                    except Exception as e:
                        print(Fore.RED +"Erreur lors de l’envoi de {nom_sans_accents} : {e}")


print(Fore.YELLOW +"Tous les fichiers ont été traités et les fichiers temporaires sont nettoyés !!.")