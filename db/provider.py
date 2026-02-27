import re
import oracledb
import sqlite3
from time import sleep
from datetime import datetime, timedelta
from PySide2.QtCore import Signal, QObject, QThread
from PySide2.QtWidgets import QMessageBox

from ..cf.conf import Config
from ..db.cache import dbcache

#
# Oracle View User:
#   create user oraview identified by "password" account unlock;
#   grant create session to oraview;
#   grant select_catalog_role to oraview;
#

def convertBigInts( rows ):
    for r in rows:
        for i in range( row.count() ):
            if isinstance( r[i], int ) and r[i] > 1e18:
                r[i] = str( r[i] )

#class dataLoader( QObject ):
#
#    def __init__( self, mutex ):
#        super().__init__()
#        self._mutex = mutex
#        self.requestExit = False
#
#    def connect( self, oracle, sqlite=sqlite3.connect(":memory:") ):
#        self._oracle = oracle
#        self._sqlite = sqlite
#        self._oraCursor = self._oracle.cursor()
#        self._sqlCursor = self._sqlite.cursor()
#
#    def close( self ):
#        self._oracle = None
#        self._sqlite = None
#        self._oraCursor = None
#        self._sqlCursor = None
#        self._columns = []
#
#    def run( self ):
#        self.buildSqlite()
#        while self.requestExit == False:
#            if self._oracle and self._sqlite:
#                self.doLoad()
#            sleep( 1 )
#        self.close()
#
#    def columnByName( self, name ):
#        for i,n in enumerate(self._columns):
#            if n == name:
#                return i
#        return None
#
#    def buildSqlite( self ):
#        pass
#
#    def doLoad( self ):
#        pass
#

#class ashLoader( dataLoader ):
#
#    def buildSqlite( self ):
#        self._oraCursor.execute( "SELECT * FROM v$active_session_history WHERE 0=1" ).fetchall()
#        oracleColumns = self._oraCursor.description
#        self._columns = [ c[0] for c in oracleColumns ]
#        oraQueryCols = [ f"rawtohex({c[0]}) {c[0]}" if c[1] == oracledb.DB_TYPE_RAW else c[0] for c in oracleColumns ]
#        sqlDropTable = "DROP TABLE IF EXISTS ash"
#        sqlCreateTable = f'CREATE TABLE ash ( {", ".join(self.columns)}, PRIMARY KEY ("SAMPLE_TIME","SESSION_ID","SESSION_SERIAL#") ) WITHOUT ROWID'
#        self._oraQuery = f"SELECT {', '.join(oraQueryCols)} FROM v$active_session_history WHERE sample_time>:last_sample_time"
#        self._sqlInsert = f"INSERT OR REPLACE INTO ash VALUES( {','.join('?' for i in self.columns)} )"
#        self._sqlCursor.execute( sqlDropTable )
#        self._sqlCursor.execute( sqlCreateTable )
#        self.lastSampleTime = datetimei.now() - timedelta(hours=1)
#
#    def doLoad( self ):
#        while True:
#            rows = self._oraCursor.execute( self._oraQuery, last_sample_time=self.lastSampleTime ).fetchall()
#            for i in range( rows.count() ):
#                rows[i] = tuple( str(v) if isinstance(v,int) and v>1e18 else v for v in rows[i] )
#            try:
#                self._mutex.lock()
#                self._sqliteiCursor().executemany( self.sqlInsert, rows )
#            except e:
#                print( f"!!! Thread {type(self)} Exception: {str(e)}" )
#            finally:
#                self.mutex.unlock()

#class sessionLoader( dataLoader ):
#
#    def buildSqlite( self ):
#        self._oraCursor.execute( "SELECT systimestamp SAMPLE_TIME, s.* FROM v$session s WHERE 0=1" ).fetchall()
#        oracleColumns = self._oraCursor.description
#        self._columns = [ c[0] for c in oracleColumns ]
#        oraQueryCols = [ f"rawtohex({c[0]}) {c[0]}" if c[1] == oracledb.DB_TYPE_RAW else c[0] for c in oracleColumns ]
#        sqlDropTable = "DROP TABLE IF EXISTS ash"
#        sqlCreateTable = f'CREATE TABLE ash ( {", ".join(self.columns)}, PRIMARY KEY ("SAMPLE_TIME","SID","SERIAL#") ) WITHOUT ROWID'
#        self._oraQuery = f"SELECT systimestamp SAMPLE_TIME, {', '.join(oraQueryCols)} FROM v$session WHERE status='ACTIVE'"
#        self._sqlInsert = f"INSERT OR REPLACE INTO ash VALUES( {','.join('?' for i in self.columns)} )"
#        self._sqlCursor.execute( sqlDropTable )
#        self._sqlCursor.execute( sqlCreateTable )
#
#    def doLoad( self ):
#        rows = self._oraCursor.execute( self._oraQuery ).fetchall()
#        convertBigInts( rows )
#        for r in rows:
#            for i in range( row.count() ):
#                if isinstance( r[i], int ) and r[i] > 1e18:
#                    r[i] = str( r[i] )
#        try:
#            self._mutex.lock()
#            self._sqliteiCursor().executemany( self.sqlInsert, rows )
#        except e:
#            print( f"!!! Thread {type(self)} Exception: {str(e)}" )
#        finally:
#            self.mutex.unlock()
#


