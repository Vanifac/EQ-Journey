import config as cfg


DBG_LOG = ['Waiting for a valid active log. Ensure logging is enabled in-game.',
           'If this problem persists, verify you have selected to correct install location.']

PROCESS_LOST = [f'{cfg.PROCESS_NAME} not found. Re-Checking every,'
                f'{cfg.WAIT_DURATION} seconds for {cfg.MAX_WAIT_TIME} seconds.']
