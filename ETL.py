# Data handling
import pandas
# import dask.dataframe as dd
import psycopg2
import psycopg2.extras
from dateutil.relativedelta import relativedelta
import datetime
import chardet
import csv

# Mainzelliste
import json
import requests


# Config paramters
# Mainzelliste
mainzellisteApiKey = 'MainzelApiKey'
mainzellistePatientPort = '8090'
mainzellisteEventPort = '591'

# PostgreSQL database
db_user = 'postgres'
db_password = 'postgres'
db_host = '127.0.0.1'
db_port = '5432'
db_name = 'clinical'

# Filepath
obrFilepath = "obr.txt"
obxFilepath = "obx.txt"

# txt file encodings
# Leave as empty string for automatic detection
# Examples: 'iso-8859-1' (or latin-1), 'uft-8', 'utf-8-sig', 'cp1252', 'ansi'
# If automatic detection fails set to 'iso-8859-1'
obrEncoding = 'iso-8859-1'
obxEncoding = 'iso-8859-1'

# Allow createn of patients in Mainzelliste with IDs from the obx
# Those patients can not be automatically edited, so reading more obr files is not possible
AllowObxPatientCreation = False

# Turn computation of obr or obx file on/off
obrComputation = False
obxComputation = True


print('\nDEBUG INFORMATION')
# Detect txt file encoding
print('Detect obr encoding:')
with open (obrFilepath, 'rb') as f:
    rawdata = f.read(10000)
    print(rawdata)
    result = chardet.detect(rawdata)
    print(result)
    charenc = result['encoding']

    if not obrEncoding:
        obrEncoding = charenc

print('Detect obr encoding:')
with open (obxFilepath, 'rb') as f:
    rawdata = f.read(10000)
    print(rawdata)
    result = chardet.detect(rawdata)
    print(result)
    charenc = result['encoding']

    if not obxEncoding:
        obxEncoding = charenc

print('Chosen obr encoding: ' + obrEncoding)
print('Chosen obx encoding: ' + obxEncoding)
print('\n')

# Filterlist
# Data that should be filtered out
# List of lists with tuples (like Allowlist)
# Event gets filtered out if ALL conditions in a list of tuples are true
Filter = [[('Category', '8')],
          [('Category', '9')],
          [('Category', '10'), ('Observation_subid', 'Erster')]]

# Allowlist
# List of lists with tuples
# Event gets NOT filtered if ALL conditions in a list of tuples are true
Allow = [[('Observation_id', 'cTheo'), ('Observation_subid', 'CodingSystem')],
         [('Observation_id', 'cTheo'), ('Observation_subid', 'Text')],
         [('Observation_id', 'cTheo'), ('Observation_subid', 'ICPM_Code')],
         [('Observation_id', 'cTheo'), ('Observation_subid', 'TherTyp')],
         [('Observation_id', 'cTheo'), ('Observation_subid', 'TherRang')],
         [('Observation_id', 'cDiag'), ('Observation_subid', 'ICDNr')],
         [('Observation_id', 'cDiag'), ('Observation_subid', 'DiagText')],
         [('Observation_id', 'cDiag'), ('Observation_subid', 'DiagTyp')],
         [('Observation_id', 'cDiag'), ('Observation_subid', 'DiagRang')],
         [('Observation_id', 'cDiag'), ('Observation_subid', 'CodingSystem')]]

########################################################################################################################
# Event table headers with 0:string 1:numerical also in obx
# Order does not madder
# Excludes computed attributes like Event_age as they get inserted on their own
Event = [('Event_id', 0), ('Pat_id', 0), ('Category', 1), ('Value_type_id', 0), ('Observation_id', 0),
         ('Observation_txt', 0), ('Observation_cs', 0), ('Alternative_observation_id', 0),
         ('Alternative_observation_txt', 0), ('Alternative_observation_cs', 0), ('Observation_ts', 0),
         ('Set_id', 0), ('Id_obr', 0), ('Unit_id', 0), ('Unit_txt', 0), ('Unit_cs', 0), ('Reference_range', 0),
         ('Result_status_id', 0), ('Observation_subid', 0)]

# Value table headers
Value = ['Event_id', 'Value']

# List with pseudonyms of edited Mainzelliste patients
# Will be used to update Event_age to use the new IDAT
editPatientPseu = []

########################################################################################################################