#class dataProvider( QObject ):
#
#    def __init__( self, mainWindow=None ):
#        super().__init__()
#        self.mainWindow = mainWindow
#        self._oracle = None
#        self.sqliteAsh = sqlite
#        self.sqliteStat = sqlite
#        self.mutexAsh = QMutex()
#        self.mutexStat = QMutex()
#        self.loaders = [ ashLoader(self.mutexAsh), statLoader(self.mutexStat) ]
#
#    def tnsnames( self ):
#        tnsFile = ( oracledb.defaults.config_dir or "." ) + "/tnsnames.ora"
#        tnsList = []
#        self._parent.setStatus( "Loading tnsnames" )
#        file= open( tnsFile, "r" )
#        for line in file.readlines():
#            match = re.match( r"^([^#;\s=]+)=", line )
#            if match:
#                tnsList.append( match.group(1) )
#        return tnsList
#
#    def sqliteOpen( self, name ):
#        self.close()
#        self._parent.setStatus( f"Opening sqlite database '{sqliteFile}'" )
#        sqlite = sqlite3.connect( name )
#        self.sqliteAsh = sqlite
#        self.sqliteStat = sqlite
#        self.cache.connect( None, sqlite )
#        pass
#
#    def oracleConnect( self, config ):
#        self.close()
#        connection = config.get("name","-unknown-")
#        connectParams = dict( Config["Oracle"] ).copy()
#        connectParams.update( config.get("params",{}) )
#        self.mainWindow.setStatus( f"Connecting to Oracle database '{connection}'" )
#        self.loaderAsh.connect( **connectParams )
#        self.loaderStat.connect( **connectParams )
#        self.cache.connect( oracledb.connect( **connectParams ), sqlite3.connect( connection ) )
#        self.mainWindow.setStatus( "Preparing in-memory databases" )
#        self.loaderAsh.buildSqlite()
#        self.loaderStat.buildSqlite()
#        self.cache.buildIfEmpty()
#        self.sqliteAsh = self.loaders[0]._sqlite
#        self.sqliteStat = self.loaders[1]._sqlite
#
#    def close( self ):
#        self.loaderAsh.requestExit = True
#        self.loaderStat.requestExit = True
#        self.cache.close()
#        self.waitForMultipleObjects( [ self.loaderAsh, self.loaderStat, self.cache ] )
#        self.oracleAsh = None
#        self.oracleStat = None
#        self.sqliteAsh = None
#        self.sqliteStat = None
#        self.cache = None
#

class loaderThread( QObject ):

    signalLoadCompleteAsh = Signal( datetime, datetime )

    def __init__( self ):
        #super(loaderThread,self).__init__()
        super().__init__()
        self.close()

    def close( self ):
        self._oracle = None
        self._query = None
        self._sqlite = None
        self._insert = None
        self.lastInserted = 0
        self.lastDeleted = 0

    def setConn( self, oracle, query, colSampleTime, sqlite, insert, delete, minmax ):
        self._oracle = oracle
        self._query = query
        self._colSampleTime = colSampleTime
        self._sqlite = sqlite
        self._insert = insert
        self._delete = delete
        self._minmax = minmax

    def doLoadAsh( self, lastSampleTime ):
        try:
            if self._oracle:
                last_sample_time = self._oracle.var( oracledb.DB_TYPE_TIMESTAMP )
                last_sample_time.setvalue( 0, lastSampleTime )
                self._oracle.execute( self._query, last_sample_time=last_sample_time )
                #
                #statusMsg = "Loading..."
                while True:
                    #owner._parent.setStatus( statusMsg ) # ProcessEvents incapsulated
                    #statusMsg += '.'
                    rows = self._oracle.fetchmany( 1000 )
                    if not rows:
                        break
                    try:
                        for row in rows:
                            nrow = tuple( str(v) if isinstance(v,int) and v>1e18 else v for v in row )
                            self._sqlite.execute( self._insert, nrow )
                    except sqlite3.IntegrityError as e:
                        print( str(e) )
                        if "unique constraint failed" not in str(e).lower():
                            raise
                    self._sqlite.execute( "commit" )
                    lastSampleTime = rows[-1][ self._colSampleTime ]
                self.lastInserted = self._oracle.rowcount
                self._sqlite.execute( self._delete, (lastSampleTime-timedelta(hours=5),) )
                self.lastDeleted = self._sqlite.rowcount
                firstSampleTime, lastSampleTime = self._sqlite.execute( self._minmax ).fetchone()
                #
                self.signalLoadCompleteAsh.emit( firstSampleTime, lastSampleTime )
        except Exception as e:
            #print( str(e) )
            raise


