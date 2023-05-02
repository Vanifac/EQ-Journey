# sourcery skip: merge-dict-assign
from configparser import ConfigParser
from tkinter import Tk, filedialog

# CONFIG
TEST = False
config_object = ConfigParser()

PROCESS_NAME = "eqgame.exe"
CONFIG_NAME = 'config.ini'
CONFIG_EQ_KEY = 'EVERQUEST_DATA'
CONFIG_GAME_DIR_KEY = 'game_directory'

TIME_BETWEEN_CHECKS = 180
SLEEP_TIMER = 15
WAIT_DURATION = 10
MAX_WAIT_TIME = 30
MAX_WAIT_TICKS = MAX_WAIT_TIME / WAIT_DURATION

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
    eqdata['CSV Output'] = False
    eqdata['TXT Output'] = False

    config_object[CONFIG_EQ_KEY] = eqdata
    with open(CONFIG_NAME, 'w') as conf:
        config_object.write(conf)

EQ_LOCATION     = eqdata[CONFIG_GAME_DIR_KEY]
LOG_LOCATION    = f'{EQ_LOCATION}/Logs/'
TEST_LOG        = "eqlog_Testiex_P1999Green.txt"
CSV             = eqdata['CSV Output']

csv_list = ['Name', 'Level', 'Race', 'Class', 'Zone', 'Guild']