# Establishing Mainzelliste session & PostgreSQL database connection
print('\nESTABLISHING CONNECTION TO MAINZELLISTE & DATABASE')
# Mainzelliste Patient
# Set up session to use globally
# get session token
session_header = {'mainzellisteApiKey': mainzellisteApiKey,
                  'mainzellisteApiVersion': '2.0',
                  'Content-Type': 'application/json'
                  }

session_patient = requests.post("http://localhost:"+mainzellistePatientPort+"/sessions", headers=session_header)

# Uncomment this on the first run to check for your ip address
# Add your ip address in mainzelliste.conf.default line 305
print('Mainzelliste PATIENT session test: ')
print(session_patient.status_code)
print(session_patient.text)  # to check for your ip address

session_id_patient = session_patient.json()['sessionId']

# Mainzelliste Event
# Set up session to use globally
# get session token
session_header = {'mainzellisteApiKey': mainzellisteApiKey,
                  'mainzellisteApiVersion': '2.0',
                  'Content-Type': 'application/json'
                  }

session_event = requests.post("http://localhost:"+mainzellisteEventPort+"/sessions", headers=session_header)

# Uncomment this on the first run to check for your ip address
# Add your ip address in mainzelliste.conf.default line 305
print('Mainzelliste EVENT session test: ')
print(session_event.status_code)
print(session_event.text)  # to check for your ip address

session_id_event = session_event.json()['sessionId']

# Establish database connection
try:
    connection = psycopg2.connect(user=db_user,
                                  password=db_password,
                                  host=db_host,
                                  port=db_port,
                                  database=db_name)

    cursor = connection.cursor()
    dictionary_cursor = connection.cursor(cursor_factory=psycopg2.extras.DictCursor)

    # Print PostgreSQL Connection properties
    print('PostgreSQL connection:')
    print(connection.get_dsn_parameters())

    # Print PostgreSQL version
    cursor.execute("SELECT version();")
    record = cursor.fetchone()
    print("You are connected to - ", record, "\n")

except (Exception, psycopg2.Error) as error:
    print("Error while connecting to PostgreSQL", error)


########################################################################################################################
# Execute & commit sql statement
# Rollback if error
def sql_exe(sql_statement):
    try:
        cursor.execute(sql_statement)
        connection.commit()

        print("SQL successful: " + sql_statement)
        return True

    except (Exception, psycopg2.Error) as sqlerror:
        connection.rollback()

        print(sqlerror)
        return False


# Check row for filter data
# Return True to be filtered out, False for not filtering out
def filter_data(df_row):
    output = False

    # Allowlist
    for listelement in Allow:
        allowed = True
        for header, characteristic in listelement:
            if str(df_row[header]).strip() != characteristic:
                allowed = False
                break
        if allowed:
            return False

    # Filterlist
    for listelement in Filter:
        filtered = True
        for header, characteristic in listelement:
            if str(df_row[header]).strip() != characteristic:
                filtered = False
                break
        if filtered:
            return True
    return False


def compute_age(time1, time2):
    timestmap1 = datetime.datetime.strptime(time1, "%d.%m.%Y")
    timestamp2 = datetime.datetime.strptime(time2, "%d.%m.%Y %H:%M:%S")

    age = relativedelta(timestamp2, timestmap1)
    return age.years


# Second function needed because timestamp select from database is in a different format then before
def compute_age_databasetime(time1, time2):
    timestmap1 = datetime.datetime.strptime(time1, "%d.%m.%Y")
    timestamp2 = datetime.datetime.strptime(time2, "%Y-%m-%d %H:%M:%S")

    age = relativedelta(timestamp2, timestmap1)
    return age.years


# NOT USED AT THE MOMENT
# Will take a long time...
# Use for skiprows parameter in read_csv to skip line if 'Doctorletter'
def skiper(line):
    df = pandas.read_csv(obxFilepath, delimiter="\t", dtype=str, skiprows=[i for i in range(1, (line - 1))],
                         nrows=1)
    print("Line: " + str(line))
    print(df)
    for index, row in df.iterrows():
        if row['Observation_id'] == 'DoctorLetter':
            return True
    return False


