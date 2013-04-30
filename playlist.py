#lil b'dia player version 0.1


import wx
import wx.media
import lastfmparser.parser
import glob
import id3reader
import sqlite3
import songpointers
import threading
import time

ID_START = 1
ID_OPEN = 2
ID_PLAY = 3
ID_CLEAR = 4
ID_DYNAMIC = 5

class ListBox(wx.Frame):
    def __init__(self, parent, id, title):
        #lfm = lastfmparser.parser.parser()
        wx.Frame.__init__(self, parent, id, title, size=(350,250))

        panel = wx.Panel(self, -1)
        hbox = wx.BoxSizer(wx.HORIZONTAL)

        lbox = wx.BoxSizer(wx.VERTICAL)
        hbox.Add(lbox, 1, wx.EXPAND | wx.ALL, 10)

        self.playinglabel = wx.StaticText(panel, -1, "Not Playing")
        lbox.Add(self.playinglabel, 0, wx.TOP, 0)
        self.listbox = wx.ListBox(panel, -1)
        lbox.Add(self.listbox, 1, wx.EXPAND | wx.ALL, 5)


        btnPanel = wx.Panel(panel, -1)
        vbox = wx.BoxSizer(wx.VERTICAL)
        new = wx.Button(btnPanel, ID_START, "Start...", size=(100, 30))
        openf = wx.Button(btnPanel, ID_OPEN, "Open...", size=(100, 30))
        play = wx.Button(btnPanel, ID_PLAY, "Play/Pause", size=(100, 30))
        listlocal = wx.Button(btnPanel, ID_CLEAR, "List Local", size=(100, 30))
        self.dynamicpl = wx.CheckBox(btnPanel, ID_DYNAMIC, "Dynamic Playlist", size=(100, 30))
         

        self.Bind(wx.EVT_BUTTON, self.Start, id=ID_START)
        self.Bind(wx.EVT_BUTTON, self.OnOpen, id =ID_OPEN)
        self.Bind(wx.EVT_BUTTON, self.OnPlay, id =ID_PLAY)
        self.Bind(wx.EVT_BUTTON, self.ListLocal, id =ID_CLEAR)
        self.Bind(wx.EVT_LISTBOX_DCLICK, self.ListDoubleClick)

        vbox.Add((-1, 25))
        vbox.Add(new)
        vbox.Add(openf, 0, wx.TOP, 5)
        vbox.Add(play, 0, wx.TOP, 5)
        vbox.Add(listlocal, 0, wx.TOP, 5)
        vbox.Add(self.dynamicpl, 0, wx.TOP, 5)

        btnPanel.SetSizer(vbox)
        hbox.Add(btnPanel, 0.6, wx.EXPAND | wx.RIGHT, 20)
        panel.SetSizer(hbox)

        self.Centre()
        self.Show(True)

        self.playing = False
        self.mp3loaded = False
        self.mediaplayer = wx.media.MediaCtrl(self, szBackend=wx.media.MEDIABACKEND_WMP10)
        self.lfm = lastfmparser.parser.parser("lastfmparser/")
        self.sp = songpointers.SongPointers()

        self.currenttrack = 0;


    def OnOpen(self, event):
        openDialog = wx.DirDialog(
            self, message="choose file",
            style=wx.OPEN | wx.CHANGE_DIR)
        if openDialog.ShowModal() == wx.ID_OK:
            path = openDialog.GetPath()
            files = self.GetGlob(path)
            for f in files:
                self.AddFilePointer(f)
                self.listbox.Append(self.GetId3(f))
        openDialog.Destroy()

    def OnPlay(self, event):
        self.mediaplayer.Stop()
        sel = self.currenttrack
        if sel < 0:
            sel = 0
        path = ""
        while sel < len(self.listbox.GetStrings()):
            song = self.listbox.GetString(sel).split(",")            
            self.playinglabel.SetLabel(("Now Playing: " + self.listbox.GetString(sel)))
            artist = song[0]
            track = song[1].strip()
            path = self.sp.getfile(artist, track)
            if len(path) > 1:
                break
            else:
                print artist, track, "not in library"
            sel = sel + 1
        if self.playing:
            self.PauseFile()
        else:
            if self.mp3loaded:
                self.mediaplayer.Play()
                self.playing = True
            else:
                print "attempting play file"
                self.PlayFile(path)

    def PlayFile(self, path):
        self.mediaplayer.Stop()        
        self.mediaplayer.Load(path)
        #else:
        self.mediaplayer.Bind(wx.media.EVT_MEDIA_LOADED, self.SongLoaded)
        self.mediaplayer.Bind(wx.media.EVT_MEDIA_FINISHED, self.PlayNext)

    def SongLoaded(self, event):
        print "sl", self.mediaplayer.GetState()
        while self.mediaplayer.GetState() == 0:
            print "in loop"
            self.mediaplayer.Play()
            self.mp3loaded = True
            self.playing = True
            #self.mediaplayer.Bind(wx.media.EVT_MEDIA_STOP, self.PlayNext)


    def PauseFile(self):
        self.mediaplayer.Pause()
        self.playing = False


    def PlayNext(self, event):
        #if self.mediaplayer.GetState() == 0:
        self.playing = False
        self.mp3loaded = False
        song = self.listbox.GetString(0).split(",")
        artist = song[0]
        track = song[1].strip()
        path = self.sp.getfile(artist, track)
        self.OnPlay(event)
        self.listbox.Delete(0)
        if self.dynamicpl.GetValue():
            self.currenttrack = 0
            self.FindSimilar(event)
        else:
            self.currenttrack = self.currenttrack + 1


    def AddFilePointer(self, path):
        sp = songpointers.SongPointers()
        deets = id3reader.Reader(path)
        artist = deets.getValue("performer")
        track = deets.getValue("title")
        sp.addfile(artist, track, path)

    def GetGlob(self, path):
        files = glob.glob(path+"/*.mp3")
        return files

    def GetId3(self, path):
        deets = id3reader.Reader(path)
        artist = deets.getValue("performer")
        track = deets.getValue("title")
        s = artist+", "+track
        return s

    def Start(self, event):
        text = wx.GetTextFromUser("Enter [artist, track]", "Choose a song to start...", "Lil B, I Own Swag")
        if text != "":
            self.listbox.Clear()
            song = text.split(",")
            playlist = self.lfm.dynamicplaylist(song[0], song[1].strip())
            self.listbox.Append(text)
            for item in playlist:
                #ntext = str(item[0]) #str((str(item[0]), item[1]))
                ntext = item[1]+ ", "+item[2]
                self.listbox.Append(ntext)

    def ListDoubleClick(self, event):
        self.mediaplayer.Stop()
        self.playing = False
        self.mp3loaded = False
        self.currenttrack = self.listbox.GetSelection()
        self.OnPlay(event)
        if self.dynamicpl.GetValue():
            self.FindSimilar(event)
            
            
    def FindSimilar(self, event):
        #self.PauseFile()
        sel = self.listbox.GetSelection()
        if sel < 0:
            sel = 0
        text = self.listbox.GetString(sel).split(",")
        self.listbox.Clear()
        playlist = self.lfm.dynamicplaylist(text[0], text[1].strip())
        for item in playlist:
            ntext = item[1]+ ", "+item[2] #str((str(item[0]), item[1]))
            self.listbox.Append(ntext)


    def ListLocal(self, event):
        allstuff = self.sp.getdb()
        for item in allstuff:
            entry = item[0] + ", " + item[1]
            self.listbox.Append(entry)

app = wx.App()
ListBox(None, -1, "Lil B'dia Player")
app.MainLoop()
