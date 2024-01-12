#!/bin/bash

# Iterate through all folders in the current directory
for folder in */; do
    folder_name="${folder%/}"

    # Run upload_session.py with required flags and automatically input 'y'
    echo "Running upload_session.py for folder: $folder_name"
    yes | python3 upload_session.py -s "$folder_name" -u matheu_campbell

    echo "$folder_name uploaded."

done