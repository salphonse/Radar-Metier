import requests
import csv

# === CONFIGURATION ===
AUTH_URL = "https://francetravail.io/connexion/oauth2/access_token?realm=/partenaire"
API_URL = "https://api.francetravail.io/partenaire/offresdemploi/v2/offres/search"
CREDENTIALS_FILE = "C:/Users/Utilisateur/Downloads/Test API/France Travail/credentials.txt"
SCOPE = "api_offresdemploiv2 o2dsoffre"
CSV_FILENAME = "C:/Users/Utilisateur/Downloads/Test API/France Travail/offres_emploi.csv"

# === LIRE LES IDENTIFIANTS ===
def read_credentials(filepath):
    creds = {}
    with open(filepath, "r") as f:
        for line in f:
            if "=" in line:
                key, value = line.strip().split("=", 1)
                creds[key.strip()] = value.strip()
    return creds.get("CLIENT_ID"), creds.get("CLIENT_SECRET")

# === OBTENIR UN TOKEN D'ACCÈS ===
def get_token(client_id, client_secret):
    data = {
        "grant_type": "client_credentials",
        "client_id": client_id,
        "client_secret": client_secret,
        "scope": SCOPE
    }
    response = requests.post(AUTH_URL, data=data)
    response.raise_for_status()
    token = response.json().get("access_token")
    if not token:
        raise Exception("Token manquant dans la réponse.")
    return token

# === RÉCUPÉRER LES OFFRES ET EXPORTER EN CSV ===
def extract_and_save_csv(token, filename=CSV_FILENAME):
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/json"
    }

    params = {
        "motsCles": "développeur python",
        "region": "11",         # Île-de-France
        "range": "0-19",        # 20 résultats
    }

    response = requests.get(API_URL, headers=headers, params=params)
    response.raise_for_status()

    data = response.json()
    offres = data.get("resultats", [])

    if not offres:
        print("Aucune offre trouvée.")
        return

    with open(filename, "w", newline="", encoding="utf-8") as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=[
            "Intitulé", "Lieu", "Entreprise", "Date de publication", "Description", "URL"
        ])
        writer.writeheader()
        for offre in offres:
            writer.writerow({
                "Intitulé": offre.get("intitule", ""),
                "Lieu": offre.get("lieuTravail", {}).get("libelle", ""),
                "Entreprise": offre.get("entreprise", {}).get("nom", ""),
                "Date de publication": offre.get("dateCreation", ""),
                "Description": offre.get("description", "").replace("\n", " ").strip(),
                "URL": offre.get("origineOffre", {}).get("urlOrigine", "")
            })

    print(f"✅ {len(offres)} offres exportées dans {filename}")

# === MAIN ===
if __name__ == "__main__":
    try:
        client_id, client_secret = read_credentials(CREDENTIALS_FILE)
        token = get_token(client_id, client_secret)
        print("✅ Token obtenu avec succès.")
        extract_and_save_csv(token)
    except Exception as e:
        print("❌ Erreur :", e)