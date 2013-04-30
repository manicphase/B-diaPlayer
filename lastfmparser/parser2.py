import urllib, json
import pprint
import glob

import sqlite3


class parser:
    cachedir = ""
    def setcachedir(self, cachedir):
        self.cachedir = cachedir

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
            url = """http://ws.audioscrobbler.com/2.0/?method=user.getrecenttracks&user=%s&limit=50&api_key=a529188a7b57eadc3cc7de40940623e1&format=json""" %user
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
        try:
            cache = open(self.cachedir+"song cache/%s - %s.txt" %(artist, song))
            jsonResponse = json.loads(cache.read())
            cache.close()
        except:
            url = "http://ws.audioscrobbler.com/2.0/?method=track.gettopfans&artist=%s&track=%s&api_key=a529188a7b57eadc3cc7de40940623e1&format=json" %(artist, song)
            Response = urllib.urlopen(url)
            jsonResponse = json.loads(Response.read())
            #jsonResponse = self.convert(jsonResponse)
            with open(self.cachedir+"song cache/%s - %s.txt" %(artist, song),"w") as cache:
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
        cursor.execute("CREATE TABLE testdb (id INTEGER PRIMARY KEY NOT NULL, trackone TEXT, tracktwo TEXT, tcount INTEGER)")
        connection.commit()
        connection.close()
        

    def sqlincrement(self, track1, track2):
        connection = sqlite3.connect(self.cachedir+"playcounts.db")
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM testdb where trackone='%s' AND tracktwo='%s'" %(track1, track2))
        rows = cursor.fetchall()
        if len(rows) == 0:
            cursor.execute("INSERT into testdb VALUES(NULL, '%s', '%s', 1)" %(track1, track2))
            print "creating row:", track1, track2
        else:
            index = rows[0][0]
            tcount = rows[0][3] + 1
            cursor.execute("INSERT or REPLACE into testdb VALUES(%s,'%s','%s',%s)" %(index, track1, track2, tcount))
            print "updating row:", index, track1, track2, tcount
        connection.commit()
        connection.close()

    def sqlgetcounts(self, _artist, _song):
        trackname = _artist + ", " + _song
        print trackname
        connection = sqlite3.connect(self.cachedir+"playcounts.db")
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM testdb where trackone='%s' OR tracktwo='%s' ORDER BY tcount DESC" %(trackname, trackname))
        rows = cursor.fetchall()
        connection.commit()
        connection.close()
        return rows

    def sendtodb(self, recent):
        listencount = len(recent)
        i = 0
        while i < (listencount-1):
            if recent[i][0].find(self._artist) > -1:
                if recent[i+1][0].find(self._artist) > -1:
                    song1 = (recent[i][0] + ", " + recent[i][1]).replace('"',"").replace("'","")
                    song2 = (recent[i+1][0] + ", " + recent[i+1][1]).replace('"',"").replace("'","")
                    a = cmp(song1, song2)
                    if a < 0:
                        entry = [song1, song2]
                        self.sqlincrement(entry[0], entry[1])
                    if a > 0:
                        entry = [song2, song1]
                        self.sqlincrement(entry[0], entry[1])
            i = i + 1

    def parsecache(_artist, _song):
        artist = _artist
        song = _song
        allusers = glob.glob(self.cachedir+"user cache/*.txt")
        recent = []
        playcounts = {}
        for fn in allusers:
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
        sendtodb(recent)

    def dynamicplaylist(self, _artist, _song):
        _artist = _artist.replace('"',"").replace("'","")
        _song = _song.replace('"',"").replace("'","")
        self._artist = _artist
        self._song = _song
        fans = self.getsongfans(_artist, _song)
        for fan in fans:
            self.getrecent(fan)
        pl = self.sqlgetcounts(_artist, _song)
        npl = []
        for item in pl:
            #print item[3], item[1] + " > " + item[2]
            if item[1].find(_song) < 0:
                npl.append([item[3],item[1]])
            else:
                npl.append([item[3],item[2]])
        return npl

if __name__ == "__main__":
    _artist = "Lil B"
    _song = "Obama BasedGod"
    np = parser()
    newplaylist = np.dynamicplaylist(_artist, _song)
    for item in newplaylist:
        print item[0],item[1]
