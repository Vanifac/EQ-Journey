import config as cfg


DBG_LOG = 'Waiting for a valid active log. Ensure logging is enabled in-game. If this problem persists, verify you have selected the correct install location.'

PROCESS_LOST = f'{cfg.PROCESS_NAME} not found. Re-Checking every, {cfg.WAIT_DURATION} seconds for {cfg.MAX_WAIT_TIME} seconds.'

BANDAGE_LOST = [
    'You have moved and your attempt to bandage has failed.',
    'The person you were bandaging has moved away.',
    r'You cannot bind wounds above 50% hitpoints.',
    r'You cannot bind wounds above 70% hitpoints.'
    ]
