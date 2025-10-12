import psycopg2
from dotenv import load_dotenv, find_dotenv
import pandas as pd
import io
import os
import boto3
from sqlalchemy import create_engine

# =================================================================================
# 1. Configuration & Globals
# =================================================================================
# Load environment variables
load_dotenv(find_dotenv('settings/.env'))

# Database global variables
db_schema = 'public' # set to 'public' by default
db_connection = None
db_cursor = None
table_prefix = 'rome_'

S3_ENDPOINT_URL = os.getenv("S3_ENDPOINT_URL")
S3_ACCESS_KEY_ID = os.getenv("S3_ACCESS_KEY_ID")
S3_SECRET_ACCESS_KEY = os.getenv("S3_SECRET_ACCESS_KEY")
S3_REGION = os.getenv("S3_REGION")
S3_BUCKET = "raw-data"

# Check settings (for debug session only)
if __debug__:
    print('Debug ON')
    print("Environment data:", 
        "\nHost:", os.getenv("DB_HOST"),
        "\nPort:", os.getenv("DB_PORT"),
        "\nDB name:", os.getenv("DB_NAME"),
        "\nUser:", os.getenv("DB_USER"),
        "\nPass:", "******", # os.getenv("DB_PASSWORD"),
        "\nSchema:", os.getenv("DB_SCHEMA")
        )

# File global variables
data_path = "/Users/stephane/Documents/Formation - Data 0325/Projet fil rouge/Data/Code ROME/RefRomeCsv/"
current_file_name = ""
current_file_path = ""


# =================================================================================
# 2. Connexion S3
# =================================================================================

s3_client = boto3.client(
    service_name="s3",
    region_name=S3_REGION,
    endpoint_url=S3_ENDPOINT_URL,
    aws_access_key_id=S3_ACCESS_KEY_ID,
    aws_secret_access_key=S3_SECRET_ACCESS_KEY,
)

# =================================================================================
# 3. Chargement des données
# =================================================================================

def read_csv_from_s3(file_path: str, bucket_name: str = S3_BUCKET) -> pd.DataFrame:
    """Charge un CSV depuis un bucket S3 dans un DataFrame pandas."""
    response = s3_client.get_object(Bucket=bucket_name, Key=file_path)
    try:
        return pd.read_csv(io.BytesIO(response["Body"].read()), dtype=str)
    except Exception:
        return pd.DataFrame()


import psycopg2
from dotenv import load_dotenv
import pandas as pd
import io
import os, fnmatch
import boto3
from sqlalchemy import create_engine

# =================================================================================
# 1. Configuration & Globals
# =================================================================================
# Load environment variables with specific location for EDI (PyCharm/VSCode)
if not load_dotenv('../../settings/.env'):
    load_dotenv('settings/.env')

# Database global variables
db_schema = 'public' # set to 'public' by default
db_connection = None
db_cursor = None
table_prefix = 'rome_'

S3_ENDPOINT_URL = os.getenv("S3_ENDPOINT_URL")
S3_ACCESS_KEY_ID = os.getenv("S3_ACCESS_KEY_ID")
S3_SECRET_ACCESS_KEY = os.getenv("S3_SECRET_ACCESS_KEY")
S3_REGION = os.getenv("S3_REGION")
S3_BUCKET = "raw-data"

S3_ROME_FOLDER = "CodeROME/RefRomeCsv"

# Check settings (for debug session only)
if __debug__:
    print('Debug ON')
    print("Environment data:", 
        "\nHost:", os.getenv("DB_HOST"),
        "\nPort:", os.getenv("DB_PORT"),
        "\nDB name:", os.getenv("DB_NAME"),
        "\nUser:", os.getenv("DB_USER"),
        "\nPass:", "******", # os.getenv("DB_PASSWORD"),
        "\nSchema:", os.getenv("DB_SCHEMA")
        )

# File global variables
data_path = S3_ROME_FOLDER
current_file_name = ""
current_file_path = ""

# =================================================================================
# 2. Connexion S3
# =================================================================================

s3_client = boto3.client(
    service_name="s3",
    region_name=S3_REGION,
    endpoint_url=S3_ENDPOINT_URL,
    aws_access_key_id=S3_ACCESS_KEY_ID,
    aws_secret_access_key=S3_SECRET_ACCESS_KEY,
)

# =================================================================================
# 3. Déclaration des fonctions d'accès au S3
# =================================================================================

def read_csv_from_s3(file_path: str, bucket_name: str = S3_BUCKET, encoding:str ='utf-8') -> pd.DataFrame:
    """Charge un CSV depuis un bucket S3 dans un DataFrame pandas."""
    response = s3_client.get_object(Bucket=bucket_name, Key=file_path)
    return pd.read_csv(io.BytesIO(response["Body"].read()), dtype=str, encoding=encoding)
    # try:
    #     return pd.read_csv(io.BytesIO(response["Body"].read()), dtype=str, encoding=encoding)
    # except Exception:
    #     return pd.DataFrame()

