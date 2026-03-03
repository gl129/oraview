import oracledb
from PySide2.QtCore import Qt, QSize
from PySide2.QtWidgets import QWidget, QHBoxLayout, QFormLayout, QSizePolicy, QGroupBox, QLabel, QPushButton, QMessageBox, QApplication, QLineEdit, QComboBox, QSpacerItem

from ..cf.conf import Config
from ..ui.win import childWin
from ..db.cache import cache_tables


"""Created by (c) Gennady Lapin, 2025-2026"""


def titleString( string ):
    return string.replace( '_', ' ' ).title()


class readonlyEdit( QLineEdit ):
    def __init__( self, dictInfo, name ):
        super().__init__( )
        self.setReadOnly( True )
        dictInfo[name] = self


class connectDialog( childWin ):

    def __init__( self, mainWindow, config ):
        super().__init__( mainWindow, "Connection Dialog" )
        self.config = config

        if True:
            grParams = QGroupBox( "Connection Params" )
            lyParams = QFormLayout()

            #self.labelNotAllowed = QLabel( "<font color='red'><b>Can't modify tnsnames.ora connection parameters</b></font>" )
            #lyParams.addWidget( self.labelNotAllowed )

            self.editConnName = QLineEdit()
            lyParams.addRow( '<b>Name</b>', self.editConnName )
            self.addConnectWidgets( lyParams )
            grParams.setLayout( lyParams )
            self.layout().addWidget( grParams )

            lyTestConnect = QHBoxLayout()

            btnDisconnect = QPushButton( "Disconnect current" )
            btnDisconnect.clicked.connect( self.clickedDisconnect )
            lyTestConnect.addWidget( btnDisconnect )

            lyTestConnect.addItem( QSpacerItem( 1, 1, QSizePolicy.Expanding, QSizePolicy.Preferred ) )

            btnTest = QPushButton( "Test connection" )
            btnTest.clicked.connect( self.clickedTest )
            lyTestConnect.addWidget( btnTest )

            self.btnSave = QPushButton( "Save" )
            self.btnSave.clicked.connect( self.clickedSave )
            lyTestConnect.addWidget( self.btnSave )

            btnConnect = QPushButton( "Connect" )
            btnConnect.clicked.connect( self.clickedConnect )
            lyTestConnect.addWidget( btnConnect )

            self.layout().addLayout( lyTestConnect )

        if True:
            grInfo = QGroupBox( "Current Connection Info" )
            lyInfo = QHBoxLayout( )

            self.info = {}
            infoEdits = [ "database", "unique_name", "inst_name", 
                          "platform", "host_name", "version",
                          "role", "open_mode", "log_mode",
                          "sessions", "processes", "",
                          "created", "resetlogs", "startup" ]
            infoLayouts = [ QFormLayout() for i in range(3) ]

            for i,t in enumerate( infoEdits ):
                infoLayouts[ i % 3 ].addRow( t.replace( '_', ' ').title(), readonlyEdit( self.info, t ))

            for i in range(3):
                lyInfo.addLayout( infoLayouts[i] )

            grInfo.setLayout( lyInfo )
            self.layout().addWidget( grInfo )

        if True:
            grCache = QGroupBox( "Populate cache tables" )
            lyCache = QHBoxLayout()

            lyCache.addItem( QSpacerItem( 1, 1, QSizePolicy.Expanding, QSizePolicy.Preferred ) )
            for name in cache_tables.keys():
                button = QPushButton( name )
                button.clicked.connect( lambda checked=False, table=cache_tables[name]: self.populateCache(table) )
                lyCache.addWidget( button )

            grCache.setLayout( lyCache )
            self.layout().addWidget( grCache )

        self.refreshCurrentParams()
        self.fillConnectionInfo()
        

    def fillConnectionInfo( self ):
        if self.isConfigCurrent():
            with self.mainWindow.data._oracle.cursor() as cursor:
                version = cursor.execute( "select version from v$instance" ).fetchone()[0]
                if version[1] != "." and int(version[0:2]) >= 18:
                    version = cursor.execute( "select version_full from v$instance" ).fetchone()[0]
                database = cursor.execute( "select name, db_unique_name, database_role, platform_name, open_mode, log_mode, created, resetlogs_time from v$database" ).fetchone()
                instance = cursor.execute( "select instance_number, instance_name, host_name, startup_time from v$instance" ).fetchone()
                sessions = cursor.execute( "select count(*) from v$session" ).fetchone()[0]
                processes = cursor.execute( "select count(*) from v$process" ).fetchone()[0]
                pnames = [ "sessions", "processes", "cursors" ]
                params = { v[0]: v[1] for v in cursor.execute( f"""select name, value from v$parameter where name in ('{"','".join(pnames)}')""" ).fetchall() }
        else:
            version = ""
            database = [ "" for i in range(8) ]
            instance = [ "" for i in range(4) ]
            sessions = ""
            processes = ""
            params = {}

        self.info["database"].setText( database[0] )
        self.info["unique_name"].setText( database[1] )
        self.info["inst_name"].setText( instance[1] )
        self.info["platform"].setText( database[3] )
        self.info["host_name"].setText( instance[2] )
        self.info["version"].setText( version )
        self.info["role"].setText( database[2] )
        self.info["open_mode"].setText( database[4] )
        self.info["log_mode"].setText( database[5] )
        self.info["sessions"].setText( f"{sessions}/{params.get('sessions','')}" )
        self.info["processes"].setText( f"{processes}/{params.get('processes','')}" )
        self.info[""].setText( "" )
        self.info["created"].setText( str(database[6]) )
        self.info["resetlogs"].setText( str(database[7]) )
        self.info["startup"].setText( str(instance[3]) )


    def isConfigCurrent( self ):
        return ( self.mainWindow.data._oracle is not None and self.mainWindow.currentConfig == self.config )


    def addConnectWidgets( self, layout ):
        def addParamWidget( layout, param ):
            label = param.replace( "_", " " ).title()
            if param == "mode":
                widget = QComboBox()
                widget.addItem( "Normal", "" )
                widget.addItem( "as SYSDBA", "2" )
                widget.addItem( "as SYSOPER", "4" )
                #widget.setCurrentText( text )
            else:
                widget = QLineEdit( ) #text )
                if param.find("password") >= 0:
                    widget.setEchoMode( QLineEdit.Password )
            widget.setProperty( "o$param", param )
            self.oracleParamsWidgets.append( widget )
            layout.addRow( label, widget )
        #
        self.oracleParamsWidgets = []
        oracleParamsList = [ "dsn",
                             [ "user", "password", "mode" ],
                             [ "protocol", "host", "port", "sdu" ],
                             [ "service_name", "instance_name", "sid", "server_type" ] ]
