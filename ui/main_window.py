from PySide2.QtCore import Qt, QTimer, QSize
from PySide2.QtGui import QIcon
from PySide2.QtWidgets import QApplication, QMainWindow, QMessageBox
from PySide2.QtWidgets import QWidget, QStatusBar, QToolBar, QDockWidget, QAction, QLabel,  QTabWidget
from PySide2.QtWidgets import QTreeWidget, QTreeWidgetItem
from PySide2.QtWidgets import QSizePolicy

from ..cf.conf import Config, loadConfig, saveConfig
from ..ut.kilomega import toKMGbytes
from ..db.provider import dataProvider
from ..db.cache import dbcache
from ..ui.connect import connectDialog
from ..ui.connlist import connlistTreeWidget
from ..ui.page_ash import ashPage


class MainWindow( QMainWindow ):


    def __init__( self, ico_path ):
        super().__init__()
        self.windowsList = []

        self.setWindowTitle( "DBA Oracle Viewer" )
        self.resize( 1200, 800 )

        #self.setWindowIcon( QIcon(ico_path) )

        loadConfig()

        self.data = dataProvider( self )
        self.cache = dbcache( )
        #self.data.signalLoadComplete.connect( self.viewportRefresh )
        self.cache = dbcache( None, None )
        self.timer = QTimer( self )
        self.timer.timeout.connect( self.pageRefresh )

        self.labelConnName = QLabel( "Disconnected" )
        self.labelConnName.setFixedWidth( 200 )
        self.labelConnName.setAlignment( Qt.AlignRight )
        self.statusBar().addPermanentWidget( self.labelConnName, 200 )

        toolTop = QToolBar( "Main toolbar" )

        actConnect = QAction( "Connect", self )
        actConnect.setStatusTip( "Open new connection dialog" )
        actConnect.triggered.connect( self.clickedConnect )
        toolTop.addAction( actConnect )

        spacer = QWidget()
        spacer.setSizePolicy( QSizePolicy.Expanding, QSizePolicy.Preferred )
        toolTop.addWidget( spacer )

#        self.lMemUsage = QLabel( "0 b" )
#        toolTop.addWidget( self.lMemUsage )
#
#        lMemText = QLabel( " in memory db" )
#        toolTop.addWidget( lMemText )
#
#        toolTop.addSeparator()

        actAbout = QAction( "About", self )
        actAbout.setStatusTip( "About program and author" )
        actAbout.triggered.connect( self.clickedAbout )
        toolTop.addAction( actAbout )

        self.addToolBar( toolTop )

        self.treeConnections = connlistTreeWidget( self, self.data )
        dockWidget = QDockWidget( "Connections List" )
        dockWidget.setWidget( self.treeConnections )
        self.addDockWidget( Qt.LeftDockWidgetArea, dockWidget )

        tabCentral = QTabWidget()
        tabCentral.addTab( ashPage(self,self.data), "Sessions History" )
        tabCentral.currentChanged.connect( self.pageRefresh )
        self.setCentralWidget( tabCentral )

        self.disconnectAll( )


    def setStatus( self, msg ):
        self.statusBar().showMessage( msg )
        QApplication.processEvents()


    def setConnected( self, msg ):
        self.labelConnName.setText( msg )
        QApplication.processEvents()


    def clickedConnect( self ):
        dialog = connectDialog( self, self.currentConfig )
        dialog.exec()


    def clickedAbout( self ):
        mem = '<disconnected>'
        cols = ''
        modified = ''
        if self.data._sqlite is not None:
            cursor = self.data._sqlite.cursor()
            page_count = cursor.execute( 'PRAGMA page_count' ).fetchone()[0]
            page_size = cursor.execute( 'PRAGMA page_size' ).fetchone()[0]
            mem = toKMGbytes( page_count * page_size )
            rows = cursor.execute( 'SELECT count(*) FROM ash' ).fetchone()[0]
            cursor.close()
            (inss,dels) = self.data.rowsModified()
            modified = f"{inss}/{dels}"
        text = "oraView:\n"     \
               "  - ashView\n"  \
               "  - sessView\n" \
               "  - statView\n" \
               "\n"             \
               "Created by Gennady Lapin, 2025-2026\n" \
               "\n"             \
               f"In-memory DB usage: {mem}, rows: {rows}\n" \
               f"Last time inserted/deleted: {modified}"
        QMessageBox.about( self, "About", text )


    def disconnectAll( self ):
        self.stopAutoRefresh( )
        self.currentConfig = dict( src=None, name=None, params={} )
        self.cache.close( )
        self.data.close( )
        self.viewportClear( )
        self.setConnected( 'Disconnected' )
        saveConfig( )


    def connectTo( self, config ):
        self.disconnectAll( )
        self.currentConfig = config
        try:
            self.data.oracleConnect( self.currentConfig )
            self.cache.connect( self.data._oracle, self.data._sqlite )
            self.setConnected( f"'{self.currentConfig.get('name','<unknown>')}' connected" )
            self.viewportSetup( )
            self.startAutoRefresh( )
        except:
            self.disconnectAll( )
            raise


    def viewportClear( self ):
        for i in range( self.centralWidget().count() ):
            self.centralWidget().widget( i ).viewportClear( )
        self.setStatus( "Ready" )
        self.setWindowIcon( QIcon(self.grab()) )


    def viewportSetup( self ):
        self.interval = 10
        self.timer.setInterval( self.interval * 1000 )
        for i in range( self.centralWidget().count() ):
            self.centralWidget().widget( i ).viewportSetup( self.data, self.cache )


    def startAutoRefresh( self ):
        self.pageRefresh()
        self.timer.start()


    def stopAutoRefresh( self ):
        self.timer.stop()


    def pageRefresh( self ):
        self.centralWidget().currentWidget().pageRefresh()
        self.setStatus( "Ready" )
        self.setWindowIcon( QIcon(self.grab()) )


#    def viewportRefresh( self ):
#        self.centralWidget().currentWidget().viewportRefresh()
#        self.setStatus( "Ready" )


    def closeEvent( self, event ):
        saveConfig( )
        for win in self.windowsList:
            win.close()