########################################################################################################################
# Build SQL query for event table
def sql_builder_event(table_head, df_row):
    sql_output = 'INSERT INTO public.\"Event\" ('
    for head, type in table_head:
        sql_output += '\"' + head + '\"'

        # Last header
        if head == table_head[-1][0]:
            continue
        else:
            sql_output += ', '

    sql_output += ')\nVALUES ('

    for head, type in table_head:
        # "Event_id" in dataframe in "Id"
        if head == 'Event_id':
            sql_output += '\'' + df_row['Id'] + '\', '
            continue

        # If type=1 -> numerical
        if type:
            if pandas.isna(df_row[head]):
                sql_output += 'NULL'
            else:
                sql_output += str(df_row[head])
        # If type=1 -> text
        else:
            if pandas.isna(df_row[head]):
                sql_output += 'NULL'
            else:
                sql_output += '\'' + df_row[head] + '\''

        # Last entry no comma
        if head == table_head[-1][0]:
            continue
        else:
            sql_output += ', '

    sql_output += ');'
    return sql_output


# Build SQL query for value table (nm or tx)
def sql_builder_value(table_head, df_row):
    sql_output = 'INSERT INTO public.\"'
    if df_row['Value_type_id'] == 'NM':
        sql_output += 'Value_nm'
    else:
        sql_output += 'Value_tx'
    sql_output += '\" ('

    for head in table_head:
        sql_output += '\"' + head + '\"'

        # Last header
        if head == table_head[-1]:  # Last header in Value table
            continue
        else:
            sql_output += ', '

    sql_output += ')\nVALUES ('

    for head in table_head:
        # Event_id in dataframe in Id
        if head == 'Event_id':
            sql_output += '\'' + df_row['Id'] + '\', '
            continue

        # Differentiate between numerical and text
        elif head == 'Value':
            if pandas.isna(df_row['Value']):
                sql_output += 'NULL'  # + ', '
                continue

            if df_row['Value_type_id'] == 'NM':
                nm = (str(df_row['Value']).strip()).replace(',', '.')
                sql_output += nm
            else:
                sql_output += '\'' + str(df_row['Value']).strip() + '\''
            # sql_output += ', '
            continue

        # Leftover headers
        if pandas.isna(df_row[head]):
            sql_output += 'NULL'
        else:
            sql_output += '\'' + str(df_row[head]).strip() + '\''

        # Last entry no comma
        if head == table_head[-1]:
            continue
        else:
            sql_output += ', '

    sql_output += ');'
    # print(sql_output)
    return sql_output


########################################################################################################################
# Functions for Mainzelliste Patient

# Mainzelliste
# Input IDAT and get pseudonym ID back
def get_anonymized_patient_id(patientid='', firstname='', lastname='', birthday='', birthmonth='', birthyear='',
                              address=''):
    # Add patient to Mainzelliste
    attributes = []
    if patientid:
        attributes.append(('pat_id=', patientid))
    if firstname:
        attributes.append(('firstname=', firstname))
    if lastname:
        attributes.append(('lastname=', lastname))
    if birthday:
        attributes.append(('birthday=', birthday))
    if birthmonth:
        attributes.append(('birthmonth=', birthmonth))
    if birthyear:
        attributes.append(('birthyear=', birthyear))
    if address:
        attributes.append(('address=', address))
    # print(attributes)

    # token addPatient
    header = {'mainzellisteApiKey': mainzellisteApiKey,
              'mainzellisteApiVersion': '2.0',
              'Content-Type': 'application/json'
              }

    body = {
        "type": "addPatient",
        "data": {
            "idtypes": ["pid"]
        }
    }
    r = requests.post("http://localhost:"+mainzellistePatientPort+"/sessions/" + session_id_patient + "/tokens", data=json.dumps(body),
                      headers=header)
    # print(r.json())
    token_id = r.json()['id']

    # add patient
    header = {
        'mainzellisteApiKey': mainzellisteApiKey,
        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'mainzellisteApiVersion': '2.0'
    }

    url = "http://localhost:"+mainzellistePatientPort+"/patients?tokenId=" + token_id

    payload = ''
    for identifier, value in attributes:
        payload += identifier + value + '&'
    #payload += 'pat_id=' + patientid
    payload += 'sureness=true'
    print(payload)

    response = requests.post(url, headers=header, data=payload.encode('utf-8'))
    print(response.text)
    # Successful insertion/match
    if response.status_code == 201:
        print('New patient inserted or matched with existing patient')

        # print(response.json())
        pseudonomized_patient_id = response.json()[0]['idString']
        return pseudonomized_patient_id

    # Pat_id already in Mainzelliste but no match
    elif response.status_code == 409:
        print('Pat_id already in use but no match using given attributes')

        if 'Found existing patient with matching external ID but conflicting IDAT!' in response.text:
            print('Debug 1')
            anchor = getPatients(pat_id=patientid)

            vor = False
            nach = False

            if firstname in anchor[0]['fields']['firstname']:
                vor = True
            if lastname in anchor[0]['fields']['lastname']:
                nach = True

            if vor and nach:
                return anchor[0]['ids'][0]['idString']


            # Patient with same ID but different IDAT
            patientidPlus = patientid + '_'
            InsertWithPlus = addPatient(patientidPlus, firstname=firstname, lastname=lastname, birthday=birthday, birthmonth=birthmonth, birthyear=birthyear)

            sql = 'INSERT INTO public.\"Relationship\"(anchor_pseu, pseu, type) VALUES (\''+anchor[0]['ids'][0]['idString']+'\', \''+InsertWithPlus+'\', \'D\')'
            sql_exe(sql)

            #delete event age - unnecessary, do at the end of computation
            #sql = 'UPDATE public.\"Event\" SET \"Event_age\" = NULL WHERE \"Pat_id\" like \''+anchor[0]['ids'][0]['idString']+'\''
            #sql_exe(sql)

            return InsertWithPlus

        elif 'Found existing patient with matching IDAT but conflicting external ID(s).' in response.text:
            print('Debug 2')
            #anchor = getPatients(pat_id=patientid)
            anchor = get_anonymized_patient_id('', firstname=firstname, lastname=lastname, birthday=birthday, birthmonth=birthmonth, birthyear=birthyear)

            # Patient with same IDAT but different ID
            firstnamePlus = firstname + '_'
            lastnamePlus = lastname + '_'
            InsertWithPlus = addPatient(patientid, firstname=firstnamePlus, lastname=lastnamePlus, birthday=birthday, birthmonth=birthmonth, birthyear=birthyear)

            sql = 'INSERT INTO public.\"Relationship\"(anchor_pseu, pseu, type) VALUES (\'' + anchor + '\', \'' + InsertWithPlus + '\', \'S\')'
            sql_exe(sql)

            return InsertWithPlus

    print('Error: ' + str(response.status_code))

    return 0

