import oracledb
from PySide2.QtCore import Qt, QSize
from PySide2.QtWidgets import QWidget, QHBoxLayout, QFormLayout, QSizePolicy, QGroupBox, QLabel, QPushButton, QMessageBox, QApplication, QLineEdit, QComboBox, QSpacerItem
from ..cf.conf import Config
from ..ui.win import childWin
from ..db.cache import cache_tables


oracleParamsList = [
        "dsn",
        [ "user", "password", "mode" ],
        [ "protocol", "host", "port", "sdu" ],
        [ "service_name", "instance_name", "sid", "server_type" ]
#        [ "program", "machine", "terminal", "osuser" ]
        ]


class readonlyEdit( QLineEdit ):
    def __init__( self, text ):
        super().__init__( text )
        self.setReadOnly( True )


class connectDialog( childWin ):

    def __init__( self, mainWindow, config ):
        super().__init__( mainWindow, "Connection Dialog" )
        self.config = config

        grParams = QGroupBox( "Connection Params" )
        lyParams = QFormLayout()

        self.labelNotAllowed = QLabel( "<font color='red'><b>Can't modify tnsnames.ora connection parameters</b></font>" )
        lyParams.addWidget( self.labelNotAllowed )

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

        # Current Connection Info

        isDbOpen = ( mainWindow.data._oracle is not None )
        if isDbOpen:
            with mainWindow.data._oracle.cursor() as cursor:
                database = cursor.execute( "select name, db_unique_name, database_role, platform_name, open_mode, log_mode, created, resetlogs_time from v$database" ).fetchone()
                instance = cursor.execute( "select instance_number, instance_name, host_name, version_full, database_type, startup_time from v$instance" ).fetchone()
                sessions = cursor.execute( "select count(*) from v$session" ).fetchone()[0]
                processes = cursor.execute( "select count(*) from v$process" ).fetchone()[0]
                pnames = [ "sessions", "processes", "cursors" ]
                params = { v[0]: v[1] for v in cursor.execute( f"""select name, value from v$parameter where name in ('{"','".join(pnames)}')""" ).fetchall() }
        else:
            database = [ '' for i in range(8) ]
            instance = [ '' for i in range(6) ]
            sessions = ''
            processes = ''
            params = {}

        grInfo = QGroupBox( "Database Info" )
        #grInfo.setSizePolicy( QSizePolicy.Expanding, QSizePolicy.Expanding )
        lyInfo = QHBoxLayout( )

        lyLeftInfo = QFormLayout()
        lyMidInfo = QFormLayout()
        lyRightInfo = QFormLayout()

        lyLeftInfo.addRow( "Database", readonlyEdit( database[0] ) )
        lyMidInfo.addRow( "Unique name", readonlyEdit( database[1] ) )
        lyRightInfo.addRow( "Inst name", readonlyEdit( instance[1] ) )

        lyLeftInfo.addRow( "Platform", readonlyEdit( database[3] ) )
        lyMidInfo.addRow( "Host name", readonlyEdit( instance[2] ) )
        lyRightInfo.addRow( "Version", readonlyEdit( instance[3] ) )

        lyLeftInfo.addRow( "Type", readonlyEdit( instance[4] ) )
        lyMidInfo.addRow( "Role", readonlyEdit( database[2] ) )
        lyRightInfo.addRow( "Log mode", readonlyEdit( database[5] ) )

        lyLeftInfo.addRow( "Open mode", readonlyEdit( database[4] ) )
        lyMidInfo.addRow( "Sessions", readonlyEdit( f"{sessions}/{params.get('sessions','')}" ) )
        lyRightInfo.addRow( "Processes", readonlyEdit( f"{processes}/{params.get('processes','')}" ) )

        lyLeftInfo.addRow( "Created", readonlyEdit( str(database[6]) ) )
        lyMidInfo.addRow( "Resetlogs", readonlyEdit( str(database[7]) ) )
        lyRightInfo.addRow( "Startup", readonlyEdit( str(instance[5]) ) )

        lyInfo.addLayout( lyLeftInfo )
        lyInfo.addLayout( lyMidInfo )
        lyInfo.addLayout( lyRightInfo )

        grInfo.setLayout( lyInfo )
        self.layout().addWidget( grInfo )

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


    def addConnectWidgets( self, layout ):
        def addParamWidget( layout, param ):
            label = param.replace("_"," ").title()
            if param == "mode":
                widget = QComboBox()
                widget.addItem( "Normal", "" )
                widget.addItem( "as SYSDBA", 2 )
                widget.addItem( "as SYSOPER", 4 )
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

    #def getConfig( self ):
    #    return dict( src="edit", name=str(self.editConnName.text()), params=self.getConnectParams() )

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
        self.mainWindow.disconnectAll()

    def clickedTest( self ):
        connectParams = dict( Config["Oracle"] ).copy()
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

    def clickedConnect( self ):
        if self.config.get("params","") != self.getConnectParams():
            print( self.config )
            print( self.getConnectParams() )
            self.config = dict( src="edit", name=str(self.editConnName.text()), params=self.getConnectParams() )
            self.mainWindow.treeConnections.addRecent( self.config )
        self.mainWindow.connectTo( self.config )

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
                widget.setCurrentText( text )
            else:
                widget.setText( text )

    def populateCache( self, table ):
        if self.mainWindow.currentConfig['src'] is not None:
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
            raise Exception( "Not connected!" )

    #def sizeHint( self ):
    #    return QSize( 800, 500 )
