import os
import requests
import zipfile
import psycopg2
from io import BytesIO
import csv
import tempfile
import shutil

# Database configuration
DB_CONFIG = {
    'dbname': os.getenv('POSTGRES_DB'),
    'user': os.getenv('POSTGRES_USER'),
    'password': os.getenv('POSTGRES_PASSWORD'),
    'host': os.getenv('POSTGRES_HOST', 'localhost'),
    'port': 5432
}

tables = {
    'members': ['CoachExport.csv', {
        'NAF Nr': 'naf_number',
        'NAF name': 'naf_name',
        'Country': 'country',
        'Registration Date': 'registration_date',
        'Expiry Date': 'expiry_date'
    }],
    'variants': ['naf_variants.csv', {
        'variantid': 'variantid',
        'variantname': 'variantname',
        'order': 'variantorder'
    }],
    'races': ['naf_race.csv', {
        'raceid': 'raceid',
        'name': 'name',
        'reroll_cost': 'reroll_cost',
        'apoth': 'apoth',
        'order': 'race_order',
        'selectable': 'selectable',
        'race_count': 'race_count'
    }],
    'awards': ['naf_tournament_statistics_list.csv', {
        'id': 'id',
        'name': 'name',
        'label': 'label',
        'order': 'award_order'
    }],
    'tournaments': ['naf_tournament.csv', {
        'tournamentid': 'tournamentid',
        'tournamentorganizerid': 'tournamentorganizerid',
        'tournamentname': 'tournamentname',
        'tournamentaddress1': 'tournamentaddress1',
        'tournamentaddress2': 'tournamentaddress2',
        'tournamentcity': 'tournamentcity',
        'tournamentstate': 'tournamentstate',
        'tournamentzip': 'tournamentzip',
        'tournamentnation': 'tournamentnation',
        'tournamenturl': 'tournamenturl',
        'tournamentnotesurl': 'tournamentnotesurl',
        'tournamentstartdate': 'tournamentstartdate',
        'tournamentenddate': 'tournamentenddate',
        'tournamenttype': 'tournamenttype',
        'tournamentstyle': 'tournamentstyle',
        'tournamentscoring': 'tournamentscoring',
        'tournamentcost': 'tournamentcost',
        'tournamentnaffee': 'tournamentnaffee',
        'tournamentnafdiscount': 'tournamentnafdiscount',
        'tournamentinformation': 'tournamentinformation',
        'tournamentcontact': 'tournamentcontact',
        'tournamentemail': 'tournamentemail',
        'tournamentorg': 'tournamentorg',
        'tournamentstatus': 'tournamentstatus',
        'tournamentmajor': 'tournamentmajor',
        'geolongitude': 'geolongitude',
        'geolattitude': 'geolattitude',
        'tournamentreport': 'tournamentreport',
        'subscription_closed': 'subscription_closed',
        'naf_rulesetid': 'rulesetid',
        'naf_variantsid': 'variantsid',
        'variant_notes': 'variant_notes',
        'variantstatus': 'variantstatus',
        'tournament_ruleset_file': 'tournament_ruleset_file'
    }],
    'tournament_statistics': ['naf_tournament_statistics_group.csv', {
        'typeID': 'typeid',
        'tournamentID': 'tournamentid',
        'coachID': 'coachid',
        'raceID': 'raceid',
        'notes': 'notes',
        'date': 'date'
    }],
    'tournament_coaches': ['naf_tournamentcoach.csv', {
        'tournamentid': 'tournamentid',
        'coachid': 'coachid',
        'raceid': 'raceid'
    }],
    'games': ['naf_game.csv', {
        'gameid': 'gameid',
        'seasonid': 'seasonid',
        'tournamentid': 'tournamentid',
        'homecoachid': 'homecoachid',
        'awaycoachid': 'awaycoachid',
        'racehome': 'racehome',
        'raceaway': 'raceaway',
        'trhome': 'trhome',
        'traway': 'traway',
        'rephome': 'rephome',
        'repaway': 'repaway',
        'rephome_calibrated': 'rephome_calibrated',
        'repaway_calibrated': 'repaway_calibrated',
        'dirty_calibrated': 'dirty_calibrated',
        'goalshome': 'goalshome',
        'goalsaway': 'goalsaway',
        'badlyhurthome': 'badlyhurthome',
        'badlyhurtaway': 'badlyhurtaway',
        'serioushome': 'serioushome',
        'seriousaway': 'seriousaway',
        'killshome': 'killshome',
        'killsaway': 'killsaway',
        'gate': 'gate',
        'winningshome': 'winningshome',
        'winningsaway': 'winningsaway',
        'notes': 'notes',
        'date': 'date',
        'dirty': 'dirty',
        'hour': 'hour',
        'newdate': 'newdate',
        'naf_variantsid': 'variantsid'
    }],
    'coach_ranking_variant': ['naf_coachranking_variant.csv', {
        'coachID': 'coachid',
        'raceID': 'raceid',
        'variantID': 'variantid',
        'dateUpdate': 'dateupdate',
        'ranking': 'ranking',
        'ranking_temp': 'ranking_temp'
    }],
    'tournament_coaches': ['naf_tournamentcoach.csv', {
        'naftournament': 'tournamentid',
        'nafcoach': 'coachid',
        'race': 'raceid'
    }]
}
# File URL
FILE_URL = os.getenv('FILE_URL', "https://member.thenaf.net/glicko/nafstat-tmp-name.zip")
DOWNLOAD_DIR = os.getenv('DOWNLOAD_DIR', '/tmp')
EXTRACT_DIR = os.getenv('EXTRACT_DIR', "/tmp/nafstat")

