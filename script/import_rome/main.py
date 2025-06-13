import psycopg2
from dotenv import load_dotenv
import pandas as pd
import os, fnmatch
from sqlalchemy import create_engine

# Load environment variables 
if not load_dotenv('settings/.env'):
    load_dotenv('script/import_rome/settings/.env')

# Check settings (for debug session only)
print("Env:", os.getenv("DB_HOST"),
    os.getenv("DB_PORT"),
    'crypto_db',
    os.getenv("DB_USER"),
    os.getenv("DB_PASSWORD"))

# Database global variables
db_name = "radarmetier"
db_schema = "radarmetier"
db_connection = None
db_cursor = None
table_prefix = 'rome_'

# File global variables
data_path = "/Users/stephane/Documents/Formation - Data 0325/Projet fil rouge/Data/Code ROME/RefRomeCsv/"
current_file_name = ""
current_file_path = ""

def init_db():
    global db_connection
    global db_cursor

    # Connect to an existing database
    try:
        db_connection = psycopg2.connect(
            host=os.getenv("DB_HOST"),
            port=os.getenv("DB_PORT"),
            database='crypto_db',
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
    engine = create_engine(f"postgresql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}:{os.getenv('DB_PORT')}/{db_name}")
    try:
        data_frame.to_sql(table_name, engine, if_exists='replace', index=False)
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
        # Remove 'unix_' at start and '_v458_utf8.csv' at the end of file name
        current_file_name = csv_file.split('unix_', 1)[1].rsplit('_v', 1)[0] # 'unix_domaine_professionnel_v458_utf8.csv'
        #print("current_file_name:", current_file_name)


def extract(src_file):
    try:
        print("Extract data from file:", src_file)
        data_frame = pd.read_csv(src_file, encoding='utf-8')
        return data_frame
    except Exception as e:
        print(e)
        try:
            print("Extract data from file:", src_file)
            data_frame = pd.read_csv(src_file, encoding='windows-1250')
            print("Récupération des données depuis le fichier terminée!")
            return data_frame
        except Exception as e:
            print(e)
            
    return None


def transform(data_frame):
    # Concerver les colonnes voulues
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

    save_csv_file(dest_file, data_frame)

    insert_db_data(current_file_name, data_frame)


def main():
    global current_file_path
    global current_file_name

    print("--- Insert ROME data ---")

    # Init database connection and cursor
    if init_db():

        file_list = [
            'grand_domaine',
            'domaine_professionnel',
            'referentiel_appellation',
            'texte',
            'rubrique_mobilite',
            'centre_interet',
            'arborescence_centre_interet',
            'referentiel_code_rome',
            'referentiel_competence',
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
