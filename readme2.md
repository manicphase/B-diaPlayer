Lil B'dia player version 0.01

Super basic media player I made to try find the gems from Lil B's 1800+ song discography, Though it should work with any artists.

Works by parsing the last.fm histories of fans of the song you're currently listening to, in order to try and pick which songs would best follow it. Then searches through locally indexed files to find the most appropriate song. It kinda works, but performs best on artists that aren't Lil B.

Required stuff:

python 2.7
wxPython

Uses:
id3reader.py from https://github.com/voidfiles/id3reader

To run:
Run playlist.py
Click "Open..." to add folders. These will be remembered across sessions.
To try out dynamic playlists add more files by the same artist and it'll start to cleverly play the songs in a nice order.