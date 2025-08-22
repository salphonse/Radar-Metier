import psycopg2
from dotenv import load_dotenv
import pandas as pd
import os, fnmatch
from sqlalchemy import create_engine

# Load environment variables with specific location for EDI (PyCharm/VSCode)
if not load_dotenv('../settings/.env'):
    load_dotenv('script/settings/.env')

# Database global variables
db_schema = 'public' # set to 'public' by default
db_connection = None
db_cursor = None
table_prefix = 'rome_'

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

def init_db():
    global db_connection
    global db_cursor
    global db_schema

    if len(os.getenv('DB_SCHEMA')) > 0:
        db_schema = os.getenv("DB_SCHEMA")

    # Create schema if not exists

    # CREATE SCHEMA IF NOT EXISTS radarmetier;
    # -- Select default schema
    # SET search_path TO radarmetier;
    # -- Set default date format
    # SET datestyle = 'ISO, DMY';


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

def save_csv_file(dest_file, data_frame):
    # Sauvegarder le résultat dans un fichier csv
    data_frame.to_csv(dest_file)
    print("Chargement des données dans le fichier CSV: ok")

def set_current_file(csv_file):
        global current_file_path
        global current_file_name

        current_file_path = os.path.join(data_path, csv_file)
        try:
            # Remove 'unix_' at beginning and '_v458_utf8.csv' at the end of file name
            current_file_name = csv_file.split('unix_', 1)[1].rsplit('_v', 1)[0] # 'unix_domaine_professionnel_v458_utf8.csv'
            #print("current_file_name:", current_file_name)
        except Exception as e:
            current_file_name = ''
            print(e)


def extract(src_file):
    try:
        print("Extract UTF8 data from file:", src_file)
        data_frame = pd.read_csv(src_file, encoding='utf-8')
        return data_frame
    except Exception as e:
        print(e)
        try:
            print("Extract ANSI data from file:", src_file)
            data_frame = pd.read_csv(src_file, encoding='windows-1252')
            print("Récupération des données depuis le fichier terminée!")
            return data_frame
        except Exception as e:
            print(e)
            
    return None


def transform(data_frame):
    # Conserver les colonnes voulues
    return data_frame


def load(data_frame):
    global data_path
    global current_file_name
    global current_file_path

    dest_file = os.path.join(data_path, 'output', current_file_name + '.csv')

    try:
        os.mkdir(os.path.join(data_path, 'output'))
    except OSError as error:
        if error.errno == 17:
            pass # Do nothing for this error
        else:
            print(error)

    #save_csv_file(dest_file, data_frame)

    insert_db_data(current_file_name, data_frame)


def main():
    global current_file_path
    global current_file_name

    print("--- Insert ROME data ---")

    # Init database connection and cursor
    if init_db():
        # Liste des fichiers à intégrer dans la base de données
        file_list = [
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

        # List all CSV files from ROME folder
        for csv_file in fnmatch.filter(os.listdir(data_path), '*.csv'):
            print("Read file:", csv_file)
            set_current_file(csv_file)

            if current_file_name in file_list:
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
