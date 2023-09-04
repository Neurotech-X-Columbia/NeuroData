# NeuroData
## Scripts for neural data collection, cloud storage, and retrieval
This repo contains documentation and utility scripts for data collection, cloud storage, and retrieval.

[Dataset Link](https://redivis.com/workspace/datasets/5e8n-ctqvm09q7)

### **Workflows**

### Data collection workflow:
1. Design your data collection session. Prepare a stimulus script, location, and time. You may need at two laptops (one for data collection and one to provide stimulus).
2. Define session info JSON via collection GUI. See ObjectInfo.md for more about info JSON files.
    - Session parameters: subject name, project name, response type, stimulus type, block length, block count, and stim cycle
    - Hardware parameters: sampling rate, buffer size, headset configuration, headset model
    - Description
    - Date
    - Time
3. Proceed to collection. When complete, there will be a session folder containing the newly generated .csv file, its accompanying info file, and session log file.
4. Supply session directory to upload script (upload_session.py) to store data on Columbia Data Platform.

### Data retrieval:
1. Decide which parameters are relevant.
2. Use retrieval script (retrieve.py) to query Columbia Data Platform (Redivis) for sessions with your desired criteria. Data will be downloaded into a datapackage folder with the following structure.

```
datapackage/
    ├─ query.txt
    ├─ session_08_11_10_62625/
    │  ├─ data.csv
    │  └─ info.json
    └─ session_09_10_11_10592/
       ├─ data.csv
       └─ info.json
```

### Supported Query Parameters:
- project name
- subject name
- response type
- stimulus type
- headset configuration
- headset model
- collection date
- any combination of the above
    
## Database Structure
### Session Table (relational)
Stores sessions in rows whose columns are object info fields, including one for FileID

### Data Table (non-relational)
Stores all sessions as files with file IDs that correspond to a row in session table.

## Environment Setup and Package Management
### Conda (recommended)
- On Windows, open an Anaconda Prompt or an Anaconda Powershell from the start menu and navigate to where this repo is cloned.
- On Mac/Linux, open a terminal and navitage to where this repo is cloned.
- Create a new environment with `conda create env -f environment.yml`
- If environment setup or package installation fails, try
  - updating conda
  - updating pip
  - installing packages without specific version numbers
- Activate environment with `conda activate data-env`

### Other
If choosing to use a non-conda virtual environment or installing to global Python site packages, reference environment.yml when
manually installing requirements.