# rekursive addPatient function
def addPatient(patientid='', firstname='', lastname='', birthday='', birthmonth='', birthyear='', address=''):
    # Add patient to Mainzelliste
    attributes = []
    if patientid:
        attributes.append(('pat_id=', patientid))
    if firstname:
        attributes.append(('firstname=', firstname))
    if lastname:
        attributes.append(('lastname=', lastname))
    if birthday:
        attributes.append(('birthday=', birthday))
    if birthmonth:
        attributes.append(('birthmonth=', birthmonth))
    if birthyear:
        attributes.append(('birthyear=', birthyear))
    if address:
        attributes.append(('address=', address))
    # print(attributes)

    # token addPatient
    header = {'mainzellisteApiKey': mainzellisteApiKey,
              'mainzellisteApiVersion': '2.0',
              'Content-Type': 'application/json'
              }

    body = {
        "type": "addPatient",
        "data": {
            "idtypes": ["pid"]
        }
    }
    r = requests.post("http://localhost:" + mainzellistePatientPort + "/sessions/" + session_id_patient + "/tokens",
                      data=json.dumps(body),
                      headers=header)
    # print(r.json())
    token_id = r.json()['id']

    # add patient
    header = {
        'mainzellisteApiKey': mainzellisteApiKey,
        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'mainzellisteApiVersion': '2.0'
    }

    url = "http://localhost:" + mainzellistePatientPort + "/patients?tokenId=" + token_id

    payload = ''
    for identifier, value in attributes:
        payload += identifier + value + '&'
    #payload += 'pat_id=' + patientid
    payload += 'sureness=true'
    print(payload)

    response = requests.post(url, headers=header, data=payload.encode('utf-8'))
    print(response.text)
    # Successful insertion/match
    if response.status_code == 201:
        print('New patient inserted or matched with existing patient')

        # print(response.json())
        pseudonomized_patient_id = response.json()[0]['idString']
        return pseudonomized_patient_id

    # Pat_id already in Mainzelliste but no match
    elif response.status_code == 409:
        print('Pat_id already in use but no match using given attributes')

        if 'Found existing patient with matching external ID but conflicting IDAT!' in response.text:
            print('ADD Debug 1')
            anchor = getPatients(pat_id=patientid)

            vor = False
            nach = False

            if firstname in anchor[0]['fields']['firstname']:
                vor = True
            if lastname in anchor[0]['fields']['lastname']:
                nach = True

            if vor and nach:
                return anchor[0]['ids'][0]['idString']


            # Patient with same ID but different IDAT
            patientidPlus = patientid + '_'
            return addPatient(patientidPlus, firstname=firstname, lastname=lastname, birthday=birthday, birthmonth=birthmonth, birthyear=birthyear)

        elif 'Found existing patient with matching IDAT but conflicting external ID(s).' in response.text:
            print('ADD Debug 2')
            #anchor = getPatients(pat_id=patientid)

            # Patient with same IDAT but different ID
            firstnamePlus = firstname + '_'
            lastnamePlus = lastname + '_'
            return addPatient(patientid, firstname=firstnamePlus, lastname=lastnamePlus, birthday=birthday,
                                        birthmonth=birthmonth, birthyear=birthyear)


