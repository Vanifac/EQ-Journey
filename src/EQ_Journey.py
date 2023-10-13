import csv
import json
import os
import re
import time
import datetime as dt
from pathlib import Path

import wmi

import config as cfg
import strings as STRI

# Initializing Things
c = wmi.WMI()
csv_list = cfg.csv_list

try:
    os.mkdir('Characters')
except FileExistsError:
    pass
try:
    os.mkdir('Active_Character')
except FileExistsError:
    pass


class Parser:
    def __init__(self):
        self.fast_Scan      = True
        self.active_Log     = get_active_log(False)
        self.name           = self.active_Log.split('/')[-1].split('_')[1]
        self.server         = self.get_server()

        self.save_dir       = self.create_save_dir()
        self.save_path      = f"{self.save_dir}/{self.name}-{self.server}.json"

        self.eq_Char        = False
        self.eq_Char        = self.load_character()
        self.new_Char       = self.eq_Char['Race'] == "Nightelf"

        self.file           = open(self.active_Log, 'r', encoding='utf-8')
        self.file_length    = self.file.seek(0, 2)

        self.last_cast      = ''
        self.last_save      = time.time()
        self.session        = False
        self.per_tick       = 0

        self.file.seek(self.eq_Char['Line'], 0)
        if cfg.TEST:
            self.file.seek(0)

    # FUNCTIONS
    def get_server(self):
        match self.active_Log.split('/')[-1].split('_')[2]:
            case 'P1999Green.txt':
                return "Green"
            case 'project1999.txt':
                return "Blue"
            case 'P1999PVP.txt':
                return "Red"
            case 'pq.proj.txt':
                return "Quarm"
            case 'loginse.txt':
                return "TAKP"
            case _:
                return "Unknown"

    def create_save_dir(self):
        save_dir = f"Characters/{self.server}-{self.name}"
        try:
            os.mkdir(save_dir)
        except FileExistsError:
            pass
        with open(f'{save_dir}/{self.name}_Zones.txt', 'a+', encoding='utf-8') as f:
            if f.tell() == 0:
                f.write('Zone Journal\n')
        if not os.path.isfile(f'{save_dir}/{self.name}_Level-Stats.csv'):
            with open(f'{save_dir}/{self.name}_Level-Stats.csv', 'w', newline='') as f:
                rowwriter = csv.writer(f)
                top = ['Level', 'Zone', 'Kills', 'Deaths', 'Spell Casts',
                       'Exp Ticks', 'Items Looted', 'PP Earned', 'PP Spent']
                rowwriter.writerow(top)
        return save_dir

    def load_character(self):
        try:
            with open(self.save_path) as json_file:
                self.eq_Char = json.load(json_file)
        except Exception:
            with open('Characters/template/template.json') as json_file:
                self.eq_Char = json.load(json_file)
                self.eq_Char['Name']     = self.name
                self.eq_Char['Server']   = self.server
        return self.eq_Char

    def convert_coins(self, coins, in_or_out):
        for coin in coins:
            denom = f"{coin[1][0].upper()}P"
            self.eq_Char['Coin'][in_or_out][denom] += int(coin[0])
        self.eq_Char['Coin'][in_or_out]['SP'] += self.eq_Char['Coin'][in_or_out]['CP'] // 10
        self.eq_Char['Coin'][in_or_out]['CP']  = self.eq_Char['Coin'][in_or_out]['CP'] % 10
        self.eq_Char['Coin'][in_or_out]['GP'] += self.eq_Char['Coin'][in_or_out]['SP'] // 10
        self.eq_Char['Coin'][in_or_out]['SP']  = self.eq_Char['Coin'][in_or_out]['SP'] % 10
        self.eq_Char['Coin'][in_or_out]['PP'] += self.eq_Char['Coin'][in_or_out]['GP'] // 10
        self.eq_Char['Coin'][in_or_out]['GP']  = self.eq_Char['Coin'][in_or_out]['GP'] % 10

    def save_it(self):
        if self.file.tell() == self.eq_Char['Line']:
            return
        with open(self.save_path, 'w') as save:
            self.eq_Char['Line'] = self.file.tell()
            save.write(json.dumps(self.eq_Char, indent=4))
            if not self.fast_Scan:
                print(f"{'Saved.' :-^41}")
        self.update_csvs()
        self.last_save = time.time()

    def update_csvs(self):
        if cfg.CSV and not self.fast_Scan:
            self.update_info_csv()
            csvs_to_export = ["Stats", "Loot", "Kills", "Skills"]
            if self.eq_Char['Stats']['Spell Casts'] > 0:
                csvs_to_export.append("Spells")
            for category in csvs_to_export:
                self.update_sub_csvs(category)

    def update_info_csv(self):
        for file_name in ['Active_Character/Info.csv', f'{self.save_dir}/Info.csv']:
            with open(file_name, 'w', newline='') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=csv_list, extrasaction='ignore')
                writer.writeheader()
                writer.writerow(self.eq_Char)

    def update_sub_csvs(self, category):
        for file_name in [f'Active_Character/{category}', f'{self.save_dir}/{category}']:
            if category == "Stats":
                top_x_list = list(self.eq_Char[category].keys())
            elif category in ["Spells", "Skills"]:
                top_x_list = sorted(self.eq_Char[category], key=self.eq_Char[category].get, reverse=True)
            else:
                top_x_list = sorted(self.eq_Char[category], key=self.eq_Char[category].get, reverse=True)[:cfg.TOP]
            with open(f'{file_name}.csv', 'w', newline='') as csvfile:
                csvwriter = csv.DictWriter(csvfile, fieldnames=top_x_list, extrasaction='ignore')
                csvwriter.writeheader()
                csvwriter.writerow(self.eq_Char[category])
            if category not in ['Skills', 'Stats'] and cfg.LEVELUPLARRY:
                top_x_list_vals = list(self.eq_Char[category].values())
                with open(f'{file_name}-Names.csv', 'w', newline='') as csvfile:
                    rowwriter = csv.writer(csvfile)
                    rowwriter.writerow(range(1, cfg.TOP+1))
                    rowwriter.writerow(top_x_list)
                with open(f'{file_name}-Numbers.csv', 'w', newline='') as csvfile:
                    rowwriter = csv.writer(csvfile)
                    rowwriter.writerow(range(1, cfg.TOP+1))
                    rowwriter.writerow(top_x_list_vals)

    def zone_journal(self, full_Line):
        with open(f'{self.save_dir}/{self.name}_Zones.txt', 'a+') as j:
            j.seek(0)
            last_line = j.readlines()[-1]
            if full_Line[27:] not in last_line[27:]:
                j.write(f'{full_Line}\n')

    def per_level_stats(self):
        lev_path = f'{self.save_dir}/{self.name}_Level-Stats.csv'
        level_line = [self.eq_Char['Level'], self.eq_Char['Zone'], self.eq_Char['Stats']['Exp Ticks'],
                      self.eq_Char['Stats']['Kills'], self.eq_Char['Stats']['Deaths'],
                      self.eq_Char['Stats']['Spell Casts'], self.eq_Char['Stats']['Items Looted'],
                      self.eq_Char['Coin']['Earned']['PP'], self.eq_Char['Coin']['Spent']['PP']]
        with open(lev_path, 'a', newline='') as lev:
            rowwriter = csv.writer(lev)
            rowwriter.writerow(level_line)

    # Commands
    def eqj_session_command(self, line):
        if self.fast_Scan:
            return
        try:
            cmd = re.findall(r'^eqj-(start-|reset-|status-|end)(?:(\d+)) is not online at this time', line.lower())[0]
        except Exception:
            return
        if 'start-' in cmd and not self.session:
            self.cmd_session_start(cmd)
        elif 'reset-' in cmd:
            self.cmd_session_start(cmd)
        elif 'status-' in cmd and self.session:
            self.cmd_session_status(cmd)
        elif 'end' in cmd and self.session:
            self.session = False

    def cmd_session_start(self, cmd):
        print(f"{'New tracking session started!' :-^41}")
        self.session        = True
        self.start_time     = time.time()
        self.start_ticks    = self.eq_Char['Stats']['Exp Ticks']
        self.start_exp      = int(cmd[1])
        self.start_lvl      = self.eq_Char['Level']
        self.per_tick       = 0
        self.exp            = self.start_exp
        self.start_plat     = self.eq_Char['Coin']['Earned']['PP']
        with open('Active_Character/SessionStats.txt', 'w') as sesh:
            sesh.write(f"{'Session Stats' :-^41}\n")
            sesh.write(f"{'Current: ' :>14}{self.exp:<5}")

    def cmd_session_status(self, cmd):
        try:
            self.exp        = float(cmd[1])
            if self.exp > 100:
                self.exp %= 100
            dur             = int((time.time() - self.start_time)/60)
            gained          = round((self.exp - self.start_exp) + ((self.eq_Char['Level'] - self.start_lvl)*100), 2)
            ticks           = self.eq_Char['Stats']['Exp Ticks'] - self.start_ticks
            self.per_tick   = round(gained / ticks, 2)
            exp_per_hour    = f'{round((gained/dur)*60, 1)}%'
            time_to_ding    = round((((100-(self.exp) % 100)) / (gained/dur)), 1)
            ding_at         = (dt.datetime.now() + dt.timedelta(minutes=time_to_ding))
            pp_gained       = self.eq_Char['Coin']['Earned']['PP'] - self.start_plat
            pp_per_hr       = round((pp_gained/dur)*60, 1)
            pp_per_tic      = round(pp_gained/ticks, 1)

            with open('Active_Character/SessionStats.txt', 'w') as sesh:
                sesh.write(f"{'Session Stats' :-^41}\n")
                sesh.write(f"{'Current: ' :>14}{self.exp:<5}|{'Kills: ' :>12}{ticks}\n")
                sesh.write(f"{'Exp Earned: ':>14}{gained:<5}|{'PP Earned: ' :>12}{pp_gained}\n")
                sesh.write(f"{'Exp/Kill: ':>14}{self.per_tick:<5}|{'PP/Kill: ':>12}{pp_per_tic}\n")
                sesh.write(f"{'Exp/Hour: ':>14}{exp_per_hour:<5}|{'PP/Hour: ' :>12}{pp_per_hr}\n")
                sesh.write(f"{'Duration: ':>14}{dur:<5}|{'Ding @: ':>12}{ding_at.strftime('%a %I:%M%p')}")
            print(f'{"Session Text Updated." :-^41}')
        except ZeroDivisionError:
            print(f'{"Not enough data yet." :-^41}')
        except Exception as e:
            print(e)

    def auto_status(self):
        if self.per_tick == 0 or not self.session:
            return
        exp_guess = round(self.exp + self.per_tick, 2)
        cmd = ['status', exp_guess]
        self.cmd_session_status(cmd)

    def eqj_wiki_command(self, line):
        if self.fast_Scan:
            return
        try:
            cmd = re.findall(r'^eqj-(wiki)(?:(-\w+)) is not online at this time', line.lower())[0]
        except Exception:
            return

        if 'start' in cmd:
            self.cmd_session_start(cmd)
        elif 'reset-' in cmd:
            self.cmd_session_start(cmd)
        elif 'status-' in cmd and self.session:
            self.cmd_session_status(cmd)
        elif 'end' in cmd and self.session:
            self.session = False


