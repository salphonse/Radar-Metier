
# ---------------------------
# Init des variables
# ---------------------------
from dotenv import load_dotenv, find_dotenv
import os

# Localiser et recharger le .env
dotenv_path = find_dotenv("../script/settings/.env")  # trouve le .env dans ton projet
load_dotenv(dotenv_path, override=True)  # override=True force le remplacement

bucket_name = "dlhybride"
db_schema = 'radarmetier'

# ---------------------------
# DB Connection
# ---------------------------
from sqlalchemy import create_engine
import pandas as pd

df_competence = pd.DataFrame()

def df_from_table(table_name):
    global db_schema

    url = f"postgresql+psycopg2://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}"
    if len(os.getenv('DB_PORT')) > 0:
        url += f":{os.getenv('DB_PORT')}"
    if len(os.getenv("DB_NAME")) > 0:
        url += f"/{os.getenv("DB_NAME")}"
    if __debug__:
        print("URL=", url)
        print("DB table:", table_name)
        print("DB schema:", db_schema)
    try:
        engine = create_engine(url)
        with engine.connect() as conn, conn.begin():

            data_frame = pd.read_sql_table(table_name, con= conn, schema= db_schema)
            print(f"Data read from DB: {data_frame.shape}")
            return data_frame
    except Exception as e:
        print(e)
    return any



# ---------------------------
# 2. Connexion à Supabase (S3-compatible)
# ---------------------------
import boto3

# Initialisation client S3
s3_client = boto3.client( 
    service_name='s3',                                      # Type de service : S3
    region_name=os.getenv("S3_REGION"),                     # Région où le bucket est hébergé
    endpoint_url=os.getenv("S3_ENDPOINT_URL"),              # Endpoint S3 (Supabase spécifique)
    aws_access_key_id=os.getenv("S3_ACCESS_KEY_ID"),        # Clé d'accès S3
    aws_secret_access_key=os.getenv("S3_SECRET_ACCESS_KEY") # Secret S3
)

# ---------------------------
# Chargement du modèle
# ---------------------------

from pydantic import BaseModel
import joblib

# model = joblib.load('house_price_model.pkl')

# ---------------------------
# API
# ---------------------------
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import numpy as np
# #from fastapi.staticfiles import StaticFiles
# from fastapi import Request
# from fastapi.responses import HTMLResponse
# from fastapi.templating import Jinja2Templates


# Définition du schéma de données
# class CaliforniaHousePrice(BaseModel):
#     medInc: float
#     houseAge: float
#     aveRooms: float
#     aveBedrms: float
#     population: float
#     aveOccup: float
#     latitude: float
#     longitude: float

class Competence(BaseModel):
    competence: str
    macro_competence: str
    domaine_competence: str

# Initialisation de l'application fastapi
app = FastAPI(
    title="House Pricing API",
    description="API de prédiction de prix immobilier",
    version="1.0.0"
)

# Configuration CORS - SOLUTION PRINCIPALE
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En production, spécifiez les domaines autorisés
    allow_credentials=True,
    allow_methods=["*"],  # Ou spécifiez ["GET", "POST"]
    allow_headers=["*"],  # Ou spécifiez ["Content-Type", "Accept"]
)

@app.get("/init")
def init_data():
    global df_competence
    df_competence = df_from_table("rome_arborescence_competences")
    print(f"Init(): DF competence: {df_competence.shape}")
    return {"status":"ready" if df_competence.shape[0] > 0 else "error"}

# Liste des domaines de compétences
@app.post("/get_domaine_competence")
def get_domaine_competence():
    global df_competence
    if df_competence.shape[0] == 0:
        init_data()
    domaine = df_competence['domaine_competence'].unique()
    print(f"Nb domaine competence: {len(domaine)}")
    return {'liste_domaine': domaine.tolist()}

# Liste des macro-compétences par domaine
@app.post("/get_macro_competence")
def get_macro_competence(competence: Competence):
    global df_competence
    if df_competence.shape[0] == 0:
        init_data()
    df_macro = df_competence.loc[df_competence['domaine_competence'] == competence.domaine_competence][['libelle_macro_competence']]
    print(f"Nb macro competence: {df_macro.shape}")
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

# @app.post("/predict")
# def predict_prices(house_data: CaliforniaHousePrice):
#     data = np.array([house_data.medInc,
#                      house_data.houseAge,
#                      house_data.aveRooms,
#                      house_data.aveBedrms,
#                      house_data.population,
#                      house_data.aveOccup,
#                      house_data.latitude,
#                      house_data.longitude
#                 ]).reshape(1, -1)

#     # Prediction
#     prediction = model.predict(data)

#     return {"prediction":float(prediction[0]*100000)}

# Endpoint pour vérifier la santé de l'API
@app.get("/health")
async def health_check():
    return {"status": "healthy", "message": "API is working correctly"}