#                             [ "program", "machine", "terminal", "osuser" ]
        for param in oracleParamsList:
            if isinstance(param,list):
                wH = QWidget()
                lyH = QHBoxLayout(wH)
                for subParam in param:
                    subLayout = QFormLayout()
                    addParamWidget( subLayout, subParam )
                    lyH.addLayout( subLayout )
                layout.addRow( "", wH )
            else:
                addParamWidget( layout, param )


    def getConnectParams( self ):
        connectParams = {}
        for widget in self.oracleParamsWidgets:
            if isinstance( widget, QComboBox ):
                value = widget.currentData()
            else:
                value = widget.text()
            if len(value) > 0 :
                param = widget.property( "o$param" )
                connectParams[param] = value
        return connectParams.copy()


    def clickedDisconnect( self ):
        try:
            self.mainWindow.disconnectAll()
        finally:
            self.fillConnectionInfo()


    def clickedTest( self ):
        connectParams = dict( Config["Oracle_defaults"] ).copy()
        connectParams.update( self.getConnectParams() )
        try:
            oracle = oracledb.connect( **connectParams )
            cursor = oracle.cursor()
            cursor.execute( "SELECT * FROM v$active_session_history" )
            rows = cursor.fetchone()
            QMessageBox.information( self, "Test Connection", "Test connection successful!", QMessageBox.Ok )
        except Exception as e:
            QMessageBox.critical( self, "Test Connection", f"Test connection failed:\n{str(e)}" )


    def clickedSave( self ):
        name = self.editConnName.text()
        if name is None or len( name ) == 0:
            QMessageBox.critical( self, "Saving connection", "You should specify connection name", QMessageBox.Ok )
            return
        if name != self.config["name"] and name in Config["SavedSessions"]:
            """name changed and such name exists"""
            if QMessageBox.question( self, "Connection Saving",
                    f"Connection with name '{name}' already exists.\nDo you want to overwrite it?",
                    QMessageBox.Yes|QMessageBox.Cancel ) != QMessageBox.Yes:
                return
        params = self.getConnectParams()
        self.config = dict( src="saved", name=name, params=params )
        Config["SavedSessions"][name] = str( params )
        self.mainWindow.treeConnections.refreshSaved()
        self.fillConnectionInfo()


    def clickedConnect( self ):
        params = self.getConnectParams()
        if params != self.config.get("params",""):
            name = self.editConnName.text() or 'noname'
            self.config = dict( src="edit", name=name, params=params )
            self.mainWindow.treeConnections.addRecent( self.config )
        try:
            self.mainWindow.connectTo( self.config )
        finally:
            self.fillConnectionInfo()


    def refreshCurrentParams( self ):
        if isinstance( self.config, dict ):
            src = self.config.get( "src", "none" )
            name = self.config.get( "name", "" )
            connectParams = self.config.get( "params", {} )
            if not isinstance( connectParams, dict ):
                connectPrams = {}
        else:
            src = "none"
            name = ""
            connectParams = {}
        #
        self.editConnName.setText( name )
        for widget in self.oracleParamsWidgets:
            param = widget.property( "o$param" )
            text = connectParams.get( param, "" )
            if param == "mode":
                widget.setCurrentIndex( int(text or "0") / 2 )  # 0: Normal, 2: as SYSDBA, 4: as SYSOPER
            else:
                widget.setText( text )


    def populateCache( self, table ):
        if self.isConfigCurrent():
            QApplication.setOverrideCursor( Qt.WaitCursor )
#            try:
            try:
                self.mainWindow.cache.populate( table )
            finally:
                QApplication.restoreOverrideCursor()
#            except:
#                raise
            QMessageBox.information( self, "Cache population", f"Cache population for table {table} complete!", QMessageBox.Ok )
        else:
            raise Exception( "Connection is not current!" )
