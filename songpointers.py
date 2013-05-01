import sqlite3
import os.path

class SongPointers:
    def __init__(self):
        if not os.path.exists("songpointers.db"):
            self.sqlcreatedb()

    def sqlcreatedb(self):
        connection = sqlite3.connect("songpointers.db")
        cursor = connection.cursor()
        cursor.execute("CREATE TABLE songs (artist TEXT, track TEXT, location TEXT)")
        connection.commit()
        connection.close()

    def addfile(self, artist, track, location):
        artist = artist.replace("'","''")
        track = track.replace("'","''")
        location = location.replace("'","''")
        print "adding pointer for:",artist, track
        connection = sqlite3.connect("songpointers.db")
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM songs where location = '%s'" %location)
        if len(cursor.fetchall()) < 1:
            cursor.execute("INSERT INTO songs VALUES('%s', '%s', '%s')" %(artist, track, location))
        connection.commit()
        connection.close()

    def getfile(self, artist, track):
        artist = artist.replace("'","''")
        track = track.replace("'","''")
        connection = sqlite3.connect("songpointers.db")
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM songs where artist = '%s' AND track = '%s'" %(artist, track))
        results = cursor.fetchall()
        if len(results) > 0:
            location = results[0][2]
        else:
            location = ""
        connection.commit()
        connection.close()
        return location

    def getdb(self):
        connection = sqlite3.connect("songpointers.db")
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM songs")
        allstuff = cursor.fetchall()
        return allstuff

if __name__ == "__main__":
    sp = SongPointers()
    print sp.getfile("Lil B", "Motivation")
