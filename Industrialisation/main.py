# Pour lancer l'application, utilisez la commande suivante dans le terminal :
# uvicorn main:app --reload
# L'API sera disponible sur http://127.0.0.1:8000
# Documentation interactive : http://127.0.0.1:8000/docs

from fastapi import FastAPI
from pydantic import BaseModel
from typing import List
import torch
import boto3
import os
import io
import pandas as pd
from dotenv import load_dotenv
from fastapi.middleware.cors import CORSMiddleware
import tempfile
import dill  # <-- on utilise dill pour charger le modèle pickle
from model import JobProfileTransformer


# ---------------------------
# 1. Variables d'environnement
# ---------------------------
load_dotenv('.env')
S3_ENDPOINT_URL = os.getenv("S3_ENDPOINT_URL")
S3_ACCESS_KEY_ID = os.getenv("S3_ACCESS_KEY_ID")
S3_SECRET_ACCESS_KEY = os.getenv("S3_SECRET_ACCESS_KEY")
S3_REGION = os.getenv("S3_REGION")
S3_BUCKET = "dlhybride"

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
# 3. Lecture CSV depuis S3
# ---------------------------
def load_csv_from_s3(file_name, bucket_name=S3_BUCKET):
    response = s3_client.get_object(Bucket=bucket_name, Key=file_name)
    df = pd.read_csv(io.BytesIO(response["Body"].read()), dtype=str)
    return df

df_jobs = load_csv_from_s3("df_competence_rome_eda_v2.csv")
df_jobs["code_ogr_competence"] = df_jobs["code_ogr_competence"].astype(str)

# ---------------------------
# 4. Construction des mappings
# ---------------------------
skills_vocab = {code: idx for idx, code in enumerate(df_jobs['code_ogr_competence'].unique())}
skill_to_label = df_jobs.drop_duplicates('code_ogr_competence') \
                        .set_index('code_ogr_competence')['libelle_competence'].to_dict()
jobs_vocab = {rome: idx for idx, rome in enumerate(df_jobs['code_rome'].unique())}
job_labels = df_jobs.drop_duplicates('code_rome').set_index('code_rome')['libelle_rome'].to_dict()
job_to_skills = df_jobs.groupby('code_rome')['code_ogr_competence'].apply(set).to_dict()

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")


# ---------------------------
# 5. Charger modèle depuis S3 avec dill
# ---------------------------
def load_model_from_s3_with_dill(key):
    obj = s3_client.get_object(Bucket=S3_BUCKET, Key=key)
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pkl") as tmp_file:
        tmp_file.write(obj['Body'].read())
        tmp_model_path = tmp_file.name

    # Charger le modèle avec dill
    with open(tmp_model_path, "rb") as f:
        model_loaded = dill.load(f)

    model_loaded.to(device)
    model_loaded.eval()
    return model_loaded

model_loaded = load_model_from_s3_with_dill("modele_epoch4001.pkl")

# ---------------------------
# 6. FastAPI
# ---------------------------
app = FastAPI(title="JobProfile API", version="1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ProfileInput(BaseModel):
    skills: List[str]

# ---------------------------
# 7. Fonction de prédiction hybride
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
# 8. Endpoints
# ---------------------------
@app.get("/")
def read_root():
    return {"message": "API JobProfileTransformer opérationnelle"}

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
