# main.py

# uvicorn mainfusionAPI:app --reload
from dotenv import load_dotenv, find_dotenv
import os
import io
import tempfile
import pandas as pd
import torch
import dill
import boto3
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List
from sqlalchemy import create_engine

# ---------------------------
# 1. Variables d'environnement
# ---------------------------
# Localiser et recharger le .env
dotenv_path = find_dotenv(".env")
load_dotenv(dotenv_path, override=True)

# Variables DB
db_schema = 'radarmetier'

# Variables S3
S3_BUCKET = "dlhybride"
S3_ENDPOINT_URL = os.getenv("S3_ENDPOINT_URL")
S3_ACCESS_KEY_ID = os.getenv("S3_ACCESS_KEY_ID")
S3_SECRET_ACCESS_KEY = os.getenv("S3_SECRET_ACCESS_KEY")
S3_REGION = os.getenv("S3_REGION")

# ---------------------------
# 2. Connexion S3
# ---------------------------
s3_client = boto3.client(
    service_name='s3',
    region_name=S3_REGION,
    endpoint_url=S3_ENDPOINT_URL,
    aws_access_key_id=S3_ACCESS_KEY_ID,
    aws_secret_access_key=S3_SECRET_ACCESS_KEY
)

# ---------------------------
# 3. Connexion à la DB
# ---------------------------
df_competence = pd.DataFrame()

def df_from_table(table_name):
    global db_schema
    url = f"postgresql+psycopg2://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}"
    if os.getenv('DB_PORT'):
        url += f":{os.getenv('DB_PORT')}"
    if os.getenv("DB_NAME"):
        url += f"/{os.getenv('DB_NAME')}"
    try:
        engine = create_engine(url)
        with engine.connect() as conn, conn.begin():
            data_frame = pd.read_sql_table(table_name, con=conn, schema=db_schema)
            return data_frame
    except Exception as e:
        print(e)
    return pd.DataFrame()

# ---------------------------
# 4. Chargement CSV S3
# ---------------------------
def load_csv_from_s3(file_name, bucket_name=S3_BUCKET):
    response = s3_client.get_object(Bucket=bucket_name, Key=file_name)
    df = pd.read_csv(io.BytesIO(response["Body"].read()), dtype=str)
    return df

df_jobs = load_csv_from_s3("df_competence_rome_eda_v2.csv")
df_jobs["code_ogr_competence"] = df_jobs["code_ogr_competence"].astype(str)

# ---------------------------
# 5. Construction des mappings
# ---------------------------
skills_vocab = {code: idx for idx, code in enumerate(df_jobs['code_ogr_competence'].unique())}
skill_to_label = df_jobs.drop_duplicates('code_ogr_competence') \
                        .set_index('code_ogr_competence')['libelle_competence'].to_dict()
jobs_vocab = {rome: idx for idx, rome in enumerate(df_jobs['code_rome'].unique())}
job_labels = df_jobs.drop_duplicates('code_rome').set_index('code_rome')['libelle_rome'].to_dict()
job_to_skills = df_jobs.groupby('code_rome')['code_ogr_competence'].apply(set).to_dict()

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

# ---------------------------
# 6. Charger modèle S3 avec dill
# ---------------------------
def load_model_from_s3_with_dill(key):
    obj = s3_client.get_object(Bucket=S3_BUCKET, Key=key)
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pkl") as tmp_file:
        tmp_file.write(obj['Body'].read())
        tmp_model_path = tmp_file.name
    with open(tmp_model_path, "rb") as f:
        model_loaded = dill.load(f)
    model_loaded.to(device)
    model_loaded.eval()
    return model_loaded

from model import JobProfileTransformer
model_loaded = load_model_from_s3_with_dill("modele_epoch4001.pkl")

