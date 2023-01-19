


      





def build_filename(self):
    self.filename = self.base_directory + self.logs_directory + \
        'eqlog_' + self.char_name + '_' + self.server_name + '.txt'
        
# open the file
# seek file position to end of file if passed parameter 'seek_end' is true
def open(self, author, seek_end=True):
    try:
        self.file = open(self.filename)
        if seek_end:
            self.file.seek(0, os.SEEK_END)
        self.author = author
        self.set_parsing()
        return True
    except Exception:
        return False
    
# close the file
def close(self):
    self.file.close()
    self.author = ''
    self.clear_parsing()
# get the next line
def readline(self):
    if self.is_parsing():
        return self.file.readline()
    else:
        return None
    
    
class Character:
def __init__(self, char_name):
    self.name    = char_name
    self.level   = 1
    self.eqclass = input
    