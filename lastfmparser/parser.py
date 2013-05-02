import urllib, json
import pprint
import glob
import os.path
import time

import sqlite3


class parser:
    cachedir = ""
    apikey = "a529188a7b57eadc3cc7de40940623e1"

    def __init__(self, cachedir):
        self.cachedir = cachedir
        if not cachedir =="":
            if not os.path.exists(cachedir):
                os.makedirs(cachedir)
            if not os.path.exists(cachedir+"user cache"):
                os.makedirs(cachedir+"user cache")
            if not os.path.exists(cachedir+"song cache"):
                os.makedirs(cachedir+"song cache")
        if not os.path.exists(cachedir+"playcounts.db"):
            self.sqlcreatedb()
        


    #covert doesn't work in python 2.6. doesn't seem to matter anyway
    """def convert(self, input):
        if isinstance(input, dict):
            return {self.convert(key): self.convert(value) for key, value in input.iteritems()}
        elif isinstance(input, list):
            return [self.convert(element) for element in input]
        elif isinstance(input, unicode):
            return input.encode('utf-8')
        else:
            return input"""

    def prettify(string):
        return json.dumps(string,
                    sort_keys=True, indent=4, separators=(',', ': '))

    def getrecent(self,user):
        try:
            cache = open(self.cachedir+"user cache/%s.txt" %user)
            jsonResponse = json.loads(cache.read())
            cache.close()
            _sendtodb = False
        except:
            url = """http://ws.audioscrobbler.com/2.0/?method=user.getrecenttracks&user=%s&limit=50&api_key=%s&format=json""" %(user, self.apikey)
            #print url
            Response = urllib.urlopen(url)
            jsonResponse = json.loads(Response.read())
            #jsonResponse = self.convert(jsonResponse)
            with open(self.cachedir+"user cache/%s.txt" %user,"w") as cache:
                json.dump(jsonResponse, cache)
            _sendtodb = True
        recent = []
        try:
            for item in jsonResponse["recenttracks"]["track"]:
                artist = json.dumps(item["artist"]["#text"],
                             sort_keys=True, indent=4, separators=(',', ': '))
                song = json.dumps(item["name"],
                             sort_keys=True, indent=4, separators=(',', ': '))
                recent.append([artist, song])
        except:
            pass
        if _sendtodb:
            self.sendtodb(recent)
        return recent

    def getsongfans(self, artist, song):
        cartist = self.correctartist(artist).replace('"','')
        try:
            cache = open(self.cachedir+"song cache/%s - %s.txt" %(cartist, song))
            jsonResponse = json.loads(cache.read())
            cache.close()
        except:
            url = "http://ws.audioscrobbler.com/2.0/?method=track.gettopfans&artist=%s&track=%s&api_key=%s&format=json" %(artist, song, self.apikey)
            Response = urllib.urlopen(url)
            jsonResponse = json.loads(Response.read())
            #jsonResponse = self.convert(jsonResponse)
            with open(self.cachedir+"song cache/%s - %s.txt" %(cartist, song),"w") as cache:
                json.dump(jsonResponse, cache)
        fans = []
        #print jsonResponse
        try:
            for item in jsonResponse["topfans"]["user"]:
                name = item["name"]
                fans.append(name)
        except:
            pass
        return fans

    def sqlcreatedb(self):
        connection = sqlite3.connect(self.cachedir+"playcounts.db")
        cursor = connection.cursor()
        #cursor.execute("CREATE TABLE plays (id INTEGER PRIMARY KEY NOT NULL, artistone TEXT, trackone TEXT, artisttwo TEXT, tracktwo TEXT, tcount INTEGER)")
        #cursor.execute("CREATE TABLE alias (id INTEGER PRIMARY KEY NOT NULL, alias TEXT, proper TEXT)")
        cursor.execute("CREATE TABLE songs (id INTEGER PRIMARY KEY NOT NULL, song TEXT, artist TEXT, proper TEXT)")
        connection.commit()
        connection.close()
        

    def sqlincrement(self, entry):
        artist1 = self.correctartist(entry[0]).strip('"')
        track1 = entry[1].strip('"')
        artist2 = self.correctartist(entry[2]).strip('"')
        track2 = entry[3].strip('"')
        connection = sqlite3.connect(self.cachedir+"playcounts.db")
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM plays where artistone='%s' AND trackone='%s' AND artisttwo='%s' AND tracktwo='%s'" %(artist1, track1, artist2, track2))
        rows = cursor.fetchall()
        if len(rows) == 0:
            try:
                cursor.execute("INSERT into plays VALUES(NULL, '%s', '%s', '%s', '%s', 1)" %(artist1, track1, artist2, track2))
                #print "creating row:", artist1, track1, artist2, track2, "1"
            except:
                print "ERROR while creating row:", artist1, track1, artist2, track2, "1"
        else:
        #try:
            index = rows[0][0]
            tcount = rows[0][5] + 1
            print "updating row:", index, artist1, track1, artist2, track2, tcount
            cursor.execute("INSERT or REPLACE into plays VALUES(%s,'%s','%s','%s','%s',%s)" %(index, artist1, track1, artist2, track2, tcount))
            
            #except:
                #print "Error Amending row: "+str(index), artist1, track1, artist2, track2, str(tcount)
        connection.commit()
        connection.close()

    def sqlgetcounts(self, _artist, _song):
        #_artist = self.correctartist(_artist)
        print _artist, _song
        connection = sqlite3.connect(self.cachedir+"playcounts.db")
        cursor = connection.cursor()
        cursor.execute("""SELECT * FROM plays where (artistone='%s' AND trackone='%s') OR (artisttwo='%s' AND tracktwo='%s')
                        ORDER BY tcount DESC""" %(_artist, _song, _artist, _song))
        rows = cursor.fetchall()
        connection.commit()
        connection.close()
        return rows

    def correctartist(self, _artist):
        connection = sqlite3.connect(self.cachedir+"playcounts.db")
        cursor = connection.cursor()
        #cursor.execute("SELECT * FROM alias")
        #print cursor.fetchall()
        if _artist[0] == _artist[-1]:
            _artist = _artist.strip('"')
        _artist = _artist.replace("''",'"')
        s_artist = _artist.replace("'","''")
        cursor.execute("SELECT * FROM alias where (alias = '%s')"%s_artist)
        results = cursor.fetchall()
        if len(results) > 0:
            connection.commit()
            connection.close()
            #print "results:",results
            return results[0][2]
        else:
            #print "adding correction for "+_artist            
            time.sleep(1)
            url = """http://ws.audioscrobbler.com/2.0/?method=artist.getcorrection&artist=%s&api_key=%s&format=json""" %(_artist, self.apikey)
            Response = urllib.urlopen(url)
            jsonResponse = json.loads(Response.read())
            try:
                properartist = jsonResponse["corrections"]["correction"]["artist"]["name"]
            except:
                properartist = _artist
            cursor.execute("INSERT into alias VALUES(NULL, '%s', '%s')" %(s_artist, properartist))
            connection.commit()
            connection.close()
            print "adding correction for "+_artist+ ": "+properartist
            return properartist

    def correcttrack(self, _artist, _song):
        connection = sqlite3.connect(self.cachedir+"playcounts.db")
        cursor = connection.cursor()
        if _song[0] == _song[-1]:
            _song = _song.strip('"')
        _song = _song.replace("''",'"')
        s_song = _song.replace("'","''")
        cursor.execute("SELECT * FROM songs where (song = '%s' AND artist='%s')"%(s_song, _artist))
        results = cursor.fetchall()
        if len(results) > 0:
            connection.commit()
            connection.close()
            return results[0][3]
        else:        
            time.sleep(1)
            url = """http://ws.audioscrobbler.com/2.0/?method=track.getcorrection&artist=%s&track='%s'&api_key=%s&format=json""" %(_artist, _song, self.apikey)
            Response = urllib.urlopen(url)
            jsonResponse = json.loads(Response.read())
            try:
                propertrack = jsonResponse["corrections"]["correction"]["track"]["name"]
            except:
                propertrack = _song
            cursor.execute("INSERT into songs VALUES(NULL, '%s', '%s', '%s')" %(s_song, _artist, propertrack))
            connection.commit()
            connection.close()
            print "adding correction for "+_song+ ": "+propertrack
            return propertrack

    def sendtodb(self, recent):
        print "before", self._artist
        self._artist = self.correctartist(self._artist)
        print "after", self._artist
        listencount = len(recent)
        i = 0
        while i < (listencount-1):
            if recent[i][0].find(self._artist) > -1:
                if recent[i+1][0].find(self._artist) > -1:
                    artist1 = self.correctartist(recent[i][0].replace("'","''"))
                    #track1 = self.correctartist(recent[i][1]).replace("'","''")
                    #artist1 = recent[i][0].replace("'","''")
                    track1 = recent[i][1].replace("'","''")
                    song1 = (artist1 + ", " + track1)

                    artist2 = self.correctartist(recent[i+1][0].replace("'","''"))
                    #track2 = self.correctartist(recent[i+1][1]).replace("'","''")
                    #artist2 = recent[i+1][0].replace("'","''")
                    track2 = recent[i+1][1].replace("'","''")
                    song2 = (artist2 + ", " + track2)

                    a = cmp(song1, song2)
                    if a < 0:
                        #entry = [song1, song2]
                        entry = [artist1, track1, artist2, track2]
                        #self.sqlincrement(entry[0], entry[1])
                        self.sqlincrement(entry)
                    if a > 0:
                        #entry = [song2, song1]
                        entry = [artist2, track2, artist1, track1]
                        #self.sqlincrement(entry[0], entry[1])
                        self.sqlincrement(entry)
            i = i + 1

    def parsecache(self, _artist):
        self._artist = self.correctartist(_artist)
        allusers = glob.glob(self.cachedir+"user cache/*.txt")
        recent = []
        playcounts = {}
        for fn in allusers:
            print "parsing user deets:",fn
            cache = open(fn)
            jsonResponse = json.loads(cache.read())
            cache.close()
            #recent = []
            #playcounts = {}
            try:
                for item in jsonResponse["recenttracks"]["track"]:
                    artist = json.dumps(item["artist"]["#text"],
                                 sort_keys=True, indent=4, separators=(',', ': '))
                    song = json.dumps(item["name"],
                                 sort_keys=True, indent=4, separators=(',', ': '))
                    recent.append([artist, song])
            except:
                pass
        self.sendtodb(recent)

    def dynamicplaylist(self, _artist, _song):
        _artist = self.correctartist(_artist.replace("'","''"))
        _song = _song.replace("'","''")
        self._artist = _artist
        self._song = _song
        fans = self.getsongfans(_artist, _song)
        for fan in fans:
            self.getrecent(fan)
        pl = self.sqlgetcounts(_artist, _song)
        npl = []
        for item in pl:
            #print item[5], item[1],item[2] + " > " + item[3],item[4]
            if item[2].find(_song) < 0:
                npl.append([item[5],item[1],item[2]])
            else:
                npl.append([item[5],item[3],item[4]])
        return npl

if __name__ == "__main__":
    _artist = 'Lil B "The BasedGod"'
    _song = "I Own Swag"
    np = parser("")
    print np.correctartist(_artist)
    np.sqlcreatedb()
    #np.parsecache(_artist)
    newplaylist = np.dynamicplaylist(_artist, _song)
    for item in newplaylist:
        print item[0],item[1]