# Mainzelliste
# Edit patient with 'pseudonym' in Mainzelliste with attributes
def editPatient(attributes, pseudonym):
    # token editPatient
    header = {'mainzellisteApiKey': mainzellisteApiKey,
              'mainzellisteApiVersion': '2.0',
              'Content-Type': 'application/json'
              }

    body = {
        "type": "editPatient",
        "data": {
            "patientId": {
                "idType": "pid",
                "idString": pseudonym
            },
            "fields": ["firstname", "lastname", "birthday", "birthmonth", "birthyear"],
            "ids": ["pat_id"]
        }
    }

    r = requests.post("http://localhost:"+mainzellistePatientPort+"/sessions/" + session_id_patient + "/tokens", data=json.dumps(body),
                      headers=header)

    token_id = r.json()['id']

    # use editPatient token
    header = {
        'mainzellisteApiKey': mainzellisteApiKey,
        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'mainzellisteApiVersion': '2.0',
        'X-HTTP-Method-Override': 'PUT'
    }

    payload = ''
    for identifier, value in attributes:
        payload += identifier + value + '&'
    payload = payload[:-1]
    #print(payload)

    url = "http://localhost:"+mainzellistePatientPort+"/patients/tokenId/" + token_id

    response = requests.post(url, headers=header, data=payload.encode('utf-8'))

    #print(response.status_code)
    if response.status_code == 200:
        print('Edit successful!')

        editPatientPseu.append(pseudonym)
    else:
        print('Error while edit!')


# Mainzelliste
# Input pseudonym ID -or- Pat_id and get IDAT back
def getPatients(pid='', pat_id=''):
    # token readPatients
    header = {'mainzellisteApiKey': mainzellisteApiKey,
              'mainzellisteApiVersion': '2.0',
              'Content-Type': 'application/json'
              }

    body = {}

    if pid == '':
        body = {
            "type": "readPatients",
            "data": {
                "searchIds": [
                    {
                        "idType": "pat_id",
                        "idString": str(pat_id)
                    }
                ],
                "resultFields": ["firstname", "lastname", "birthday", "birthmonth", "birthyear"],
                "resultIds": ["pid", "pat_id"]
            }
        }

    elif pat_id == '':
        body = {
            "type": "readPatients",
            "data": {
                "searchIds": [
                    {
                        "idType": "pid",
                        "idString": str(pid)
                    }
                ],
                "resultFields": ["firstname", "lastname", "birthday", "birthmonth", "birthyear"],
                "resultIds": ["pid", "pat_id"]
            }
        }

    r = requests.post("http://localhost:"+mainzellistePatientPort+"/sessions/" + session_id_patient + "/tokens", data=json.dumps(body),
                      headers=header)

    #print(r.text)
    #print(r.status_code)

    if r.status_code == 201:
        # print(r.json())
        token_id = r.json()['id']

        # use readPatients token
        url = "http://localhost:"+mainzellistePatientPort+"/patients/tokenId/" + token_id
        response = requests.request("GET", url, headers=header)
        #print(response.text)

        return response.json()

    elif r.status_code == 404:
        print('No Patient found')
        return 0

    elif r.status_code == 400:
        print('No Patient found')
        return 0

####################
# Functions for Mainzelliste Event


