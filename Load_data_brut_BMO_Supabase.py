import requests
from bs4 import BeautifulSoup
import io
import zipfile
from supabase import create_client, Client
from dotenv import load_dotenv
import os

load_dotenv()

# === Configuration Supabase ===
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
BUCKET_NAME = "raw-data"
FOLDER = "BMO"
FOLDER_FAP = "FAP2021_CORRESPOND_ROME"

if not SUPABASE_URL or not SUPABASE_KEY:
    raise ValueError("Les variables SUPABASE_URL ou SUPABASE_KEY ne sont pas définies dans le fichier .env")

# Connexion Supabase
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

print("démarrage")

#1. LOAD fichiers bruts Besoin Main d'Oeuvre via France Travail
# URL de la page contenant les fichiers Excel et ZIP
url = "https://www.francetravail.org/opendata/enquete-besoins-en-main-doeuvre.html?type=article"
response = requests.get(url)
soup = BeautifulSoup(response.text, "html.parser")
print("Page chargée")

# Récupérer les liens vers fichiers .xlsx et .zip
fichiers_links = []
for link in soup.find_all("a", href=True):
    href = link['href']
    if ".xlsx" in href or ".zip" in href:
        if href.startswith("http"):
            fichiers_links.append(href)
        else:
            fichiers_links.append("https://www.francetravail.org" + href)

# Fonction pour uploader un fichier sur Supabase depuis un contenu en mémoire
def upload_to_supabase(filename: str, content: bytes):
    try:
        response = supabase.storage.from_(BUCKET_NAME).upload(
            f"{FOLDER}/{filename}",
            content,
            {
                "content-type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                "x-upsert": "true"
            }
        )
        
        print(f"{filename} -> Upload réussi ")
    except Exception as e:
        print(f"Erreur lors de l'upload de {filename} : {e}")

# Traitement des fichiers
for link in fichiers_links:
    raw_filename = link.split("/")[-1]
    filename_clean = raw_filename.split("?")[0]
    print(f"Téléchargement : {filename_clean}")

    resp = requests.get(link)
    if resp.status_code == 200:
        if filename_clean.endswith(".zip"):
            try:
                with zipfile.ZipFile(io.BytesIO(resp.content)) as zip_ref:
                    for file_in_zip in zip_ref.namelist():
                        if file_in_zip.endswith(".xlsx"):
                            print(f"Extraction et upload du fichier Excel : {file_in_zip}")
                            with zip_ref.open(file_in_zip) as extracted_file:
                                file_bytes = extracted_file.read()
                                upload_to_supabase(file_in_zip.split("/")[-1], file_bytes)
            except zipfile.BadZipFile:
                print(f"Erreur : fichier ZIP corrompu - {filename_clean}")
        elif filename_clean.endswith(".xlsx"):
            # Upload direct du fichier xlsx
            upload_to_supabase(filename_clean, resp.content)
        else:
            print(f"Fichier ignoré (pas .xlsx ni .zip) : {filename_clean}")
    else:
        print(f"Erreur lors du téléchargement de : {link}")


#2. LOAD du fichier de correspondance entre les codes_metier_bmo et code_rome_metier par le fichier:Dares_FAP2021_Table_passage_ROME 

# URL où se situe le fichier Excel
excel_url = "https://dares.travail-emploi.gouv.fr/donnees/la-nomenclature-des-familles-professionnelles-2021"
#"https://www.francetravail.org/sites/default/files/f83237de4f41868cb73b0e1aafe4800c/Dares_FAP2021_Table_passage_ROME.xlsx"

resp = requests.get(excel_url)
soup_exc = BeautifulSoup(resp.text, "html.parser")
print("Page chargée")

# Récupération du fichier cible: href="/sites/default/files/f83237de4f41868cb73b0e1aafe4800c/Dares_FAP2021_Table_passage_ROME.xlsx
href_cible = "/sites/default/files/f83237de4f41868cb73b0e1aafe4800c/Dares_FAP2021_Table_passage_ROME.xlsx"

lien = soup_exc.find("a", href=href_cible)
if lien:
    url_fichier = "https://www.dares.travail-emploi.gouv.fr" + href_cible
    print("Lien trouvé :", url_fichier)

    fichier_resp = requests.get(url_fichier)
    if fichier_resp.status_code == 200:
        file_excel = fichier_resp.content

# Upload du fichier dans Supabase Storage
    chemin_dans_bucket = f"{FOLDER_FAP}/Dares_FAP2021_Table_passage_ROME.xlsx"

    upload_response = supabase.storage.from_(BUCKET_NAME).upload(
        chemin_dans_bucket,
        file_excel,
        {"content-type": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"},
    )

    print("Fichier uploadé dans Supabase :", upload_response)
else:
    print("Lien introuvable sur la page DARES. Erreur lors du téléchargement du fichier :", {href_cible})
