import os
import os.path
import shutil
import json
import time
import pystray
import sqlite3 as sql

from tkinter import *
from tkinter import filedialog
from tkinter import ttk

from functools import partial
from posixpath import splitext
from watchdog.observers import Observer
from watchdog.events import PatternMatchingEventHandler
from PIL import Image

#create a database and a cursor
if not os.path.exists("./Transfer Log.db"):
    conn = sql.connect("Transfer Log.db", check_same_thread=False)
    cursor = conn.cursor()
    cursor.execute("""CREATE TABLE transfer_log(
        File_name VARCHAR(255),
        From_Dir VARCHAR(255),
        To_Dir VARCHAR(255))
        """)
else:
    conn = sql.connect("Transfer Log.db", check_same_thread=False)
    cursor = conn.cursor()
    
#function to show all data in the database
def Show_all():
    cursor.execute("SELECT * FROM transfer_log")
    records = ''
    for row in cursor.fetchall():
        records += str(row[0]) +"   |   "+str(row[1])+"   |   "+str(row[2])+ "\n"
    return records

#variable to close the observer when set to false 
isOpend = True

title = "Downloads manager"

#Extensions dict
Extensions = {
        "ImgExt" : [".jpg", ".jpeg", ".png", ".tif", ".tiff", ".gif", ".eps", ".raw", ".cr2", ".nef", ".orf", ".sr2", ".ico", ".bmp", ".cur"],
        "VidExt" : [".webm", ".mkv", ".flv", ".vob", ".org", ".ogg", ".drc", ".mng", ".avi", ".mov", ".qt", ".wmv", ".yuv", ".rm", ".rmvb", ".viv", ".asf", ".amv", ".mp4", ".mpg", ".mp2", ".mpeg", ".mpe", ".mpv", ".mpg", ".mpeg", ".m2v", ".m4v",	".svi", ".3gp", ".3g2", ".mxf", ".roq", ".nsv", ".flv", ".f4v", ".f4p", ".f4a", ".f4b"],
        "AudExt" : [".m4p", ".m4v", ".3gp", ".aa", ".aac", ".aax", ".act", ".aiff", ".alac", ".amr", ".ape", ".au", ".awb", ".dss", ".dvf", ".flac", ".gsm", ".iklax", ".ivs", ".m4a", ".m4b", ".mmf", ".mp3", "mpc", ".msv", "nmf", "ogg", ".oga", ".mogg", ".opus", ".ra", ".rm", ".raw", ".rf64", ".sln", ".tta", ".voc", ".vox", ".wav", ".wma", ".wv", ".webm", ".8svx", ".cda"],
        "DocExt" : [".doc", ".docx", ".html", ".htm", ".odt", ".pdf", ".xls", ".xlsx", ".ods", ".ppt", ".pptx", ".txt"],
        "ExeExt" : [".exe", ".bat", ".com", ".cmd", ".inf", ".ipa", ".osx", ".pif", ".run", ".wsh"]
}

#create the event handler
my_event_handler = PatternMatchingEventHandler(["*"], None, False, True)

#Default Folders
DefaultFolders = {
    "Source" : os.path.expanduser('~/Downloads/'),
    "ImgDir" : "./Images/",
    "VidDir" : "./Videos/",
    "AudDir" : "./Audio/",
    "DocDir": "./Documents/",
    "ExeDir" : "./Executable/",
    "OthDir" : "./Others/"   
}

#create the tkinter window
main = Tk()
main.title(title)
main.iconbitmap("./icon.ico")
main.geometry("255x335")

#Create a nootebook widget
notebook = ttk.Notebook(main)
notebook.pack()

#Creating frames for tab 1 and 2
MainFrame = Frame(notebook, width=300, height=320)
LogFrame = Frame(notebook, width=300, height=320)

MainFrame.pack()
LogFrame.pack()

#Creating Tabs
notebook.add(MainFrame, text="Main")
notebook.add(LogFrame, text="Log")

#transfare log label
Transfer_log_label = Label(LogFrame, text=Show_all())
Transfer_log_label.pack()

#update the transfare logLabel text
def Update_log_tab():
    Transfer_log_label.configure(text=Show_all())
Update_log_tab()

#Delaring the tray status variable to use with the checkbox
TrayStatus = IntVar()

#import or create settings.json
if os.path.exists("./Settings.json"):
    with open("./Settings.json") as file:
        Settings = json.load(file)
        Folders = Settings[0]
        for i in range(len(Folders.values())):
            folder = Folders[list(Folders)[i]]
            #if path dosen't exist change it to the default one
            if os.path.exists(folder) == False:
                if os.path.exists(DefaultFolders[list(Folders)[i]]):
                    pass
                else: os.mkdir(DefaultFolders[list(Folders)[i]])
                Folders[list(Folders)[i]] = DefaultFolders[list(Folders)[i]]
        TrayIconStatus = Settings[1]
        TrayStatus.set(Settings[1]["TrayIconStatus"])
else:
    Folders = DefaultFolders
    TrayIconStatus = {"TrayIconStatus" : 1}

    Settings = [Folders, TrayIconStatus]
    with open("./Settings.json", "w") as file:
        json.dump(Settings, file, indent=4)

#a function i call every time i change something in folders or trayiconstatus so the settings variable get updated
def UpdateSettings():
    globals()["Settings"] = [Folders, TrayIconStatus]