# Mainzelliste
def get_anonymized_event_id(eventid):
    # token addPatient
    header = {'mainzellisteApiKey': mainzellisteApiKey,
              'mainzellisteApiVersion': '2.0',
              'Content-Type': 'application/json'
              }

    body = {
        "type": "addPatient",
        "data": {
            "idtypes": ["pid"]
        }
    }
    r = requests.post("http://localhost:"+mainzellisteEventPort+"/sessions/" + session_id_event + "/tokens", data=json.dumps(body),
                      headers=header)

    print('\naddEvent Token:')
    print('HTML code: ' + str(r.status_code))
    print('HTML text: ' + str(r.text))
    # print(r.json())
    token_id = r.json()['id']

    # add patient
    header = {
        'mainzellisteApiKey': mainzellisteApiKey,
        'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
        'mainzellisteApiVersion': '2.0'
    }

    url = "http://localhost:"+mainzellisteEventPort+"/patients?tokenId=" + token_id

    payload = 'idat=identifier&event_id=' + eventid + '&sureness=true'

    response = requests.post(url, headers=header, data=payload.encode('utf-8'))

    print('\naddEvent Execution:')
    print('HTML code: ' + str(response.status_code))
    print('HTML text: ' + str(response.text))
    #print(str(response.text))
    # Successful insertion/match
    if response.status_code == 201:
        print('New event inserted or matched with existing event')

        # print(response.json())
        pseudonomized_event_id = response.json()[0]['idString']
        #print(pseudonomized_event_id)
        return pseudonomized_event_id

    elif response.status_code == 409:
        print('Event_id already in use but no match using given attributes')
        get_json = getEvent(event_id=eventid)

        # print(response.json()[0]['ids'][0]['idString'])
        pseudonomized_event_id = get_json[0]['ids'][0]['idString']
        return pseudonomized_event_id

    print('\n')
    print('Error while addEvent')
    print('HTML code: ' + str(response.status_code))
    print('HTML text: ' + str(response.text))

    return 0


# Mainzelliste
# Input pseudonym ID -or- Event_id and get IDAT (in this case the ids) back
def getEvent(pid='', event_id=''):
    # token readPatients
    header = {'mainzellisteApiKey': mainzellisteApiKey,
              'mainzellisteApiVersion': '2.0',
              'Content-Type': 'application/json'
              }

    body = {}

    if pid == '':
        body = {
            "type": "readPatients",
            "data": {
                "searchIds": [
                    {
                        "idType": "event_id",
                        "idString": str(event_id)
                    }
                ],
                "resultIds": ["pid", "event_id"]
            }
        }

    elif event_id == '':
        body = {
            "type": "readPatients",
            "data": {
                "searchIds": [
                    {
                        "idType": "pid",
                        "idString": str(pid)
                    }
                ],
                "resultIds": ["pid", "event_id"]
            }
        }

    r = requests.post("http://localhost:"+mainzellisteEventPort+"/sessions/" + session_id_event + "/tokens", data=json.dumps(body),
                      headers=header)

    print('\ngetEvent Token:')
    print('HTML code: ' + str(r.status_code))
    print('HTML text: ' + str(r.text))

    #print(r.json())
    token_id = r.json()['id']

    # use readPatients token
    url = "http://localhost:"+mainzellisteEventPort+"/patients/tokenId/" + token_id
    response = requests.request("GET", url, headers=header)

    return response.json()


########################################################################################################################
########################################################################################################################
########################################################################################################################
# Start of computation
print('\n\nSTART OF COMPUTATION\n\n')


if obrComputation:

    # Compute obr.txt data
    obr = pandas.read_csv(obrFilepath, delimiter="\t", dtype=str, engine='python', encoding=obrEncoding, error_bad_lines=False)
    # Debug txt file
    print('obr header:')
    print(list(obr.columns))
    print('\nPrint obr dataframe for manual controll:')
    print(obr)

    # Filter out not needed rows
    obr = obr[obr['Pat_id'].notnull()]
    obr = obr[obr['Name'] != 'unknown']
    obr = obr[obr['Name'].notnull()]
    obr = obr[obr['Vorname'] != 'unknown']
    obr = obr[obr['Vorname'].notnull()]
    obr = obr[obr['Geb_dat'].notnull()]

    print('\nobr after filtering for manual controll:')
    print(obr)


    # Mainzelliste Patient
    # Get new session because old one can be timed out
    # get session token
    session_header = {'mainzellisteApiKey': mainzellisteApiKey,
                      'mainzellisteApiVersion': '2.0',
                      'Content-Type': 'application/json'
                      }

    session_patient = requests.post("http://localhost:"+mainzellistePatientPort+"/sessions", headers=session_header)

    # Uncomment this on the first run to check for your ip address
    # Add your ip address in mainzelliste.conf.default line 305
    print('\nNew Mainzelliste PATIENT session: ')
    print(session_patient.status_code)
    print(session_patient.text)  # to check for your ip address

    session_id_patient = session_patient.json()['sessionId']


    # iterate rows of obr
    for index, row in obr.iterrows():
        print('*****************************')
        print(index, ' processing...')
        # Create pseudonym
        Pat_id = row['Pat_id'].strip()

        # Convert birthday to datetime
        bd = row['Geb_dat']
        bd_date = datetime.datetime.strptime(bd, "%d.%m.%Y %H:%M:%S")

        lastname = row['Name']
        firstname = row['Vorname']

        # Create Pseudonym
        Pat_pseu = str(get_anonymized_patient_id(Pat_id, firstname, lastname, bd_date.strftime('%d'), bd_date.strftime('%m'),
                                             bd_date.strftime('%Y')))
        # Pat_pseu = Pat_id

        if Pat_pseu == str(0):
            print('Anonymizing patient went wrong! Invalid input to Mainzelliste!')
            exit()


        # Insert pseudonym in dataframe for next computation
        row['Pat_id'] = Pat_pseu

        # Insertion into "Patient"
        sql = 'INSERT INTO public.\"Patient\"(\"Pat_id\") VALUES(\'' + row['Pat_id'] + '\');'
        sql_exe(sql)

        # Compute age
        now = datetime.datetime.now()
        age = relativedelta(now, bd_date)
        # print(age.years)

        sql = 'UPDATE public.\"Patient\" SET age=' + str(age.years) + ' WHERE \"Pat_id\" = \'' + row['Pat_id'] + '\';'
        sql_exe(sql)

        print('*****************************')