class dataProvider( QObject ):

    signalStartLoadAsh = Signal( datetime )
    signalLoadCompleteAsh = Signal()

    def __init__( self, parent=None, dataReady=None ):
        super().__init__()
        self._parent = parent
        self._oracle = None
        self._sqlite = None
        #self.thread = QThread()
        self.loader = loaderThread()
        #self.loader.moveToThread( self.thread );
        self.signalStartLoadAsh.connect( self.loader.doLoadAsh )
        self.loader.signalLoadCompleteAsh.connect( self.loadCompleteHandlerAsh )
        self.threadIsBusy = False
        #self.thread.start()
        self.close()

    def tnsnames( self ):
        tnsFile = ( oracledb.defaults.config_dir or "." ) + "/tnsnames.ora"
        tnsList = []
        self._parent.setStatus( "Loading tnsnames" )
        file= open( tnsFile, "r" )
        for line in file.readlines():
            match = re.match( r"^([^#;\s=]+)=", line )
            if match:
                tnsList.append( match.group(1) )
        return tnsList

    def oracleConnect( self, config ):
        self.close()
        connection = config.get("name","-unknown-")
        connectParams = dict( Config["Oracle"] ).copy()
        connectParams.update( config.get("params",{}) )
        #
        self._parent.setStatus( f"Connecting to Oracle database '{connection}'" )
        self._oracle = oracledb.connect( **connectParams )
        #
        self._parent.setStatus( "Building Oracle column list and requests" )
        cursor = self._oracle.cursor()
        cursor.execute( 'SELECT * FROM v$active_session_history WHERE 0=1' )
        self._oracleColumns = cursor.description
        self._columns = [ c[0] for c in self._oracleColumns ]
        #
        oracleQueryColumns = []
        sqliteCreateColumns = []
        sqliteQueryColumns = []
        #
        for c in self._oracleColumns:
            column = c[0]
            oracleType = c[1]
            sqliteType = "" #oracle_to_sqlite_types.get( oracleType, "TEXT" )
            #self._sqliteNeedColumns.append( (column,sqliteType) )
            sqliteCreateColumns.append( f'"{column}" {sqliteType}' )
            sqliteQueryColumns.append( f'"{column}"' )
            if oracleType == oracledb.DB_TYPE_RAW:
                oracleQueryColumns.append( f"rawtohex({column}) as {column}" )
            else:
                oracleQueryColumns.append( column )
        _oracleQuery = f"SELECT {', '.join(oracleQueryColumns)} FROM v$active_session_history WHERE sample_time>:last_sample_time ORDER BY sample_time"
        _sqliteCreateTable = f'CREATE TABLE ash ( {", ".join(sqliteCreateColumns)}, PRIMARY KEY (SAMPLE_TIME, SESSION_ID, "SESSION_SERIAL#") ) WITHOUT ROWID'
        self._sqliteQuery = f"SELECT {', '.join(sqliteQueryColumns)} FROM ash WHERE sample_time between :beg and :end"
        _sqliteInsert = f"INSERT OR REPLACE INTO ash VALUES( { ', '.join(['?' for i in sqliteCreateColumns]) } )"
        _sqliteDelete = f"DELETE FROM ash WHERE sample_time<:sample_time"
        _sqliteMinMax = f"SELECT (SELECT min(sample_time) FROM ash), (SELECT max(sample_time) FROM ash)"
        #
        #sqliteFile = Config["Sqlite"]["path"] + "/" + connection + ".sqlite"
        #self.sqliteOpen( sqliteFile )
        self._sqlite = sqlite3.connect( ":memory:" )
        self.sqliteBuild( _sqliteCreateTable)
        self.loader.setConn( self._oracle.cursor(), _oracleQuery, self.columnByName("SAMPLE_TIME"), self._sqlite.cursor(), _sqliteInsert, _sqliteDelete, _sqliteMinMax )


    def sqliteOpen( self, sqliteFile=None ):
        self.close()
        #
        if sqliteFile:
            self._parent.setStatus( f"Opening sqlite database '{sqliteFile}'" )
        #
        self._sqlite = sqlite3.connect( sqliteFile, detect_types=sqlite3.PARSE_DECLTYPES|sqlite3.PARSE_COLNAMES )
        #
        self._parent.setStatus( "Building sqlite column list and requests" )
        cursor = self._sqlite.cursor()
        #
