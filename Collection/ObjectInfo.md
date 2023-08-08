## JSON Info Objects
Every data collection session should have an accompanying JSON info object that contains metadata about the session. Below are examples of the expected format of these JSON info objects and a description of the required fields. Extra fields may be added as necessary as long as the required fields are satisfied. All JSON keys should be strings, and all values should be strings or numbers. Info JSON objects can be created manually, but they will usually be created interactively through the collection script.

## A note on blocks, block length, and the stim cycle.
To standardize the description of how each data session is carried out, we split one data collection
session into evenly sized blocks. "BlockSize" is given in seconds. We know how long the session is by how many blocks are in it, and
we know what happened during each part of the collection session by the stim cycle encoding.
A stim cycle is given as a binary word where a 0 denotes no stimulus and 1 denotes stimulus.

Ex 1: A 120 second session in which the participant looks at a flashing light for 60 seconds, rests for 30 seconds, looks at the light again for 60 seconds, rests for 30 seconds, and looks at the light again for 60 seconds.

BlockLength: 30
BlockCount: 9
StimCycle: 11011011

Ex 2: A 200-second session in which the participant sees a series of images. In every 20-second period except two (predetermined), an image that is "out of place" appears on the screen at some point.

BlockLength: 20
BlockCount: 10
StimCycle: 1101011111

Some session designs may not completely fit this encoding. In those cases, make sure to fully describe the design in the "Description" field (outside of the SessionParams subfield). 

Ex 3: A 120-second session in which the participant blinks whenever they want. Blinks are marked in annotations.

BlockLength: 120
BlockCount: 1
StimCycle: 1
Description: Subject blinked as natural while watching a two minute video, clicking the mouse every time they blinked.

## Required Fields (S3Path and SessionID generated by upload_session script)
**SessionParams**: A list of parameters pertaining to the collection session
    **SubjectName**: The subject's name
    **ResponseType**: The relevant neural response (usually ERP or SSVEP, but may be something else)
    **StimulusType**: Type of stimulus, e.g. audio, visual, other
    **BlockLength**: Length in seconds of block of the session
    **BlockCount**: Number of blocks in the session
    **StimCycle**: Stimulus/Rest cycle encoded by 1s and 0s
**HardwareParams**:
    **SampleRate**: Sampling rate of the headset (250 for 8-channel operation, 125 for 16 channel operation)
    **HeadsetConfiguration**: Positioning of the electrodes in the headset. Usually "standard", may be "occipital" for half-brain setup for SSVEP recording
    **HeadsetModel**: Headset board. Currently CytonDaisy (16 channel) and Cyton (8 channel) are the only options.
    **BufferSize**: Size of the ring buffer on the headset board. Dependent on the data collection script.
**ProjectName**: Name of the project the data collection is for
**Description**: Description of the data collection session
**Annotations**: List of (time, note) pairs.
**Date**: Date of recording
**Time**: Time of recording
**S3Path**: Path to where .csv is stored on S3
**SessionID**: 5 digit number that identifies this session

### Sample Info for 3-stimulus SSVEP session
{
    "SessionParams" : {
        "SubjectName" : "Matheu Campbell",
        "ResponseType" : "SSVEP",
        "StimulusType" : "visual",
        "BlockLength" : 30,
        "BlockCount" : 10,
        "StimCycle" : 1101101101
    },
    "HardwareParams" : {
        "SampleRate" : 125,
        "HeadsetConfiguration" : "Standard",
        "HeadsetModel" : "CytonDaisy",
        "BufferSize" : 400000
    },
    "ProjectName" : "Speller",
    "Description" : "low room lighting and 144Hz external monitor, freqs 8/10/15 Hz",    
    "Timestamps" : [[0.00, "t1"], [90.00, "t2"], [180.00, "t3"], [210.00, "t4"]],
    "Date" : "12-03-22",
    "Time" : "15:44",
    "S3Path" : "s3://neuro-session-bucket/15422_12-03-22.csv",
    "SessionID": 15422
}

### Sample Info for audio ERP session
{
    "SessionParams" : {
        "SubjectName" : "Matheu Campbell",
        "SubjectID" : 10025,
        "ResponseType" : "ERP",
        "StimulusType" : "audio",
        "BlockLength" : 300,
        "BlockCount" : 1,
        "StimCycle" : 1
    },
    "HardwareParams" : {
        "SampleRate" : 125,
        "HeadsetConfiguration" : "Standard",
        "HeadsetModel" : "CytonDaisy",
        "BufferSize" : 400000
    },
    "ProjectName" : "Drone",
    "Description" : "Sennheiser over-ear headphones, randomly timed stimulus",    
    "Annotations" : [[14.63, "A3"], [24.46, "B4"], [46.23, "C7"], [60.45, "D#4"], [20.66, "Eb4"]],
    "Date" : "11-15-23",
    "Time" : "17:38"
    "S3Path" : "https://neurobucket.s3.amazonaws.com/19937"
    "SessionID": 19937
}

### Sample Info for generic data collection session
{
    "SessionParams" : {
        "SubjectName" : "Matheu Campbell",
        "SubjectID" : 10025,
        "ResponseType" : "custom",
        "StimulusType" : "custom",
    },
    "HardwareParams" : {
        "SampleRate" : 125,
        "HeadsetConfiguration" : "Standard",
        "HeadsetModel" : "CytonDaisy",
        "BufferSize" : 400000
    },
        "ProjectName" : "EEG Guitar",
    "Description" : "Right index finger moved every 5 seconds",
    "Annotations" : [],
    "Date" : "11-15-23",
    "Time" : "17:38",
    "S3Path" : "https://neurobucket.s3.amazonaws.com/19456"
    "SessionID": 19945
}