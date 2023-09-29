# Data Collection Procedure
Data collection is at best a long and boring process, so here's a guide to minimize obstacles.

## Preparation
1. Find a subject. Think about your project or application and which subjects would be best suited. Note that, generally, people with shorter hair make for easier and cleaner data collection.
2. Before running a data collection session, decide on a time and location. Plan when and where to get the headset and who to get it from. Let people know where it'll go afterwards.
3. Design your data collection session. Think about the reaction you want to measure and how you will induce it. Also think about how you will record it.

### Design Considerations
- What is the session structure? Are you incorporating breaks into your session design? Have you defined a stim cycle?
- If using a script to generate stimulus, have you tested it on the laptop that'll run it for the session? Have you set up the proper environment?
- Are there hardware considerations to make (monitor refresh rate, monitor size, brightness, etc.)?
- How are you recording the data? Using DataGUI.py or one of its binaries is strongly recommended. Have you tested it on your laptop? If using another script, make sure to test it and conform to the info.json conventions.
- If using OpenBCI's GUI for data collection, make sure to create a session folder in the expected format and an info JSON that describes the session.
- Who's administering the session and who is undergoing data collection? Does the subject know the purpose and understand the session design?

## Collection Steps
### Setup
1. Loosen electrodes as necessary to fit the headset somewhat comfortably on the subject's head.
2. Clip voltage references to the subject's earlobes.
3. Plug the Cyton dongle into your PC. The switch on the side should be in the GPIO 6 position (closest to your laptop).
    - On Windows, note the active serial ports in your device manager before and after plugging in the board to determine which one is correct.
4. Turn on the Cyton board by moving the switch to the PC position. If a blue LED does not turn on, press the reset button. If not it still does not light, the batteries may be dead.

### Electrode Tuning
1. Open the OpenBCI GUI. Select live data transfer from Cyton using the serial transfer protocol. Choose the appropriate serial port or try auto-discovery.
    - Windows serial ports are formatted as COM<NUMBER>
    - Max/Linux serial ports are formatted as /dev/tty.<NAME>
2. Start the system via the GUI. The board should initialize a connection and open to the GUI.
3. Switch the GUI view to see the head plot (mapping of electrodes on a top-down view of a head) and the time-series data stream. For the electrodes of interest, ensure their time-series 
   channels are _not railed_. Railed channels are saturated at unexpected bounds, so they are probably not recording useful data. To fix railed channels, adjust electrodes in and out until
   the channel is consistently not railed.

### Collection
1. When you're satisfied that your electrodes are properly aligned, close the OpenBCI GUI. Open the DataGUI from this repo, and fill out the form with your session details.
    - If running the DataGUI in Python (not using one of the binaries in the release section), create a conda environment from the environment.yml file at the top level of this repo. If you don't have conda/don't want to install it, just install
      the modules imported by DataGUI.py to whichever local environment you're using. Python 3.8+ is required. When you've ensured you're in the correct environment, just run main.py.
    - No Python environment required to run DataGUI.exe, but it's a very large file and may take some time to open (> 30 seconds). Don't give up if it seems to be taking long.
2. Prepare a stimulus script if you have one, and position the subject for collection.
3. When ready, press the confirm button of the DataGUI, start your stimulus script, and guide the subject as necessary during collection.
4. When finished, press stop (or allow time to elapse) in the DataGUI. Your session directory will be created with an info.json file, sessionlog.log file, and data.csv file.
5. Your data collection is complete.

## Uploading
1. In a terminal, export the API key environment variable from your Redivis account. Generate one if necessary.
2. Run upload_session.py from this repository. Follow the instructions to provide your session directory.
3. You may need to be granted access to our dataset. Slack Matheu for access. If all else fails, email a .zip to mgc2171@columbia.edu.
4. Your session should be uploaded!
