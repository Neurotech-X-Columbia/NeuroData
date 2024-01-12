"""
Upload new data session and associated info.json to Redivis.
    -s --session-path: Path to directory containing a properly formatted info.json and data.csv files.
    -u --username: Redivis username
"""

import argparse
import simplejson as json
import os
import redivis
import sys

DATASET = "neurotechxcolumbia dataset"
INFO_TABLE = "Info Table"
DATA_TABLE = "Data Table"
HPARAMS = ("SampleRate", "HeadsetConfiguration", "HeadsetModel", "BufferSize")
SPARAMS = ("ProjectName", "SubjectName", "ResponseType", "StimulusType",
           "BlockLength", "BlockCount", "StimCycle")


def verify_json(json: dict):
    valid = True
    req = ['SessionParams', 'HardwareParams', 'Description',
           'Annotations', 'Date', 'Time', 'FileID']

    for field in req:
        if field not in json:
            print(f"Info JSON missing field: '{field}'.")
            valid = False
            
    req2 = ['SubjectName', 'ProjectName', 'ResponseType', 'StimulusType',
            'BlockLength', 'BlockCount', 'StimCycle']
    for field in req2:
        if field not in json.get('SessionParams'):
            print(f"SessionParams field missing subfield: '{field}'.")
            valid = False
        
    req3 = ['SampleRate', 'HeadsetConfiguration', 'HeadsetModel', 'BufferSize']
    for field in req3:
        if field not in json.get('HardwareParams'):
            print(f"HardwareParams field missing subfield: '{field}'.")
            valid = False

    return valid


def dictify(annotations):
    """Convert annotation list to json formatted string."""
    out = {}
    for a in annotations:
        out[str(a[0])] = a[1]
    
    return out


def flatten(dct):
    flat = {}
    for key, val in dct.items():
        if isinstance(val, dict):
            for k, v in flatten(val).items():
                flat[k] = v
        elif isinstance(val, list):
            flat[key] = str(dictify(val)).replace("'", '"')
        else:
            flat[key] = val
    return flat


def info_upload(ds_name, table_name, username, infodct, fname):
    dataset = redivis.user(username).dataset(ds_name)
    table = dataset.table(table_name)
    flat = [flatten(infodct)]
    with open('tmp', 'w') as f:
        json.dump(flat, f)
    with open('tmp') as f:
        upload = table.upload(fname).create(f, type="json",
                                            replace_on_conflict=True)
    os.remove('tmp')
    return upload


def session_upload(ds_name, table_name, username, datapath, fname):
    dataset = redivis.user(username).dataset(ds_name)
    table = dataset.table(table_name)
    with open(datapath, "rb") as f:
        file = table.add_file(fname, f)

    return file


parser = argparse.ArgumentParser(prog='upload_session.py',
                                 description='Uploads data session to Redivis')
parser.add_argument('-s', '--session-path', help="Path to session directory", required=True)
parser.add_argument('-u', '--username', help="Your Redivis username", required=True)

args = parser.parse_args()
session_path = os.path.abspath(args.session_path)
username = args.username
info_path = os.path.abspath(os.path.join(session_path, "info.json"))
data_path = os.path.abspath(os.path.join(session_path, "data.csv"))

if not os.path.isdir(session_path):
    print(f"Error: Session path '{session_path}' invalid.")
    sys.exit(1)

if not os.path.exists(info_path):
    print(f"Error: Info file not found in session directory.")
    sys.exit(1)

if not os.path.exists(data_path):
    print(f"Error: Data file not found in session directory.")
    sys.exit(1)

with open(info_path) as fileinfo:
    info = json.loads(fileinfo.read())

# Confirm info JSON contains the right fields.
if not verify_json(info):
    sys.exit(1)

if not input(f"Session found at '{session_path}'. Upload to database? (y/N) ") == 'y':
    sys.exit(1)

# Upload file to data table
fname = "data" + os.path.basename(session_path).split("_")[2] + ".csv"
try:
    print("Attempting data.csv upload.")
    file = session_upload(DATASET, DATA_TABLE, username, data_path, fname)
except Exception as E:
    print(f"Error: {str(E)}")
    sys.exit(1)

if isinstance(file, redivis.classes.File.File):
    print(f"Data file successfully uploaded to {DATA_TABLE}")

# Upload info JSON to Redivis
fname = os.path.basename(session_path)
try:
    file.get()
    info['FileID'] = file.properties['id']
    print("Attempting info.json upload.")
    resp = info_upload(DATASET, INFO_TABLE, username, info, fname)
except Exception as E:
    print(f"Error: {str(E)}")
    if 'tmp' in os.listdir():
        os.remove('tmp')
    sys.exit(1)

if isinstance(resp, redivis.classes.Upload.Upload):
    print(f"Info JSON successfully uploaded to {INFO_TABLE}.\n")