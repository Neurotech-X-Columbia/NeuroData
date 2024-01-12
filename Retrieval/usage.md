## Retrieval Script
### Usage

```
usage: retrieve.py [-h] [-p PROJECT_NAME] [-n SUBJECT_NAME]
                   [-r RESPONSE_TYPE] [-s STIMULUS_TYPE]
                   [-c HEADSET_CONFIGURATION] [-m HEADSET_MODEL]
                   [-b BEFORE_DATE] [-a AFTER_DATE]

Queries revidis for relevant data sessions and downloads folder of results.

options:
  -h, --help            show this help message and exit
  -p PROJECT_NAME, --project-name PROJECT_NAME
                        Project name
  -n SUBJECT_NAME, --subject-name SUBJECT_NAME
                        The name of a particular data collection subject
  -r RESPONSE_TYPE, --response-type RESPONSE_TYPE
                        EEG Response Type (SSVEP|ERP|other)
  -s STIMULUS_TYPE, --stimulus-type STIMULUS_TYPE
                        Stimulus type (visual|audio|other)
  -c HEADSET_CONFIGURATION, --headset-configuration HEADSET_CONFIGURATION
                        Headset configuration (standard|occipital|other)
  -m HEADSET_MODEL, --headset-model HEADSET_MODEL
                        Headset model (CytonDaisy|Cyton)
  -b BEFORE_DATE, --before-date BEFORE_DATE
                        only include data collected before this date (MM-DD-YYYY) (inclusive); defaults to now
  -a AFTER_DATE, --after-date AFTER_DATE
                        only include data collected after this date (MM-DD-YYYY) (inclusive); defaults to 10 years ago
```

**Before using this script or the upload_session script, ensure you have exported your Redivis API token in your terminal.**
In terminal, run `export REDIVIS_API_TOKEN=your_access_token`.
In Windows Powershell, run `$Env:REDIVIS_API_TOKEN = 'your access token'`.
If you don't have a Redivis API token, generate one in the [Redivis profile settings](https://redivis.com/workspace/settings/tokens).
