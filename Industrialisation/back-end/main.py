"""
JobProfile API
--------------

Pour lancer l'application :
    uvicorn main:app --reload

Documentation :
    http://127.0.0.1:8000/docs
"""

import io
import os
import tempfile
from typing import List

import boto3
import dill
import pandas as pd
import torch
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy import create_engine

from model import JobProfileTransformer  # Assurez-vous que model.py est dans le même répertoire

# ===========================
# 1. Configuration & Globals
# ===========================

BUCKET_NAME = "dlhybride"
DB_SCHEMA = "radarmetier"

load_dotenv(".env")

S3_ENDPOINT_URL = os.getenv("S3_ENDPOINT_URL")
S3_ACCESS_KEY_ID = os.getenv("S3_ACCESS_KEY_ID")
S3_SECRET_ACCESS_KEY = os.getenv("S3_SECRET_ACCESS_KEY")
S3_REGION = os.getenv("S3_REGION")
S3_BUCKET = "dlhybride"

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# ===========================
# 2. Connexion S3
# ===========================

s3_client = boto3.client(
    service_name="s3",
    region_name=S3_REGION,
    endpoint_url=S3_ENDPOINT_URL,
    aws_access_key_id=S3_ACCESS_KEY_ID,
    aws_secret_access_key=S3_SECRET_ACCESS_KEY,
)

# ===========================
# 3. Chargement des données
# ===========================

def load_csv_from_s3(file_name: str, bucket_name: str = S3_BUCKET) -> pd.DataFrame:
    """Charge un CSV depuis S3 en DataFrame pandas."""
    response = s3_client.get_object(Bucket=bucket_name, Key=file_name)
    return pd.read_csv(io.BytesIO(response["Body"].read()), dtype=str)

df_jobs = load_csv_from_s3("df_competence_rome_eda_v2.csv")
df_jobs["code_ogr_competence"] = df_jobs["code_ogr_competence"].astype(str)

# Vocabulaire et mappings
skills_vocab = {code: idx for idx, code in enumerate(df_jobs["code_ogr_competence"].unique())}
skill_to_label = (
    df_jobs.drop_duplicates("code_ogr_competence")
    .set_index("code_ogr_competence")["libelle_competence"]
    .to_dict()
)
jobs_vocab = {rome: idx for idx, rome in enumerate(df_jobs["code_rome"].unique())}
job_labels = (
    df_jobs.drop_duplicates("code_rome")
    .set_index("code_rome")["libelle_rome"]
    .to_dict()
)
job_to_skills = df_jobs.groupby("code_rome")["code_ogr_competence"].apply(set).to_dict()

# ===========================
# 4. Chargement du modèle
# ===========================

def load_model_from_s3_with_dill(key: str):
    """Charge un modèle picklé (dill) depuis S3."""
    obj = s3_client.get_object(Bucket=S3_BUCKET, Key=key)
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pkl") as tmp_file:
        tmp_file.write(obj["Body"].read())
        tmp_model_path = tmp_file.name

    with open(tmp_model_path, "rb") as f:
        model_loaded = dill.load(f)

    model_loaded.to(device)
    model_loaded.eval()
    return model_loaded

model_loaded = load_model_from_s3_with_dill("modele_epoch4001.pkl")

# ===========================
# 5. Connexion DB
# ===========================

def df_from_table(table_name: str) -> pd.DataFrame | None:
    """Lit une table PostgreSQL et retourne un DataFrame."""
    user = os.getenv("DB_USER")
    password = os.getenv("DB_PASSWORD")
    host = os.getenv("DB_HOST")
    port = os.getenv("DB_PORT", "")
    db_name = os.getenv("DB_NAME", "")

    url = f"postgresql+psycopg2://{user}:{password}@{host}"
    if port:
        url += f":{port}"
    if db_name:
        url += f"/{db_name}"

    if __debug__:
        print("URL =", url)
        print("DB table:", table_name)
        print("DB schema:", DB_SCHEMA)

    try:
        engine = create_engine(url)
        with engine.connect() as conn, conn.begin():
            df = pd.read_sql_table(table_name, con=conn, schema=DB_SCHEMA)
            print(f"Data read from DB: {df.shape}")
            return df
    except Exception as e:
        print(f"Erreur DB: {e}")
        return None

def df_from_query(query):
    url = f"postgresql+psycopg2://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}"
    if len(os.getenv('DB_PORT')) > 0:
        url += f":{os.getenv('DB_PORT')}"
    if len(os.getenv("DB_NAME")) > 0:
        url += f"/{os.getenv("DB_NAME")}"
    if __debug__:
        print("URL=", url)
    try:
        engine = create_engine(url)
        with engine.connect() as conn, conn.begin():
            data_frame = pd.read_sql_query(query, con= conn)
            print(f"Data read from DB: {data_frame.shape}")
            return data_frame
    except Exception as e:
        print(e)
    return any

