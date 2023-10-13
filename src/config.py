# sourcery skip: merge-dict-assign
from configparser import ConfigParser
from tkinter import Tk, filedialog

# CONFIG
TEST = False
log_to_read = 'eqlog_Vlex_P1999Green.txt'
config_object = ConfigParser()

PROCESS_NAME        = "eqgame.exe"
CONFIG_NAME         = 'config.ini'
CONFIG_EQ_KEY       = 'EVERQUEST_DATA'
CONFIG_GAME_DIR_KEY = 'game_directory'

TIME_BETWEEN_CHECKS = 5 if TEST else 60
SLEEP_TIMER         = 1 if TEST else 10
WAIT_DURATION       = 10
MAX_WAIT_TIME       = 600
MAX_WAIT_TICKS      = MAX_WAIT_TIME / WAIT_DURATION

# Load saved info
eqdata = None
try:
    config_object.read(CONFIG_NAME)
    eqdata = config_object[CONFIG_EQ_KEY]
except Exception:
    pass

if eqdata is None:
    print('Select where P99 Everquest is Installed ie C:\\Everquest')
    root = Tk()
    root.withdraw()  # Hide small window
    root.attributes('-topmost', True)  # Opened windows will be active. above all windows despite of selection
    eqdata = {CONFIG_GAME_DIR_KEY: filedialog.askdirectory(title="Everquest Directory")}
    eqdata['TAKP']              = False
    eqdata['CSV Output']        = True
    eqdata['TXT Output']        = False
    eqdata['Top List Length']   = 10

    config_object[CONFIG_EQ_KEY] = eqdata
    with open(CONFIG_NAME, 'w') as conf:
        config_object.write(conf)

EQ_LOCATION     = eqdata[CONFIG_GAME_DIR_KEY]
LOG_LOCATION    = f'{EQ_LOCATION}/Logs/'
TEST_LOG        = log_to_read
CSV             = eqdata['CSV Output']
TAKP            = eqdata['TAKP']
TOP             = int(eqdata['Top List Length'])

try:
    LEVELUPLARRY = eqdata['LEVELUPLARRY']
except KeyError:
    LEVELUPLARRY = False


# # Auto Enable Logging
# eq_log_setting = None
# try:
#     config_object.read(f"{EQ_LOCATION}/eqclient.ini")
#     eq_log_setting = config_object['DEFAULTS']
# except Exception:
#     pass

# Variables for outputs
csv_list = ['Name', 'Level', 'Race', 'Class', 'Zone', 'Guild', "Server"]
