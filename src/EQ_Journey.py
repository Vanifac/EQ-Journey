import json
import time
import re
import csv
from pathlib import Path
import prints as WARN

import wmi

import col
import config as cfg

# Initializing Things
c = wmi.WMI()
csv_list = cfg.csv_list


class Parser:
    def __init__(self):
        self.fast_Scan      = True
        self.active_Log     = self.get_active_log(False)
        self.name           = self.active_Log.split('/')[-1].split('_')[1]
        self.save_path      = f"saves/{self.name}.json"
        self.eq_Char        = self.load_character()
        self.new_Char       = self.eq_Char['Race'] == "Nightelf"
        self.file           = open(self.active_Log, 'r', encoding='utf-8')
        self.file_length    = self.file.seek(0, 2)

        self.file.seek(self.eq_Char['Line'], 0)
        if cfg.TEST:
            self.file.seek(0)

    # FUNCTIONS
    def get_active_log(self, silent):
        if cfg.TEST:
            log = cfg.TEST_LOG
        else:
            x, log = max((f.stat().st_mtime, str(f)) for f in Path(cfg.LOG_LOCATION).iterdir())
            while 'dbg.txt' in log:
                if not silent:
                    print(WARN.DBG_LOG)
                    silent = True
                x, log = max((f.stat().st_mtime, str(f)) for f in Path(cfg.LOG_LOCATION).iterdir())
                time.sleep(2.5)
            return log

    def load_character(self):
        try:
            with open(self.save_path) as json_file:
                eq_Char = json.load(json_file)
        except Exception:
            with open('src/data/template.json') as json_file:
                eq_Char = json.load(json_file)
                eq_Char['Name'] = self.name
        return eq_Char

    def save_it(self):
        if self.file.tell() == self.eq_Char['Line']:
            return
        with open(self.save_path, 'w') as save:
            self.eq_Char['Line'] = self.file.tell()
            save.write(json.dumps(self.eq_Char, indent=4))
            col.green('Saved.')
        self.update_csv()

    def update_csv(self):
        if cfg.CSV and not self.fast_Scan:
            with open('Active Character.csv', 'w', newline='') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=csv_list, extrasaction='ignore')
                writer.writeheader()
                writer.writerow(self.eq_Char)
            self.update_stats_csv()
            self.update_loot_csv()
            self.update_kills_csv()

    def update_stats_csv(self):
        with open(f'saves/{self.eq_Char["Name"]}_Stats.csv', 'w', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=self.eq_Char["Stats"].keys(), extrasaction='ignore')
            writer.writeheader()
            writer.writerow(self.eq_Char['Stats'])

    def update_loot_csv(self):
        top_5_loot = sorted(self.eq_Char['Looted'], key=self.eq_Char['Looted'].get, reverse=True)[:5]
        with open(f'saves/{self.eq_Char["Name"]}_Loot.csv', 'w', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=top_5_loot, extrasaction='ignore')
            writer.writeheader()
            writer.writerow(self.eq_Char['Looted'])

    def update_kills_csv(self):
        top_5_kills = sorted(self.eq_Char['Killed'], key=self.eq_Char['Killed'].get, reverse=True)[:5]
        with open(f'saves/{self.eq_Char["Name"]}_Kills.csv', 'w', newline='') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=top_5_kills, extrasaction='ignore')
            writer.writeheader()
            writer.writerow(self.eq_Char['Killed'])


def process_status():
    return next((process for process in c.Win32_Process() if process.Name == cfg.PROCESS_NAME), False)


def look_for_process():
    if cfg.TEST:
        return True
    x = 0
    while not (game_process := process_status()) and cfg.MAX_WAIT_TICKS > x:
        if x == 0:
            col.red(WARN.PROCESS_LOST)
        else:
            col.red(f'{cfg.PROCESS_NAME} missing for {x * cfg.WAIT_DURATION} seconds..')
        x += 1
        time.sleep(cfg.WAIT_DURATION)
    return game_process


def parse():
    Par = Parser()
    game_process = look_for_process()
    last_activity = time.time()
    Par.save_it()

    while game_process:
        full_Line = Par.file.readline().strip()
        now = time.time()
        # Parse it
        if full_Line:
            to_save = True
            last_activity = time.time()
            line = full_Line[27:]
            print(line)

            if 'You have become better at ' in line:
                skill_Name = line[26:line.index("!")]
                Par.eq_Char['Skills'].update({skill_Name: int(line[line.index("(")+1:-1])})

            elif 'You have entered ' in line:
                Par.eq_Char['Zone'] = line[17:-1]

            elif f"] {Par.eq_Char['Name']} (" in line and "[ANON" not in line:
                if "<" in line:
                    if Par.eq_Char['Guild'] != line[line.index('<')+1:line.index('>')]:
                        Par.eq_Char.update({"Guild": line[line.index('<')+1:line.index('>')]})
                    else:
                        to_save = False
                if Par.new_Char:
                    Par.eq_Char.update({'Level': int(line.strip("AFK")[1:line.index(' ')])})
                    Par.eq_Char.update({'Class': line[line.index(' ')+1:line.index(']')]})
                    Par.eq_Char.update({'Race': line[line.index('(')+1:line.index(')')]})
                    Par.new_Char = False
                    to_save = True

            elif 'You have slain ' in line:
                Par.eq_Char['Stats']['Kills'] += 1
                mob_name = line[15:line.index('!')]
                try:
                    Par.eq_Char['Killed'][mob_name] += 1
                except KeyError:
                    Par.eq_Char['Killed'][mob_name] = 1

            elif 'You have been slain by ' in line:
                Par.eq_Char['Stats']['Deaths'] += 1

            elif 'You gain experience!!' in line or 'You gain party experience!!' in line:
                Par.eq_Char['Stats']["Exp Ticks"] += 1

            elif 'You have gained a level! Welcome to level ' in line:
                Par.eq_Char['Level'] = int(line[42:-1])

            elif '--You have looted a ' in line:
                item_name = line[20:line.index('.--')]
                try:
                    Par.eq_Char['Looted'][item_name] += 1
                except KeyError:
                    Par.eq_Char['Looted'][item_name] = 1
            elif 'from the corpse' in line:
                print('you got cash!')
                to_save = False
            elif 'as your split' in line:
                print('you got cash!')
                to_save = False
            else:
                to_save = False
            if to_save:
                Par.save_it()

            if Par.fast_Scan and Par.file_length == Par.file.tell():
                Par.fast_Scan = False
                Par.update_csv()

        elif (now - last_activity) > cfg.TIME_BETWEEN_CHECKS:
            game_process = look_for_process()
            last_activity = time.time()
            Par.save_it()

        if (now - last_activity) > cfg.SLEEP_TIMER:
            if Par.active_Log != Par.get_active_log(True):
                print('New active log found.')
                Par.file.close()
                parse()
            time.sleep(10)
        elif not Par.fast_Scan:
            time.sleep(.1)


# Do the Thing

parse()

col.red(f'{cfg.PROCESS_NAME} not found, closing..')
time.sleep(2)
