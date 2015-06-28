from util.crc32 import crc32_from_file
from PyQt4.QtGui import QApplication, QProgressDialog
import PyQt4
import os
import chess
import shutil
import pickle

class Database():

    def __init__(self, filename):
        super(Database, self).__init__()
        self.filename = filename
        self.offset_headers = []
        self.checksum = None
        self.game_open = False
        self.game_open_idx = None
        self.unsaved_changes = False

    def create_new_pgn(self,gamestate = None):
        filename = self.filename
        f = open(filename, 'w')
        f.close()
        self.filename = filename
        if(not gamestate == None):
            f = open(filename,'a')
            print(gamestate.current.root(), file=f, end="\n\n")
            f.close()
            self.game_open = True
            self.game_open_idx = 0
            self.unsaved_changes = False
            self.init_from_file1()
            print(str(self.offset_headers))

    def add_index_for_current(self):
        self.game_open_idx = len(self.offset_headers) - 1

    def save_as_new(self,mainWindow, gamestate,new_filename):
        if(new_filename == self.filename):
            self.save_all(mainWindow, gamestate)
        else:
            shutil.copy(self.filename,new_filename)
            self.filename = new_filename
            self.save_all(mainWindow, gamestate)


    def save_all(self, mainWindow, gamestate):
        # create a new temp file
        if not self.is_consistent():
            raise IOError("database file has changed on disk - index is inconsistent")
        pDialog = QProgressDialog(mainWindow.trUtf8("Saving PGN File"),None,0,len(self.offset_headers),mainWindow)
        pDialog.show()
        pDialog.setWindowModality(PyQt4.QtCore.Qt.WindowModal)
        QApplication.processEvents()
        with open(self.filename,'r') as pgn:
            with open(self.filename+"tmp",'w') as new_pgn:
                for idx, (offset,headers) in enumerate(self.offset_headers):
                    QApplication.processEvents()
                    pDialog.setValue(idx)
                    #print("about to load: "+str(offset) + str(headers))
                    # either load from file, or it's the current game
                    if not idx == self.game_open_idx:
                        pgn.seek(offset)
                        game = chess.pgn.read_game(pgn)
                        print(game.root(), file=new_pgn, end="\n\n")
                    else:
                        print(gamestate.current.root(), file=new_pgn, end="\n\n")
                if(self.game_open_idx == len(self.offset_headers)-1):
                    print(gamestate.current.root(), file=new_pgn, end="\n\n")
                pDialog.close()
        shutil.copy(self.filename+"tmp",self.filename)
        self.init_from_file1()
        self.game_open_idx = len(self.offset_headers)-1

    def init_from_file1(self):
        with open(self.filename) as pgn:
            size = os.path.getsize(self.filename)
            self.offset_headers = []
            QApplication.processEvents()
            for offset, headers in chess.pgn.scan_headers(pgn):
                QApplication.processEvents()
                self.offset_headers.append((offset,headers))
        self.checksum = crc32_from_file(self.filename)

    def init_from_file(self, mainWindow):
        with open(self.filename) as pgn:
            size = os.path.getsize(self.filename)
            self.offset_headers = []
            pDialog = QProgressDialog(mainWindow.trUtf8("Scanning PGN File"),None,0,size,mainWindow)
            pDialog.show()
            pDialog.setWindowModality(PyQt4.QtCore.Qt.WindowModal)
            QApplication.processEvents()
            for offset, headers in chess.pgn.scan_headers(pgn):
                QApplication.processEvents()
                pDialog.setValue(offset)
                self.offset_headers.append((offset,headers))
            pDialog.close()
        self.checksum = crc32_from_file(self.filename)

    def init_from_cache(self):
        filename = self.filename[:-4] + ".idx"
        with open(filename,"rb") as f:
            self.checksum, self.offset_headers = pickle.load(f)

    def no_of_games(self):
        return len(self.offset_headers)

    def load_game(self, index):
        if not self.is_consistent():
            raise IOError("database file has changed on disk - index is inconsistent")
        if not index == self.game_open_idx:
            if index >= 0 and index < len(self.offset_headers):
                with open(self.filename) as pgn:
                    offset, headers = self.offset_headers[index]
                    pgn.seek(offset)
                    game = chess.pgn.read_game(pgn)
                    print(str(game))
                    self.game_open = True
                    self.game_open_idx = index
                return game
            else:
                raise ValueError("no game for supplied index in database")

    def is_consistent(self):
        checksum = crc32_from_file(self.filename)
        if not checksum == self.checksum:
            return False
        else:
            return True

