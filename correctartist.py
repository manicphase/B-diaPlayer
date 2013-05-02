import json
import urllib

apikey = "a529188a7b57eadc3cc7de40940623e1"
_artist = 'Lil B "The BasedGod"'

url = """http://ws.audioscrobbler.com/2.0/?method=artist.getcorrection&artist=%s&api_key=%s&format=json""" %(_artist, apikey)
Response = urllib.urlopen(url)
jsonResponse = json.loads(Response.read())
try:
    _artist = jsonResponse["corrections"]["correction"]["artist"]["name"]
except:
    pass

print _artist