######################################
def process_status():
    return next((process for process in c.Win32_Process() if process.Name == cfg.PROCESS_NAME), False)


def look_for_process():
    if cfg.TEST:
        return
    x = 0
    while not (game_process := process_status()) and cfg.MAX_WAIT_TICKS > x:
        if x == 0:
            print(STRI.PROCESS_LOST)
        else:
            print(f'{cfg.PROCESS_NAME} missing for {x * cfg.WAIT_DURATION} seconds..')
        x += 1
        time.sleep(cfg.WAIT_DURATION)
    if not game_process:
        print(f'{cfg.PROCESS_NAME} not found, closing..')
        time.sleep(2)
        quit()


def recent_modified_log():
    log = ""
    try:
        x, log = max((f.stat().st_mtime, str(f)) for f in Path(cfg.LOG_LOCATION).iterdir())
    except:
        try:
            x, log = max((f.stat().st_mtime, str(f)) for f in Path(cfg.EQ_LOCATION).iterdir()
                       if 'eqlog' in str(f).split("\\")[-1].split("_")
                       and ('loginse.txt' in str(f).split("\\")[-1].split("_")
                            or 'pq.proj.txt' in str(f).split("\\")[-1].split("_")))
        except Exception:
            with open('errorlog.txt', 'a', encoding='utf-8') as f:
                f.write(f'{"Could not find any compatable EQ logs. Verify the install location and that logs are enabled."}\n{Exception}')
    return log


