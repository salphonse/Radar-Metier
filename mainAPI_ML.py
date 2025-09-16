# main.py
from dotenv import load_dotenv, find_dotenv
import os, io, pandas as pd, joblib, boto3
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from sqlalchemy import create_engine
from typing import List
import numpy as np
from scipy.sparse import csr_matrix
from sklearn.preprocessing import normalize

# ---------------------------
# 1. Variables d'environnement
# ---------------------------
load_dotenv(find_dotenv(".env"), override=True)
db_schema = 'radarmetier'

S3_BUCKET = "ML"
S3_KEY = "metiers_comp.joblib"
S3_ENDPOINT_URL = os.getenv("S3_ENDPOINT_URL")
S3_ACCESS_KEY_ID = os.getenv("S3_ACCESS_KEY_ID")
S3_SECRET_ACCESS_KEY = os.getenv("S3_SECRET_ACCESS_KEY")
S3_REGION = os.getenv("S3_REGION")

# ---------------------------
# 2. Connexion S3 et chargement du modèle
# ---------------------------
print("Connexion S3…")
s3_client = boto3.client(
    service_name="s3",
    region_name=S3_REGION,
    endpoint_url=S3_ENDPOINT_URL,
    aws_access_key_id=S3_ACCESS_KEY_ID,
    aws_secret_access_key=S3_SECRET_ACCESS_KEY,
)

obj = s3_client.get_object(Bucket=S3_BUCKET, Key=S3_KEY)
file_stream = io.BytesIO(obj["Body"].read())
bundle = joblib.load(file_stream)

# Artefacts
X       = bundle["X"]
roms    = bundle["roms"]
comp2j  = {str(k): v for k, v in bundle["comp2j"].items()}  # harmonisation clé str
rom_lbl = bundle.get("rom_lbl", {})
comp_lbl= bundle.get("comp_lbl", {})

MIN_SKILLS = 3
THRESHOLD  = 0.30

# ---------------------------
# 3. Connexion DB
# ---------------------------
def df_from_table(table_name):
    url = f"postgresql+psycopg2://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}"
    if os.getenv('DB_PORT'): url += f":{os.getenv('DB_PORT')}"
    if os.getenv("DB_NAME"): url += f"/{os.getenv('DB_NAME')}"
    try:
        engine = create_engine(url)
        with engine.connect() as conn:
            return pd.read_sql_table(table_name, con=conn, schema=db_schema)
    except Exception as e:
        print(e)
    return pd.DataFrame()

df_competence = pd.DataFrame()

# ---------------------------
# 4. FastAPI
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
# 5. Pydantic Models
# ---------------------------
class Competence(BaseModel):
    competence: str = None
    macro_competence: str = None
    domaine_competence: str = None

class SkillsRequest(BaseModel):
    skills: List[str]

# ---------------------------
# 6. Endpoints compétences (DB)
# ---------------------------
@app.get("/init")
def init_data():
    global df_competence
    df_competence = df_from_table("rome_arborescence_competences")
    return {"status": "ready" if df_competence.shape[0] > 0 else "error"}

@app.post("/get_domaine_competence")
def get_domaine_competence():
    global df_competence
    if df_competence.empty:
        init_data()
    domaines = df_competence['domaine_competence'].unique()
    return {'liste_domaine': domaines.tolist()}

@app.post("/get_macro_competence")
def get_macro_competence(competence: Competence):
    global df_competence
    if df_competence.empty:
        init_data()
    df_macro = df_competence.loc[df_competence['domaine_competence'] == competence.domaine_competence][['libelle_macro_competence']]
    return {'liste_macro_competence': df_macro['libelle_macro_competence'].unique().tolist()}

''' première version
@app.post("/get_competence")
def get_competence(competence: Competence):
    global df_competence
    if df_competence.empty:
        init_data()
    df_comp = df_competence.loc[df_competence['libelle_macro_competence'] == competence.macro_competence][['libelle_competence']]
    return {'liste_competence': df_comp['libelle_competence'].unique().tolist()}
    '''
@app.post("/get_competence")
def get_competence(competence: Competence):
    global df_competence
    if df_competence.empty:
        init_data()

    # Sélectionner les compétences de la macro-compétence
    df_comp = df_competence.loc[
        df_competence['libelle_macro_competence'] == competence.macro_competence,
        ['libelle_competence', 'code_competence']
    ]

    # Filtrer uniquement celles présentes dans comp2j
    df_comp = df_comp[df_comp['code_competence'].astype(str).isin(comp2j.keys())]

    # Retourner la liste enrichie avec les libellés (comp_lbl)
    liste_competences = [
        {"code": str(row['code_competence']), "label": comp_lbl.get(str(row['code_competence']), row['libelle_competence'])}
        for _, row in df_comp.iterrows()
    ]

    return {'liste_competence': liste_competences}


# ---------------------------
# 7. Endpoint jobs (Option B)
# ---------------------------
def infer_simple_api(codes_comp, topk=3):
    codes_comp = [str(c).strip() for c in codes_comp]
    if len(codes_comp) < MIN_SKILLS:
        return {"status":"needs_more_skills","min_required":MIN_SKILLS,"topk":[]}
    
    cols = [comp2j[c] for c in codes_comp if c in comp2j]
    if not cols:
        return {"status":"no_known_skills","topk":[]}

    q = csr_matrix((np.ones(len(cols)), ([0]*len(cols), cols)), shape=(1, X.shape[1]))
    q = normalize(q, norm="l2", axis=1)
    s = (q @ X.T).toarray().ravel()
    order = np.argsort(-s)[:topk]
    preds = [(roms[i], float(s[i])) for i in order]
    top1 = preds[0]

    return {
        "status":"ok" if top1[1] >= THRESHOLD else "indecis",
        "threshold":THRESHOLD,
        "top1":{"code":top1[0],"label":rom_lbl.get(top1[0], top1[0]),"score":top1[1]},
        "topk":[{"code":code,"label":rom_lbl.get(code,code),"score":score} for code,score in preds]
    }

@app.post("/predict")
def predict(req: SkillsRequest):
    input_skills = [
        {"code": c, "label": comp_lbl.get(str(c).strip(), str(c).strip())}
        for c in req.skills
    ]
    result = infer_simple_api(req.skills, topk=3)
    result["input_skills"] = input_skills
    return result