# ---------------------------
# 7. FastAPI
# ---------------------------
app = FastAPI(title="API Radar_Métiers", version="1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------
# 8. Pydantic Models
# ---------------------------
class Competence(BaseModel):
    competence: str
    macro_competence: str
    domaine_competence: str

class ProfileInput(BaseModel):
    skills: List[str]

# ---------------------------
# 9. Endpoints compétences (DB)
# ---------------------------
@app.get("/init")
def init_data():
    global df_competence
    df_competence = df_from_table("rome_arborescence_competences")
    return {"status": "ready" if df_competence.shape[0] > 0 else "error"}

# Liste des domaines de compétences
@app.post("/get_domaine_competence")
def get_domaine_competence():
    global df_competence
    if df_competence.empty:
        init_data()
    domaine = df_competence['domaine_competence'].unique()
    return {'liste_domaine': domaine.tolist()}

@app.post("/get_macro_competence")
def get_macro_competence(competence: Competence):
    global df_competence
    if df_competence.empty:
        init_data()
    df_macro = df_competence.loc[df_competence['domaine_competence'] == competence.domaine_competence][['libelle_macro_competence']]
    return {'liste_macro_competence': df_macro['libelle_macro_competence'].unique().tolist()}

# Liste des compétences par macro-compétence
@app.post("/get_competence")
def get_competence(competence: Competence):
    global df_competence
    if df_competence.shape[0] == 0:
        init_data()
    df_comp = df_competence.loc[df_competence['libelle_macro_competence'] == competence.macro_competence][['libelle_competence']]
    print(f"Nb competence: {df_comp.shape}")
    return {'liste_macro_competence': df_comp['libelle_competence'].unique().tolist()}

# ---------------------------
# 10. Fonction de prédiction jobs
# ---------------------------
def predict_hybrid(model, input_skills, skills_vocab, job_to_skills, jobs_vocab, job_labels,
                   top_k=5, seuil=0.3, min_overlap=2):
    ids = [skills_vocab[s] for s in input_skills if s in skills_vocab]
    if len(ids) == 0:
        return {"status": "undefined", "reason": "aucune compétence reconnue", "predictions": []}
    skills = torch.tensor(ids).unsqueeze(0).to(device)
    weights = torch.tensor([1.0 for _ in ids], dtype=torch.float).unsqueeze(0).to(device)
    v_p = model.encode_profile(skills, weights)
    all_jobs = torch.arange(len(jobs_vocab)).to(device)
    v_j = model.encode_job(all_jobs)
    scores_dl = (v_p @ v_j.T).squeeze(0)
    input_set = set(input_skills)
    overlap_scores_list = [len(input_set & set(job_to_skills.get(j, []))) for j in jobs_vocab.keys()]
    overlap_scores = torch.tensor(overlap_scores_list, device=device)
    combined_scores = 0.3 * scores_dl + 0.7 * (overlap_scores / max(1, max(overlap_scores)))
    filtered_indices = torch.arange(len(jobs_vocab), device=device)[overlap_scores >= min_overlap]
    filtered_scores = combined_scores[overlap_scores >= min_overlap]
    if len(filtered_scores) == 0:
        return {"status": "undefined", "reason": "aucune compétence ne passe le filtre", "predictions": []}
    best_scores, best_idx = filtered_scores.topk(min(top_k, len(filtered_scores)))
    best_jobs = [list(jobs_vocab.keys())[i] for i in filtered_indices[best_idx]]
    predictions = [
        {"rome": rome, "libelle": job_labels.get(rome, "?"), "score": round(float(s.detach().cpu()), 4)}
        for rome, s in zip(best_jobs, best_scores)
    ]
    if best_scores[0] < seuil:
        return {"status": "uncertain", "reason": "score sous le seuil", "predictions": predictions}
    return {"status": "ok", "predictions": predictions}

# ---------------------------
# 11. Endpoints jobs (S3 + modèle)
# ---------------------------

@app.post("/predict")
def predict(profile: ProfileInput):
    recognized_skills = [s for s in profile.skills if s in skills_vocab]
    prediction = predict_hybrid(
        model_loaded,
        recognized_skills,
        skills_vocab,
        job_to_skills,
        jobs_vocab,
        job_labels,
        top_k=5
    )
    return {
        "input_skills": profile.skills,
        "recognized_skills": recognized_skills,
        "result": prediction
    }