df_competence = pd.DataFrame()

def load_df_competence():
    """Charge df_competence depuis la DB de façon sûre"""
    global df_competence
    query = "SELECT code_domaine_competence, domaine_competence, \
            code_macro_competence, libelle_macro_competence, \
            code_ogr_competence, libelle_competence, \
            coh.code_rome, ref.libelle_rome \
            FROM radarmetier.rome_arborescence_competences arb \
            INNER JOIN radarmetier.rome_coherence_item coh ON (arb.code_ogr_competence = coh.code_ogr) \
            INNER JOIN radarmetier.rome_referentiel_code_rome ref ON(coh.code_rome = ref.code_rome);"

    df_competence = pd.DataFrame(df_from_query(query))
    print(f"df_competence chargé: {df_competence.shape}")
    #df_competence.to_csv("competences.csv", index=False, encoding="utf-8")


# ===========================
# 6. FastAPI App
# ===========================

app = FastAPI(title="JobProfile API", version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def startup_event():
    load_df_competence()

# ===========================
# 7. Schémas Pydantic
# ===========================

class ProfileInput(BaseModel):
    skills: List[str]

class Competence(BaseModel):
    competence: str | None = None
    macro_competence: str | None = None
    domaine_competence: str | None = None

# ===========================
# 8. Endpoints Init & Données
# ===========================

@app.get("/init")
def init_data():
    load_df_competence()
    if df_competence.empty:
        return {"status": "error", "message": "DataFrame vide"}
    return {"status": "ready", "message": f"{df_competence.shape[0]} lignes chargées"}

@app.post("/get_domaine_competence")
def get_domaine_competence():
    global df_competence
    if df_competence.empty:
        load_df_competence()
    return {"status": "success", "liste_domaine": df_competence["domaine_competence"].sort_values().unique().tolist()}

@app.post("/get_macro_competence")
def get_macro_competence(competence: Competence):
    global df_competence
    if df_competence.empty:
        return {"status": "error", "message": "Les données n'ont pas été initialisées. Faites d'abord /init."}
    df_macro = df_competence[df_competence["domaine_competence"] == competence.domaine_competence]
    if df_macro.empty:
        return {"status": "error", "message": f"Aucune macro-compétence pour {competence.domaine_competence}"}
    return {"status": "success", "liste_macro_competence": df_macro["libelle_macro_competence"].sort_values().unique().tolist()}

@app.post("/get_competence")
def get_competence(competence: Competence):
    global df_competence
    if df_competence.empty:
        return {
            "status": "error",
            "message": "Les données n'ont pas été initialisées. Faites d'abord /init."
        }
    # Filtrer sur la macro compétence demandée
    df_comp = (
        df_competence.loc[
            df_competence['libelle_macro_competence'] == competence.macro_competence,
            [
                'code_ogr_competence',
                'libelle_competence',
                'code_rome',
                'libelle_rome'
            ]
        ]
        .drop_duplicates(subset=["code_ogr_competence", "libelle_competence"])
        .sort_values('libelle_competence')
    )

    df_comp['code_ogr_competence'] = df_comp['code_ogr_competence'].astype(int)
    # Renommer pour un JSON plus propre
    df_comp = df_comp.rename(columns={
        'code_ogr_competence': 'code',
        'libelle_competence': 'libelle',
        'coh.code_rome': 'code_rome',
        'ref.libelle_rome': 'libelle_rome'
    })

    print(f"Nb competence: {df_comp.shape}")

    if df_comp.empty:
        return {
            "status": "error",
            "message": f"Aucune compétence pour {competence.macro_competence}"
        }

    return {
        "status": "success",
        "liste_competence": df_comp[['code', 'libelle', 'code_rome', 'libelle_rome']].to_dict(orient='records')
    }

@app.get("/get_all_competences")
def get_all_competences():
    global df_competence
    if df_competence.empty:
        return {
            "status": "error",
            "message": "Les données n'ont pas été initialisées. Faites d'abord /init."
        }

    df_comp = (
        df_competence[['code_ogr_competence', 'libelle_competence', 'code_rome', 'libelle_rome']]
        .drop_duplicates(subset=["code_ogr_competence", "libelle_competence"])
        .sort_values('libelle_competence')
    )

    df_comp['code_ogr_competence'] = df_comp['code_ogr_competence'].astype(int)

    df_comp = df_comp.rename(columns={
        'code_ogr_competence': 'code',
        'libelle_competence': 'libelle',
        'code_rome': 'code_rome',
        'libelle_rome': 'libelle_rome'
    })

    return {
        "status": "success",
        "liste_competence": df_comp[['code', 'libelle', 'code_rome', 'libelle_rome']].to_dict(orient='records')
    }

@app.post("/get_rome_actuel_list")
def get_rome_actuel_list():
    """
    Retourne la liste des codes ROME actuels (avec libellés),
    classés par ordre alphabétique de code_rome.
    """
    global df_competence
    if df_competence.empty:
        load_df_competence()

    df_rome_actuel = (
        df_competence[['code_rome', 'libelle_rome']]
        .drop_duplicates()
        .sort_values('code_rome')   # Tri alphabétique
    )

    return {
        "status": "success",
        "liste_rome_actuel": df_rome_actuel.to_dict(orient="records")
    }
print("ok")

@app.post("/get_rome_cible_list")
def get_rome_cible_list():
    """
    Retourne la liste des codes ROME ciblés (avec libellés),
    classés par ordre alphabétique de code_rome.
    Si besoin d'une autre logique pour distinguer “ciblé”,
       tu peux filtrer ici selon ta table ou ton mapping.
    """
    global df_competence
    if df_competence.empty:
        load_df_competence()

    df_rome_cible = (
        df_competence[['code_rome', 'libelle_rome']]
        .drop_duplicates()
        .sort_values('code_rome')   # Tri alphabétique
    )

    return {
        "status": "success",
        "liste_rome_cible": df_rome_cible.to_dict(orient="records")
    }
print("ok")

from fastapi import Query
@app.post("/get_competences_by_rome")
def get_competences_by_rome(code_rome: str = Query(..., description="Code ROME actuel")):
    """
    Retourne la liste des compétences correspondant au code ROME actuel.
    """
    global df_competence
    if df_competence.empty:
        load_df_competence()

    df_comp = df_competence[df_competence["code_rome"] == code_rome][
        ["code_ogr_competence", "libelle_competence"]
    ].drop_duplicates()

    return {
        "status": "success",
        "competences": df_comp.to_dict(orient="records")
    }
print("ok")
# ===========================
# 9. Fonction de prédiction
# ===========================

def predict_hybrid(model,
                    input_skills,
                    skills_vocab,
                    job_to_skills,
                    jobs_vocab,
                    job_labels,
                    top_k: int = 5,
                    seuil: float = 0.3,
                    min_overlap: int = 2,):

    ids = [skills_vocab[s] for s in input_skills if s in skills_vocab]
    if not ids:
        return {"status": "undefined", "reason": "aucune compétence reconnue", "predictions": []}

    skills = torch.tensor(ids).unsqueeze(0).to(device)
    weights = torch.tensor([1.0] * len(ids), dtype=torch.float).unsqueeze(0).to(device)

    v_p = model.encode_profile(skills, weights)
    all_jobs = torch.arange(len(jobs_vocab)).to(device)
    v_j = model.encode_job(all_jobs)
    scores_dl = (v_p @ v_j.T).squeeze(0)

    input_set = set(input_skills)
    overlap_scores = torch.tensor(
        [len(input_set & set(job_to_skills.get(j, []))) for j in jobs_vocab.keys()],
        device=device,
    )

    combined_scores = 0.3 * scores_dl + 0.7 * (overlap_scores / max(1, overlap_scores.max()))
    filtered_indices = torch.arange(len(jobs_vocab), device=device)[overlap_scores >= min_overlap]
    filtered_scores = combined_scores[overlap_scores >= min_overlap]

    if len(filtered_scores) == 0:
        return {"status": "empty", "reason": "aucun métier ne correspond aux compétences choisies", "predictions": []}

    best_scores, best_idx = filtered_scores.topk(min(top_k, len(filtered_scores)))
    best_jobs = [list(jobs_vocab.keys())[i] for i in filtered_indices[best_idx]]

    predictions = [
        {"rome": rome, 
         "libelle": job_labels.get(rome, "?"), 
         "score": round(float(s.detach().cpu()), 4)}
        for rome, s in zip(best_jobs, best_scores)
    ]

    if best_scores[0] < seuil:
        return {"status": "uncertain", "reason": "score sous le seuil", "predictions": predictions}

    return {"status": "ok", "predictions": predictions}

# ===========================
# 10. Endpoints API
# ===========================

@app.get("/")
def read_root():
    return {"message": "API opérationnelle"}

@app.post("/predict")
def predict(profile: ProfileInput):
    print(profile)
    recognized_skills = [s for s in profile.skills if s in skills_vocab]
    prediction = predict_hybrid(
        model_loaded, recognized_skills, skills_vocab, job_to_skills, jobs_vocab, job_labels, top_k=5
    )
    print("return:", {"input_skills": profile.skills, "recognized_skills": recognized_skills, "result": prediction})
    return {"input_skills": profile.skills, "recognized_skills": recognized_skills, "result": prediction}
