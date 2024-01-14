## Upload Script
### Usage

```
usage: upload_session.py [-h] -s SESSION_PATH -u USERNAME

Uploads data session to Redivis

options:
  -h, --help            show this help message and exit
  -s SESSION_PATH, --session-path SESSION_PATH
                        Path to session directory
  -u USERNAME, --username USERNAME
                        Your Redivis username
```

**Before using this script or the retrieve.py script, ensure you have exported your Redivis API token in your terminal.**
In terminal, run `export REDIVIS_API_TOKEN=your_access_token`.
In Windows Powershell, run `$Env:REDIVIS_API_TOKEN = 'your access token'`.
If you don't have a Redivis API token, generate one in the [Redivis profile settings](https://redivis.com/workspace/settings/tokens).