def list_bucket_file(Bucket: str, Folder: str, Ext:str = None) -> list: 
    response = s3_client.list_objects_v2(Bucket= Bucket, Prefix= Folder)
    file_list = []
    for obj in response["Contents"]:
        key = obj["Key"]
        if Ext is None or key.lower().endswith(Ext):
            file_list.append(key.split("/")[-1])
    return file_list


def set_current_file(csv_file):
    global current_file_path
    global current_file_name

    current_file_path = os.path.join(data_path, csv_file)
    if __debug__:
        print("Current file path is now:", current_file_path)
    try:
        # Remove 'unix_' at beginning and '_v4xx_utf8.csv' at the end of file name
        current_file_name = csv_file.split('unix_', 1)[1].rsplit('_v', 1)[0] # 'unix_domaine_professionnel_v458_utf8.csv'
    except Exception as e:
        current_file_name = ''
        print(e)

#df_test = read_csv_from_s3("CodeROME/RefRomeCsv/unix_arborescence_centre_interet_v459_utf8.csv")
print("Test lecture - Nb fichiers=", len(list_bucket_file(S3_BUCKET, S3_ROME_FOLDER, ".csv")))

# =================================================================================
# 4. Déclaration des fonctions d'accès à la DB
# =================================================================================
def init_db():
    global db_connection
    global db_cursor
    global db_schema

    if os.getenv('DB_SCHEMA') is not None and len(os.getenv('DB_SCHEMA')) > 0:
        db_schema = os.getenv("DB_SCHEMA")

    # Connect to an existing database
    try:
        db_connection = psycopg2.connect(
            host=os.getenv("DB_HOST"),
            port=os.getenv("DB_PORT"),
            database=os.getenv("DB_NAME"),
            user=os.getenv("DB_USER"),
            password=os.getenv("DB_PASSWORD"))

    except Exception as e:
        print(e)
        return False

    # Open a cursor to perform database operations
    try:
        db_cursor = db_connection.cursor()
        print("connection and cursor are created")
    except Exception as e:
        print(e)
        return False
    
    return True # Connection success

def insert_db_data(table_name, data_frame):
    global db_schema

    url = f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}"
    if len(os.getenv('DB_PORT')) > 0:
        url += f":{os.getenv('DB_PORT')}"
    if len(os.getenv("DB_NAME")) > 0:
        url += f"/{os.getenv("DB_NAME")}"
    if __debug__:
        print("URL=", url)
        print("DB table:", table_name)
    try:
        engine = create_engine(url)
        data_frame.to_sql(table_name, engine, schema=db_schema, if_exists='replace', index=False)
        print("Insertion des données dans la DB: ok")
    except Exception as e:
        print(e)

# =================================================================================
# 5. Déclaration des fonctions ETL
# =================================================================================

def extract(src_file):
    try:
        print("Extract UTF8 data from file:", src_file)
        #data_frame = pd.read_csv(src_file, encoding='utf-8')
        data_frame = read_csv_from_s3(src_file, encoding='utf-8')
        return data_frame
    except Exception as e:
        print(e)
        try:
            print("Extract ANSI data from file:", src_file)
            #data_frame = pd.read_csv(src_file, encoding='windows-1252')
            data_frame = read_csv_from_s3(src_file, encoding='windows-1252')
            return data_frame
        except Exception as e:
            print(e)
            
    return None


def transform(data_frame):
    # Conserver les colonnes voulues
    return data_frame


def load(data_frame):
    global current_file_name
    
    insert_db_data(current_file_name, data_frame)


# =================================================================================
# 4. Déclaration de la fonction principale
# =================================================================================
def main():
    global current_file_path
    global current_file_name

    print("--- Insert ROME data ---")

    # Init database connection and cursor
    if init_db():
        # Liste des fichiers à intégrer dans la base de données
        load_file_list = [
            'grand_domaine',
            'domaine_professionnel',
            'referentiel_appellation',
            'texte',
            'rubrique_mobilite',
            'centre_interet',
            'arborescence_centre_interet',
            'arborescence_competences',
            'referentiel_code_rome',
            'referentiel_competence',
            'referentiel_savoir',
            'coherence_item',
            'item',
            'descriptif_rubrique']

        bucket_file_list = list_bucket_file(S3_BUCKET, S3_ROME_FOLDER, ".csv")
        
        # List all CSV files from ROME folder
        for csv_file in bucket_file_list:
            print("Read file:", csv_file)
            set_current_file(csv_file)

            if current_file_name in load_file_list:
                current_file_name = table_prefix + current_file_name # Add prefix
                # Extract
                data_frame = extract(current_file_path)
                if data_frame is None:
                    print("Error during extract statement")
                    break

                # Transform
                data_frame = transform(data_frame)
                if data_frame is None:
                    print("Error during transform statement")
                    break

                #Load
                load(data_frame)
                if data_frame is None:
                    print("Error during load statement")
                    break
            else:
                print(f"File '{current_file_name}' is exclude")

    # Close database cursor and connection
    if db_cursor is not None:
        db_cursor.close()
    if db_connection is not None:
        db_connection.close()


if __name__ == "__main__":
    main()

# =================================================================================
# End
# =================================================================================