def get_missing_naf_numbers():
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()
    cursor.execute("SELECT MIN(naf_number), MAX(naf_number) FROM members;")
    min_naf, max_naf = cursor.fetchone()
    cursor.execute("SELECT naf_number FROM members;")
    existing_numbers = {row[0] for row in cursor.fetchall()}
    missing_numbers = [num for num in range(min_naf, max_naf + 1) if num not in existing_numbers]
    cursor.close()
    conn.close()
    return missing_numbers

def download_file(url, download_path):
    with requests.Session() as session:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate, br",
            "Connection": "keep-alive",
        }
        response = session.get(url, headers=headers, stream=True)
        response.raise_for_status()
        with open(download_path, 'wb') as file:
            for chunk in response.iter_content(chunk_size=8192):
              file.write(chunk)
    print(f"File downloaded to {download_path}")

def extract_zip(file_path, extract_to):
    with zipfile.ZipFile(file_path, 'r') as zip_ref:
        zip_ref.extractall(extract_to)
    print(f"File extracted to {extract_to}")

def import_to_postgres(file_path, table_name, column_mapping):
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()
    with open(file_path, 'r') as file:
        # Replace headers in the CSV with the corresponding columns in the mapping
        reader = csv.DictReader(file, delimiter=';')
        temp_file = tempfile.NamedTemporaryFile(delete=False, mode='w', newline='')
        writer = csv.DictWriter(temp_file, fieldnames=column_mapping.values())
        writer.writeheader()

        for row in reader:
            mapped_row = {column_mapping.get(key, key): (None if value.startswith('0000-00-00') else value) for key, value in row.items()}
            writer.writerow(mapped_row)

        temp_file.close()
        file.close()

        # Reopen the temporary file for the copy operation
        file = open(temp_file.name, 'r')
        cursor.copy_expert(f"COPY {table_name} FROM STDIN WITH CSV HEADER", file)
        
    conn.commit()
    print(f"Data imported to table {table_name}")
    if table_name == 'members':
        missing_naf_numbers = get_missing_naf_numbers()
        if missing_naf_numbers:
            for naf_number in missing_naf_numbers:
                cursor.execute("""
                    INSERT INTO members (naf_number, naf_name, country, registration_date)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT (naf_number) DO NOTHING;
                """, (naf_number, "Deleted", "Deleted", "2000-01-01"))
            conn.commit()
    cursor.close()
    conn.close()            

def main():
    # Remove the extract directory if it exists
    if os.path.exists(EXTRACT_DIR):
        shutil.rmtree(EXTRACT_DIR)
    # Remove the zip file if it exists
    zip_path = os.path.join(DOWNLOAD_DIR, "nafstat.zip")
    if os.path.exists(zip_path):
        os.remove(zip_path)
    if os.path.exists(EXTRACT_DIR):
        shutil.rmtree(EXTRACT_DIR)
    os.makedirs(EXTRACT_DIR, exist_ok=True)
    zip_path = os.path.join(DOWNLOAD_DIR, "nafstat.zip")
    
    # Step 1: Download the file
    download_file(FILE_URL, zip_path)
    
    # Step 2: Extract the file
    extract_zip(zip_path, EXTRACT_DIR)
    # List the contents of the extracted directory
    folder = os.listdir(EXTRACT_DIR)
    print(f"Extracted files: {folder}")
    # Step 2.5: Delete all data from the database tables
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()
    for table in tables.keys():
        cursor.execute(f"TRUNCATE TABLE {table} CASCADE;")
    conn.commit()
    cursor.close()
    conn.close()
    print("All data deleted from the database.")
    # Step 2.6: Insert default values into the races and variants tables
    conn = psycopg2.connect(**DB_CONFIG)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO races (raceid, name, reroll_cost, apoth, race_order, selectable, race_count)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (raceid) DO NOTHING;
    """, ("0", "Unknown", "0", "n", "6", None, "no"))
    
    cursor.execute("""
        INSERT INTO variants (variantid, variantname, variantorder)
        VALUES (%s, %s, %s)
        ON CONFLICT (variantid) DO NOTHING;
    """, ("6", "Deleted", "9998"))
    cursor.execute("""
        INSERT INTO variants (variantid, variantname, variantorder)
        VALUES (%s, %s, %s)
        ON CONFLICT (variantid) DO NOTHING;
    """, ("0", "Unknown", "9999"))
    conn.commit()
    cursor.close()
    conn.close()
    print("Default values inserted into the races table.")
    # Step 3: Import the extracted fileo the database
    for table, path in tables.items():
        print(f"Importing {path[0]} to {table}")
        csv_file_path = os.path.join(EXTRACT_DIR, folder[-1], path[0])
        import_to_postgres(csv_file_path, table, column_mapping=path[1])
        

if __name__ == "__main__":
    main()