#lists
FoldersList = list(Folders)
ChoseLabels = []
PathLabels = []

#Creating the observer
my_observer = Observer()
my_observer.schedule(my_event_handler, Folders["Source"], recursive=False)
my_observer.start()

#create dir label and name label
for i in range(len(FoldersList)):
    ChoseLabels.append(Label(MainFrame, text = FoldersList[i]))
    ChoseLabels[i].grid(row=i, column=0)
    PathLabels.append(Label(MainFrame, text=Folders[FoldersList[i]], bd=1, relief="solid", justify="left"))
    PathLabels[i].grid(row=i, column=1, pady= 5)

#select button function
def SelectDir(i):
    label = PathLabels[i]
    FolderType = globals()["FoldersList"][i]
    #--------------------------------------------------------------------
    main.path = filedialog.askdirectory(initialdir="%USERPROFILE%\Downloads", title="Select a folder")
    global Folders
    Folders[FolderType] = main.path
    UpdateSettings()
    label.config(text=Folders[FolderType])
    with open("./Settings.json", "w") as file:
        json.dump(Settings, file, indent=4)

#create select buttons
for i in range(len(PathLabels)):
    buttoni = Button(MainFrame, text="select", command=partial(SelectDir,i))
    buttoni.grid(row=i, column=2, pady=5, padx=5)

#sort system function
def Sort():
    #list of extensions's dict keys
    ExtensionsKeys = list(Extensions)
    
    for file in os.listdir(Folders["Source"]):
        #variable to know if the file is known or not
        ExtFound = False
        
        Src = Folders["Source"] + file
        #spltin the file's name and extension
        file_name, Ext = splitext(file)[0], splitext(file)[1].lower()
        
        #check if file is known
        for i in range(len(ExtensionsKeys)):
            if Ext in Extensions[ExtensionsKeys[i]]:
                toDir = Folders[str(ExtensionsKeys[i][0:3]) + "Dir"]
                #if file exists in toDir
                if os.path.isfile(f"{toDir}{file}"):
                    counter = 0
                    while True:
                        counter += 1
                        New_File = file_name + f"({counter})" + Ext
                        New_Src = Folders["Source"] + New_File
                        if os.path.isfile(f"{toDir}{New_File}"):
                            print(New_File, New_Src)
                            continue
                        else:
                            os.rename(Src, New_Src)
                            Src = New_Src
                            file = New_File
                            print(Src)
                            print(New_Src)
                            print("Renamed")
                            break
                print("moving file")
                shutil.move(Src, toDir)
                print("file moved")
                ExtFound = True
                cursor.execute(f"INSERT INTO transfer_log VALUES(?,?,?)", (file, Src, toDir))
                conn.commit()
                Update_log_tab()
                break
        if ExtFound:continue
        if Ext != ".tmp":
            shutil.move(Src, Folders["OthDir"])
            cursor.execute(f"INSERT INTO transfer_log VALUES(?,?,?)", (file, Src, Folders["OthDir"]))
            conn.commit()
            Update_log_tab()

#sort button
SortButton = Button(MainFrame, text="Sort", command=Sort, padx=10, pady=5)
SortButton.grid(row=7, column=0, columnspan=3)

#listen for changes in source dir using watchdog library
def on_created(self):
    Sort()

#declaring event handlers's functions
my_event_handler.on_created = on_created
my_event_handler.on_modified = on_created
#my_event_handler.on_any_event = on_created

#create Tray Icon
def CreateTray():
        icon = Image.open("./icon.ico")
        global Tray
        Tray = pystray.Icon("name", icon, title="title", menu=pystray.Menu(
            pystray.MenuItem("Exit", Exit),
            pystray.MenuItem("Open"+title, Show))
            )
        globals()["TrayIsEnabled"] = True

#show tkinter window
def Show():
    Tray.stop()
    CreateTray()
    main.deiconify()

#exit app through the tray icon
def Exit():
        conn.close()
        main.destroy()
        Tray.stop()
        globals()["isOpend"] = False

#when i press the X (close) button
def CloseWin():
    if TrayIconStatus["TrayIconStatus"] == 1:
        main.withdraw()
        Tray.run()
    else:
        conn.close()
        main.destroy()
        globals()["isOpend"] = False

#CheckBox for tray icon
TrayCheckBox = Checkbutton(MainFrame, text="run in the background", variable=TrayStatus, command=lambda:UpdateTrayIconStatus(TrayStatus))#define a command
TrayCheckBox.grid(row=8, column=0, columnspan=2)

#create tray icon function
def UpdateTrayIconStatus(TrayStatus):
    TrayStatus = TrayStatus.get()
    TrayIconStatus["TrayIconStatus"] = TrayStatus
    UpdateSettings()
    with open("./Settings.json", "w") as file:
        json.dump(Settings, file, indent=4)

    if TrayStatus == 1:
        TrayCheckBox.select()
        CreateTray()
    else:
        TrayCheckBox.deselect()

main.protocol("WM_DELETE_WINDOW", partial(CloseWin))

UpdateTrayIconStatus(TrayStatus)

main.mainloop()

try:
    while True:
        if isOpend == False:
            raise KeyboardInterrupt
        time.sleep(1)

except KeyboardInterrupt:
    my_observer.stop()
my_observer.join()