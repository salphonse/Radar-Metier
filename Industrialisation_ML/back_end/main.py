# main.py
import pandas as pd
import joblib
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from dotenv import load_dotenv, find_dotenv
import os, io, pandas as pd, joblib, boto3
from sqlalchemy import create_engine
from typing import List
import numpy as np
from scipy.sparse import csr_matrix
from sklearn.preprocessing import normalize



# ---------------------------
# Variables d'environnement
# ---------------------------
load_dotenv(find_dotenv(".env"), override=True)
DB_SCHEMA = 'radarmetier'

S3_BUCKET = "ML"
S3_KEY = "metiers_comp.joblib"
S3_ENDPOINT_URL = os.getenv("S3_ENDPOINT_URL")
S3_ACCESS_KEY_ID = os.getenv("S3_ACCESS_KEY_ID")
S3_SECRET_ACCESS_KEY = os.getenv("S3_SECRET_ACCESS_KEY")
S3_REGION = os.getenv("S3_REGION")

# ---------------------------
# Connexion S3 et chargement du modèle
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


# ---------------------------
# Artefacts
# ---------------------------

MIN_SKILLS = 3
THRESHOLD  = 0.30

X       = bundle["X"]
roms    = bundle["roms"]
comp2j  = {str(k): v for k, v in bundle["comp2j"].items()}
rom_lbl = bundle.get("rom_lbl", {})
comp_lbl= bundle.get("comp_lbl", {})

# ---------------------------
# Connexion DB
# ---------------------------
def df_from_query(query: str) -> pd.DataFrame:
    url = f"postgresql+psycopg2://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}"
    if os.getenv('DB_PORT'):
        url += f":{os.getenv('DB_PORT')}"
    if os.getenv("DB_NAME"):
        url += f"/{os.getenv('DB_NAME')}"

    try:
        engine = create_engine(url)
        with engine.connect() as conn, conn.begin():
            df = pd.read_sql_query(query, con=conn)
            print(f"Data read from DB: {df.shape}")
            return df
    except Exception as e:
        print(f"Erreur SQL: {e}")
        return pd.DataFrame()

# ---------------------------
# Chargement df_competence
# ---------------------------
df_competence = pd.DataFrame()

def load_df_competence():
    global df_competence
    query = """
    SELECT arb.code_domaine_competence,
           arb.domaine_competence,
           arb.code_macro_competence,
           arb.libelle_macro_competence,
           arb.code_ogr_competence,
           arb.libelle_competence,
           coh.code_rome,
           ref.libelle_rome
    FROM radarmetier.rome_arborescence_competences AS arb
    INNER JOIN radarmetier.rome_coherence_item AS coh
        ON arb.code_ogr_competence = coh.code_ogr
    INNER JOIN radarmetier.rome_referentiel_code_rome AS ref
        ON coh.code_rome = ref.code_rome;
    """
    df = df_from_query(query)

    # Nettoyage : convertir en str, enlever .0 éventuels et espaces
    df['code_ogr_competence'] = (
        df['code_ogr_competence']
        .fillna('')
        .astype(str)
        .str.replace('.0', '', regex=False)
        .str.strip()
    )

    # Garder seulement les compétences présentes dans le modèle
    df_competence = df[df['code_ogr_competence'].isin(comp2j.keys())].drop_duplicates(subset='code_ogr_competence')

    print(f"df_competence chargé et filtré: {df_competence.shape}")
    print("Exemple codes filtrés:", df_competence['code_ogr_competence'].tolist()[:10])
    
    return df_competence


# ---------------------------
# FastAPI App
# ---------------------------
app = FastAPI(title="JobProfile ML API", version="1.0")

origins = [
    "http://localhost:5500",
    "https://radar-metier-zh10.onrender.com/"   # Ajoutez d'autres origines autorisées si nécessaire
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



@app.on_event("startup")
def startup_event():
    load_df_competence()

# ---------------------------
# Pydantic Models
# ---------------------------
class Competence(BaseModel):
    competence: str | None = None
    macro_competence: str | None = None
    domaine_competence: str | None = None

class SkillsRequest(BaseModel):
    skills: List[str]

# ---------------------------
# Endpoints
# ---------------------------
@app.get("/init")
def init_data():
    load_df_competence()
    if df_competence.empty:
        return {"status": "error", "message": "DataFrame vide"}
    return {"status": "ready", "message": f"{df_competence.shape[0]} lignes chargées"}

@app.post("/get_domaine_competence")
def get_domaine_competence():
    if df_competence.empty:
        load_df_competence()
    return {"status": "success", "liste_domaine": sorted(df_competence["domaine_competence"].unique())}

@app.post("/get_macro_competence")
def get_macro_competence(competence: Competence):
    if df_competence.empty:
        load_df_competence()
    df_macro = df_competence[df_competence["domaine_competence"] == competence.domaine_competence]
    return {"status": "success", "liste_macro_competence": sorted(df_macro["libelle_macro_competence"].unique())}

@app.post("/get_competence")
def get_competence(competence: Competence):
    # 1. Filtrer par macro-compétence
    df_comp = df_competence.loc[
        df_competence['libelle_macro_competence'] == competence.macro_competence,
        ['libelle_competence', 'code_ogr_competence']
    ].copy()

    # 2. Nettoyer les codes pour correspondre au modèle
    df_comp['code_ogr_competence'] = (
        df_comp['code_ogr_competence']
        .astype(str)
        .str.replace('.0', '', regex=False)
        .str.strip()
    )

    # 3. Garder uniquement celles présentes dans le modèle ML
    df_comp = df_comp[df_comp['code_ogr_competence'].isin(comp2j.keys())]

    # 4. Supprimer les doublons et trier
    df_comp = df_comp.drop_duplicates(subset='code_ogr_competence').sort_values('libelle_competence')

    # 5. Transformer pour le front
    liste_competences = [
        {"code": row['code_ogr_competence'], "libelle": row['libelle_competence']}
        for _, row in df_comp.iterrows()
    ]

    print(f"[GET_COMPETENCE] Macro: {competence.macro_competence} -> {len(liste_competences)} compétences valides")
    return {"liste_competence": liste_competences}


# ---------------------------
# Endpoint /predict
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
    input_skills = [{"code": c, "label": comp_lbl.get(str(c).strip(), str(c).strip())} for c in req.skills]
    result = infer_simple_api(req.skills, topk=3)
    result["input_skills"] = input_skills
    return result

# ---------------------------
# Root
# ---------------------------
@app.get("/")
def read_root():
    return {"message": "API opérationnelle"}



"""# Pour debug / test
print("Compétences DB uniques :", df_competence['code_ogr_competence'].nunique())
print("Compétences modèle :", len(comp2j))
print("Intersection :", len(set(df_competence['code_ogr_competence']) & set(comp2j.keys())))

df_test = df_from_query("SELECT * FROM radarmetier.rome_arborescence_competences LIMIT 5;")
print(df_test)
"""

# Exemple debug
#print("Exemple DB:", df_competence['code_ogr_competence'].head(10).tolist())
#print("Exemple modèle:", list(comp2j.keys())[:10])

