import argparse
import os
import platform
import redivis
import simplejson as json
import sys

from datetime import datetime, timedelta

DATASET = "neurotechxcolumbia dataset"
INFO_TABLE = f"matheu_campbell.neurotechxcolumbia_dataset.info_table:rx53"
DATA_TABLE = "data_table"
HPARAMS = ("SampleRate", "HeadsetConfiguration", "HeadsetModel", "BufferSize")
SPARAMS = ("ProjectName", "SubjectName", "ResponseType", "StimulusType",
           "BlockLength", "BlockCount", "StimCycle")


def listify(annotations):
    """Convert annotation json to list"""
    dct = json.loads(annotations)
    out = []
    for key, val in dct.items():
        out.append((int(float(key)), val))
    return out


def reconstruct_info(row):
    out = {'HardwareParams': {}, 'SessionParams': {}}
    for key, val in row.items():
        if key == 'Annotations':
            out[key] = listify(val)
        elif key in HPARAMS:
            out['HardwareParams'][key] = val
        elif key in SPARAMS:
            out['SessionParams'][key] = val
        elif key[0] == "_":
            continue
        else:
            out[key] = str(val)
    return out


def multisort(arr, attrs):
    arr.sort(key=lambda x: tuple(getattr(x, attr) for attr in attrs))


def gen_exp(parsed):
    if not [v for f, v in vars(parsed).items() if v and f != "after_date" and f != "before_date"]:
        return f"""SELECT * from `{INFO_TABLE}`"""

    def fieldmatch(field, val):
        return f"LOWER({field.title().replace('_', '')}) = LOWER(\"{val}\")"

    query = f"""SELECT * from `{INFO_TABLE}` WHERE """
    query += " AND ".join([fieldmatch(f, v) for f, v in vars(parsed).items() if v and f != "after_date"
                           and f != "before_date"])
    return query


def query_criteria(parsed):
    ret = f"Project: {parsed.project_name}\n" if parsed.project_name else ""
    ret += f"Subject: {parsed.subject_name}\n" if parsed.subject_name else ""
    ret += f"Response Type: {parsed.response_type}\n" if parsed.response_type else ""
    ret += f"Stimulus Type: {parsed.stimulus_type}\n" if parsed.stimulus_type else ""
    ret += f"Headset Configuration: {parsed.headset_configuration}\n" if parsed.headset_configuration else ""
    ret += f"Headset Model: {parsed.headset_model}\n" if parsed.headset_model else ""
    ret += f"Collected before: {parsed.before_date}\n" if parsed.before_date else ""
    ret += f"Collected after: {parsed.after_date}\n" if parsed.after_date else ""
    return ret


parser = argparse.ArgumentParser(
    prog='retrieve.py',
    description='Queries revidis for relevant data sessions and downloads folder' +
                ' of results.',
    formatter_class=argparse.RawTextHelpFormatter)

parser.add_argument('-p', '--project-name', help="Project name")
parser.add_argument('-n', '--subject-name', help="The name of a particular data collection subject")
parser.add_argument('-r', '--response-type', help="EEG Response Type (SSVEP|ERP|other)")
parser.add_argument('-s', '--stimulus-type', help="Stimulus type (visual|audio|other)")
parser.add_argument('-c', '--headset-configuration', help="Headset configuration (standard|occipital|other)")
parser.add_argument('-m', '--headset-model', help="Headset model (CytonDaisy|Cyton)")
parser.add_argument('-b', '--before-date',
                    help="only include data collected before this date (MM-DD-YYYY) (inclusive); defaults to now")
parser.add_argument('-a', '--after-date',
                    help="only include data collected after this date (MM-DD-YYYY) (inclusive); defaults to 10 years ago")

args = parser.parse_args()
qstring = query_criteria(args)
if not qstring and input("No search criteria provided. Query for all available data? (y/N) ") != "y":
    print("Exiting")
    sys.exit(0)
elif qstring:
    print("Searching for sessions by the following criteria: \n" + qstring)

# Query for sessions
qexp = gen_exp(args)
try:
    query = redivis.query(qexp)
except OSError:
    if platform.system() == "Linux" or platform.system() == "Darwin":
        print("Error: Redivis API token not set. Run 'export REDIVIS_API_TOKEN=your_token' in your terminal "
              "before retrieving data.")
    elif platform.system() == 'Windows':
        print("Error: Redivis API token not set. Run '$Env:REDIVIS_API_TOKEN = 'your_token' in PowerShell "
              "before retrieving data.")
    sys.exit(1)

while query.get()['status'] == 'running':
    pass
if not query.get()['outputNumRows']:
    print("0 sessions found. Try again with different criteria.")
    sys.exit(0)

rows = query.list_rows()

if args.before_date or args.after_date:
    try:
        bdate = datetime.strptime(args.before_date, "%m-%d-%Y") if args.before_date else datetime.now()
        adate = datetime.strptime(args.after_date, "%m-%d-%Y") if args.after_date \
            else datetime.now() - timedelta(days=3650)
    except ValueError:
        print("Error: Incorrect date format; should be MM-DD-YYYY")
        sys.exit(1)

    to_remove = []
    for row in rows:
        if not adate.date() <= row.Date <= bdate.date():
            to_remove.append(row)
    for r in to_remove:
        rows.remove(r)

count = len(rows)
print(f"{count} session found." if count == 1 else
      f"{count} sessions found.\n")

if not count:
    print("Try again with different criteria.")
    sys.exit(0)

print("Project\t\tSubject\t\t\tLength\t\tDate\t\tDescription")
print("--------------------------------------------------------------------------------------------")

multisort(rows, ["ProjectName", "SubjectName", "Date", "Description"])

for session in rows:
    desc = session.Description.replace("\n", "") if len(session.Description) <= 20 else (
            session.Description[:17].replace("\n", "") + "...")
    print(session.ProjectName + "\t\t" + session.SubjectName + "\t\t" + 
          str(round(int(session.BlockLength)*int(session.BlockCount), 2))+"s" + "\t\t" + 
          str(session.Date) + "\t" + desc)

if input("\nDownload all found sessions and their associated info JSON? (y/N) ") == "y":
    outpath = os.path.abspath("datapackage")
    os.makedirs(outpath, exist_ok=True)
    with open(os.path.join(outpath, "query.txt"), 'w+') as file:
        file.write("Query Criteria\n")
        file.write(qstring)

    for num, session in enumerate(rows):
        folder = os.path.join(outpath, session._UPLOAD_NAME)
        os.makedirs(folder, exist_ok=True, mode=0o700)
        with open(os.path.join(folder, "info.json"), 'w') as file:
            json.dump(reconstruct_info(session), file, indent=4, ensure_ascii=False)

        file = redivis.file(session.FileID)
        try:
            file.download(os.path.join(folder, "data.csv"))
        except Exception as E:
            print(f"Error: {E}")

        print(f"Created {folder}")
else:
    print("Exiting.")
    sys.exit(0)

print("Downloaded requested files.")