if obxComputation:

    # Get indexes of all lines with more tabs than in the header (line 0)
    # Use them for skiprows parameter of read_csv
    tabmax = 0
    skipindex = []
    with open(obxFilepath, encoding='iso-8859-1') as f:
        for i, line in enumerate(f):
            if i == 0:
                tabmax = line.count('\t')

            tabcount = line.count('\t')
            #print('Index: ' + str(i) + "\tTabcount: " + str(tabcount))

            if (tabcount > tabmax):
                skipindex.append(i)
    #print(tabmax)
    #print(skipindex)

    print('\n\n\n')
    # Compute obr.txt data
    obx = pandas.read_csv(obxFilepath, delimiter="\t", dtype=str, skiprows=skipindex, engine='python', encoding=obxEncoding, error_bad_lines=False, quoting=csv.QUOTE_NONE)
    print('obx header:')
    print(list(obx.columns))

    # Filter out program-breaking rows
    obx = obx[obx['Id'].notnull()]
    obx = obx[obx['Pat_id'].notnull()]

    print('\nPrint obx dataframe for manual controll:')
    print(obx)


    # Mainzelliste Patient
    # Get new session because old one can be timed out
    # get session token
    session_header = {'mainzellisteApiKey': mainzellisteApiKey,
                      'mainzellisteApiVersion': '2.0',
                      'Content-Type': 'application/json'
                      }

    session_patient = requests.post("http://localhost:"+mainzellistePatientPort+"/sessions", headers=session_header)

    # Uncomment this on the first run to check for your ip address
    # Add your ip address in mainzelliste.conf.default line 305
    print('\nNew Mainzelliste PATIENT session: ')
    print(session_patient.status_code)
    print(session_patient.text)  # to check for your ip address

    session_id_patient = session_patient.json()['sessionId']


    # Mainzelliste Event
    # Get new session because old one probably timed out
    # get session token
    session_header = {'mainzellisteApiKey': mainzellisteApiKey,
                      'mainzellisteApiVersion': '2.0',
                      'Content-Type': 'application/json'
                      }

    session_event = requests.post("http://localhost:"+mainzellisteEventPort+"/sessions", headers=session_header)

    # Uncomment this on the first run to check for your ip address
    # Add your ip address in mainzelliste.conf.default line 305
    print('New Mainzelliste EVENT session: ')
    print(session_event.status_code)
    print(session_event.text)  # to check for your ip address

    session_id_event = session_event.json()['sessionId']


    # iterate rows of obx
    for index, row in obx.iterrows():

        # Filter out predefined data
        if filter_data(row):
            continue

        print('~~~~~~~~~~~~~~~~~~~~~~~~~~~~~')
        print(index, ' processing...')
        # Create pseudonym: ACHTUNG LEERZEICHEN IN Pat_id
        Pat_id = row['Pat_id'].strip()
        Event_id = row['Id'].strip()
        Obr_id = row['Id_obr'].strip()

        # Create Pseudonym
        #Pat_pseu = str(get_anonymized_patient_id(Pat_id))

        #if Pat_pseu == str(0):
        #    print('Anonymizing patient went wrong! Invalid input to Mainzelliste!')
        #    exit()

        Pat_pseu_json = getPatients(pat_id=Pat_id)
        #print(Pat_pseu_json[0]['ids'][0])
        Pat_pseu = 0

        # No IDAT for patient, so skip row
        if Pat_pseu_json == 0:
            if AllowObxPatientCreation:
                Pat_pseu = str(get_anonymized_patient_id(Pat_id))

                if Pat_pseu == str(0):
                    print('Anonymizing patient went wrong! Invalid input to Mainzelliste!')
                    exit()

            else:
                continue

        else:
            Pat_pseu = Pat_pseu_json[0]['ids'][0]['idString']

        print('Event_id pseudonymization')
        Event_pseu = str(get_anonymized_event_id(Event_id))
        if Event_pseu == 0:
            print('ERROR WHILE GETTING EVENT PSEUDONYM')

        print('\n\nId_obr pseudonymization')
        Obr_pseu = str(get_anonymized_event_id(Obr_id))
        if Obr_pseu == 0:
            print('ERROR WHILE GETTING EVENT PSEUDONYM')
            exit()
        # Pat_pseu = Pat_id
        #Event_pseu = Event_id
        #Obr_pseu = Obr_id

        # Insert pseudonym in dataframe for next computation
        row['Pat_id'] = Pat_pseu
        row['Id'] = Event_pseu
        row['Id_obr'] = Obr_pseu

        print('\nSQL:')
        # Making sure obx.Pat_id is in "Patient"
        sql = 'INSERT INTO public.\"Patient\"(\"Pat_id\") VALUES(\'' + row['Pat_id'] + '\');'
        sql_exe(sql)

        # Build SQL for Event
        sql = sql_builder_event(Event, row)

        # Add SQL for Value_nm or Value_tx
        sql += '\n\n'
        sql += sql_builder_value(Value, row)

        # Execute both SQL statements
        sql_exe(sql)

        # Get age at event timestamp
        pat_data = getPatients(pid=row['Pat_id'])
        if (pat_data[0]['fields']['birthday'] != '') and (pat_data[0]['fields']['birthmonth'] != '') and (
                pat_data[0]['fields']['birthyear'] != ''):
            bd = pat_data[0]['fields']['birthday'] + "." + pat_data[0]['fields']['birthmonth'] + "." + \
                 pat_data[0]['fields']['birthyear']
            event_age = compute_age(bd, row['Observation_ts'])

            # Insert event age
            sql = 'UPDATE public.\"Event\" SET \"Event_age\"=' + str(event_age) + ' WHERE \"Event_id\" = \'' + row[
                'Id'] + '\';'
            sql_exe(sql)

        print('~~~~~~~~~~~~~~~~~~~~~~~~~~~~~')


