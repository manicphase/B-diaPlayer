import lastfmparser.parser
import id3reader
import songpointers

ps = lastfmparser.parser.parser("lastfmparser/")
#ps.cachedir = "lastfmparser/"


playlist = ps.dynamicplaylist("Lil B", "Motivation")
for item in playlist:
    print item[0], item[1]+",", item[2]

deets = id3reader.Reader("02 - I Own Swag.mp3")
print deets.getValue("performer")

sp = songpointers.SongPointers()
print sp.getfile("Lil B", "Motivation")
