from ast import literal_eval
from configparser import RawConfigParser


"""Created by (c) Gennady Lapin, 2025-2026"""


configfile = "oraview.ini"

defconfig = {
        "MainWindow": {
            "refreshInterval": "10"
            },
        "Oracle_defaults": {
            "user": "oraview",
            },
        "Oracle_prepopulate": {
            "users": "Y",
            "services": "N",
            "objects": "N",
            "sqls": "N",
            },
        "Sqlite": {
            "path": "./data",
            "prefetch": "3",
            "purge": "5"
            },
        "SavedSessions": {},
        "ColumnSizes": {},
        "WaitColors": {
          "On CPU": "lime"
        , "Scheduler": "palegreen"
        , "System I/O": "cyan"
        , "User I/O": "dodgerblue"
        , "Application": "red"
        , "Concurrency": "brown"
        , "Commit": "yellow"
        , "Administrative": "magenta"
        , "Configuration": "orange"
        , "Network": "yellowgreen"
        , "Cluster": "lightsteelblue"
        , "Queueing": "darkseagreen"
        , "Idle": "lightgrey"
        , "Other": "violet"
        }
    }

Config = RawConfigParser()
Config.optionxform = str

def loadConfig():
    """!!! process absent and upgraded items here !!!"""
    try:
        with open( configfile, 'r') as cf:
            Config.clear()
            Config.read_file( cf )
    except FileNotFoundError:
        Config.read_dict( defconfig )
    #
    for sect in defconfig:
        if not sect in Config:
            Config[ sect ] = defconfig[ sect ]

def saveConfig():
    """!!! check and dont save non-saveable items here !!!"""
    with open( configfile, "w" ) as cf:
        Config.write( cf )

def literalEval( str ):
    return literal_eval( str )

def getConfig( sect, opt, default=None ):
    if opt in Config[sect]:
        return Config[sect][opt]
    if sect in defconfig and opt in defconfig[sect]:
        return defconfig[sect][opt]
    return default


loadConfig()