# Update Event_age if new IDAT from edited patients in Mainzelliste is available
if editPatientPseu:
    print(editPatientPseu)
    sql = 'SELECT * FROM public.\"Event\" WHERE '

    for pseudonym in editPatientPseu:
        sql += '(\"Pat_id\"=\'' + pseudonym + '\' AND \"Event_age\" IS NULL) AND'

    sql = sql[:-4]
    sql += ';'

    dictionary_cursor.execute(sql)
    rows = dictionary_cursor.fetchall()

    # print(rows)

    #
    for row in rows:
        pat_data = getPatients(pid=row['Pat_id'])
        if (pat_data[0]['fields']['birthday'] != '') and (pat_data[0]['fields']['birthmonth'] != '') and (
                pat_data[0]['fields']['birthyear'] != ''):
            print('#############################')

            bd = pat_data[0]['fields']['birthday'] + "." + pat_data[0]['fields']['birthmonth'] + "." + \
                 pat_data[0]['fields']['birthyear']

            #print(str(row['Observation_ts']))
            event_age = compute_age_databasetime(bd, str(row['Observation_ts']))

            # Insert event age
            sql = 'UPDATE public.\"Event\" SET \"Event_age\"=' + str(event_age) + ' WHERE \"Event_id\" = \'' + row[
                'Event_id'] + '\';'
            sql_exe(sql)
            print('#############################')

# Update Event_age for existing relationsships
sql = 'UPDATE public.\"Event\" SET \"Event_age\"=NULL WHERE \"Pat_id\" IN (SELECT anchor_pseu FROM public.\"Relationship\" WHERE type LIKE \'D\')'
sql_exe(sql)

if (connection):
    cursor.close()
    connection.close()
    print("PostgreSQL connection is closed")