#        cursor.execute( "PRAGMA table_info(ash)" )
#        self._sqliteColumns = [ (c[1],c[2]) for c in cursor.fetchall() ]
#        sqliteQueryColumns = []
#        #
#        for c in self._sqliteColumns:
#            column = f'"{c[0]}"'
#            sqliteQueryColumns.append( column )
#        self._sqliteQuery = f"SELECT {', '.join(sqliteQueryColumns)} FROM ash WHERE sample_time between :beg and :end"
#        #
#        try:
#            cursor.execute( "SELECT ifnull(max(sample_time),datetime('now','-01:00')) from ash" )
#            row = cursor.fetchone()
#            self._sqliteLastSampleTime = datetime.fromisoformat(row[0]) if row else None
#        except sqlite3.OperationalError as e:
#            if "no such table" in str(e).lower():
#                """empty or non-prepared sqlite database, waiting for build"""
#                None
#            else:
#                raise

#    def oracleIsConnected( self ):
#        return self._oracle is not None

#    def sqliteIsConnected( self ):
#        return self._sqlite is not None

#    def sqliteIsEmpty( self ):
#        return ( not self._sqliteColumns )

#    def sqliteNeedsBuild( self ):
#        return ( self._sqliteColumns != self._sqliteNeedColumns )

    def sqliteBuild( self, sqliteCreateTable ):
        self._parent.setStatus( "Building sqlite database" )
        cursor = self._sqlite.cursor()
        cursor.execute( "DROP TABLE IF EXISTS ash" )
        cursor.execute( sqliteCreateTable )
        self.firstSampleTime = self.lastSampleTime = datetime.now() - timedelta(hours=5)

    def columnByName( self, name ):
        return self._columns.index( name )
        #for idx,col in enumerate(self._columns):
        #    if col == name:
        #        return idx
        #return None

    def loadDataAsh( self ):
        self._parent.setStatus( "Loading data..." )
        if self._oracle is not None and self._sqlite is not None:
            if self.threadIsBusy:
                """ wait for thread availability """
                pass
            self.threadIsBusy = True
            #self.loader.setConn( self._oracle.cursor(), self._oracleQuery, self.columnByName("SAMPLE_TIME"), self._sqlite.cursor(), self._sqliteInsert, self._sqliteDelete )
            aHourAgo = datetime.now() - timedelta(hours=5)
            if self.lastSampleTime < aHourAgo:
                self.lastSampleTime = aHourAgo
            self.signalStartLoadAsh.emit( self.lastSampleTime )

    def loadCompleteHandlerAsh( self, firstSampleTime, lastSampleTime ):
        self._parent.setStatus( "Loading complete" )
        self.threadIsBusy = False
        self.firstSampleTime = datetime.fromisoformat( firstSampleTime )
        self.lastSampleTime = datetime.fromisoformat( lastSampleTime )
        self.signalLoadCompleteAsh.emit()

    def rowsModified( self ):
        return ( self.loader.lastInserted, self.loader.lastDeleted )

    def close( self ):
        self.loader.close()
        if self._oracle:
            self._oracle.close()
        self._oracle = None
        self._oracleColumns = []
        #self._oracleQuery = ""
        if self._sqlite:
            self._sqlite.close()
        self._sqlite = None
        self._columns = []
        self._sqliteQuery = ""
        #self._sqliteInsert = ""
        #self._sqliteDelete = ""
        #self._sqliteCreateTable = ""
        self.firstSampleTime = None
        self.lastSampleTime = None