def get_active_log(silent):
    if cfg.TEST:
        return cfg.TEST_LOG
    x = 0
    log = recent_modified_log()
    while 'dbg.txt' in log or 'sky.txt' in log:
        print("they're in log!")
        if not silent:
            print(STRI.DBG_LOG)
            silent = True
        log = recent_modified_log()
        if x % 15 == 0:
            look_for_process()
        x += 1
        time.sleep(1)
    return log


def parse():
    try:
        look_for_process()
        Par = Parser()
        print(f'Parsing {Par.eq_Char["Name"]} from {Par.active_Log}')
        last_activity = time.time()
        Par.start_time = time.time()
        Par.save_it()
        to_save = False

        while True:
            full_Line = Par.file.readline().strip()
            now = time.time()
            # Parse it
            if full_Line:
                last_activity = time.time()
                line = full_Line[27:]
                if not Par.fast_Scan:
                    print(full_Line)

                # General info
                if 'You have entered ' in line and 'an Arena (PvP) area' not in line:
                    Par.eq_Char['Zone'] = line[17:-1]
                    Par.zone_journal(full_Line)
                    to_save = True

                elif f"] {Par.eq_Char['Name']} (" in line and "[ANON" not in line:
                    who = re.findall(r'^(?:.+)?\[(\d+) (.+)\] \w+ \((.+)\)(?: <(.+)>)?', line)[0]
                    if who[3] != Par.eq_Char["Guild"]:
                        Par.eq_Char.update({"Guild": who[3]})
                        to_save = True
                    if Par.new_Char:
                        Par.eq_Char.update({'Level': int(who[0])})
                        Par.eq_Char.update({'Class': who[1]})
                        Par.eq_Char.update({'Race': who[2]})
                        Par.new_Char = False

                # Spells / Skills
                elif 'You have become better at ' in line:
                    skill_Name = line[26:line.index("!")]
                    Par.eq_Char['Skills'].update({skill_Name: int(line[line.index("(")+1:-1])})

                elif 'You begin casting ' in line:
                    Par.last_cast = line[18:-1]
                    Par.eq_Char['Stats']['Spell Casts'] += 1
                    try:
                        Par.eq_Char['Spells'][Par.last_cast] += 1
                    except KeyError:
                        Par.eq_Char['Spells'][Par.last_cast] = 1
                    to_save = True

                elif 'Your spell fizzles!' in line:
                    Par.eq_Char['Stats']['Fizzles'] += 1
                    if Par.last_cast != '':
                        Par.eq_Char['Spells'][Par.last_cast] -= 1
                        Par.last_cast = ''
                    to_save = True

                elif 'Your spell is interrupted.' in line:
                    Par.eq_Char['Stats']['Interrupts'] += 1
                    if Par.last_cast != '':
                        Par.eq_Char['Spells'][Par.last_cast] -= 1
                        Par.last_cast = ''
                    to_save = True

                elif 'bandag' in line or 'You cannot bind wounds above ' in line:
                    if 'You begin to bandage ' in line:
                        Par.eq_Char['Stats']['Bandages Used'] += 1
                    elif line in STRI.BANDAGE_LOST:
                        Par.eq_Char['Stats']['Bandages Wasted'] += 1

                # Kills / Killed by
                elif 'You have slain ' in line:
                    Par.eq_Char['Stats']['Kills'] += 1
                    mob_name = line[15:line.index('!')]
                    try:
                        Par.eq_Char['Kills'][mob_name] += 1
                    except KeyError:
                        Par.eq_Char['Kills'][mob_name] = 1

                elif 'You have been slain by ' in line or 'You have died' in line:
                    Par.eq_Char['Stats']['Deaths'] += 1
                    to_save = True

                # Levels / EXP
                elif 'You gain experience!!' in line:
                    Par.eq_Char['Stats']["Exp Ticks"] += 1
                    Par.eq_Char['Stats']["Solo Exp Ticks"] += 1
                    to_save = True
                    Par.auto_status()

                elif 'You gain party experience!!' in line:
                    Par.eq_Char['Stats']["Exp Ticks"] += 1
                    Par.eq_Char['Stats']["Party Exp Ticks"] += 1
                    to_save = True
                    Par.auto_status()

                elif 'You have gained a level! Welcome to level ' in line:
                    Par.eq_Char['Level'] = int(line[42:-1])
                    Par.per_level_stats()
                    to_save = True

                # Loot / Coin
                elif '--You have looted a ' in line:
                    item_name = line[20:-3]
                    Par.eq_Char["Stats"]["Items Looted"] += 1
                    try:
                        Par.eq_Char['Loot'][item_name] += 1
                    except KeyError:
                        Par.eq_Char['Loot'][item_name] = 1
                    to_save = True

                elif re.match('^You receive (.+) (from|as|pieces)(.+)', line):
                    Par.convert_coins(re.findall(r'(\d+) (\w+)', line), "Earned")
                    to_save = True

                elif re.match('^You give (.+) to (.+).', line):
                    Par.convert_coins(re.findall(r'(\d+) (\w+)', line), "Spent")
                    to_save = True

                # Hits
                elif re.match(f'^{Par.name} (lands|Scores) a (critical hit|Crippling Blow)!', line):
                    typ, hit = re.findall(r'(critical hit|Crippling Blow|\d+)', line)
                    Par.eq_Char['Stats'][typ.title()] = max(Par.eq_Char['Stats'][typ.title()], int(hit))

                elif re.match(r'eqj-(.+) is not online at this time.', line.lower()):
                    Par.eqj_session_command(line)

                # Disable fast_Scan once the log has caught up to the end.
                # I would do >= if but there's something with the "---" line when you /who
                # where it returns an astronomically high file position and will trigger this way too early
                if Par.fast_Scan and (Par.file_length == Par.file.tell()):
                    Par.fast_Scan = False
                    to_save = True

            # Save when flagged and if it's been over 5 seconds since last save.
            if (to_save and (now - Par.last_save) > 10) or (now - Par.last_save) > 60:
                Par.save_it()
                to_save = False

            # Throttle parse rate / Log and Process checks if no activity / disable fast_Scan just in case
            if (now - last_activity) > cfg.SLEEP_TIMER:
                Par.fast_Scan = False

                # Verify Active Log
                if Par.active_Log != get_active_log(True):
                    print('New active log found..')
                    Par.file.close()
                    parse()

                # Verify eqgame.exe Process
                if (now - last_activity) > cfg.TIME_BETWEEN_CHECKS:
                    look_for_process()
                    last_activity = time.time()

                # Longer wait if "sleeping"
                time.sleep(0.5)

            # Shorter wait if parsing. No wait if fast_Scan.
            elif not Par.fast_Scan:
                time.sleep(.01)
    except Exception:
        with open('errorlog.txt', 'a', encoding='utf-8') as f:
            f.write(f'{line}\n{Exception}')


# Do the Thing
parse()
