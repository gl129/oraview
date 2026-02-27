from PySide2.QtCore import Qt, QSize
from PySide2.QtWidgets import QMessageBox
from PySide2.QtWidgets import QTreeWidget, QTreeWidgetItem, QMenu, QAction

from ..cf.conf import Config, literalEval
from ..ui.connect import connectDialog


class connlistTreeWidget( QTreeWidget ):

    def __init__( self, mainWindow, data ):
        super().__init__()
        self.mainWindow = mainWindow
        self.data = data

        self.setColumnCount( 1 )
        self.setMouseTracking( True )
        self.header().setVisible( False )

        self.listRecent = QTreeWidgetItem( ["Recent"] )
        self.listRecent.setStatusTip( 0, "Recently used not saved connections" )

        self.listSaved = QTreeWidgetItem( ["Saved"] )
        self.listSaved.setStatusTip( 0, "Saved connections" )
        self.refreshSaved()

        self.listTns = QTreeWidgetItem( ["TnsNames"] )
        self.listTns.setStatusTip( 0, "TnsNames.ora connections" )
        self.refreshTns()

        for item in [ self.listRecent, self.listSaved, self.listTns ]:
            self.addTopLevelItem( item )
        self.expandAll()

        self.itemDoubleClicked.connect( self.doubleClicked )
        self.setContextMenuPolicy( Qt.CustomContextMenu )
        self.customContextMenuRequested.connect( self.contextMenu )


    def doubleClicked( self, item, column ):
        config = item.data( 0, Qt.UserRole )
        self.mainWindow.connectTo( config )

    def contextMenu( self, pos ):
        item = self.itemAt( pos )
        if not item:
            return
        config = item.data( 0, Qt.UserRole )
        if not config:
            return
        menu = QMenu()
        actConnect = QAction( "Connect", self )
        actConnect.triggered.connect( lambda: self.mainWindow.connectTo(config) )
        menu.addAction( actConnect )
        menu.setDefaultAction( actConnect )
        actEdit = QAction( "Edit", self )
        actEdit.triggered.connect( lambda: self.openConnectDialog(config) )
        menu.addAction( actEdit )
        if config.get("src","") in [ "saved", "edit" ]:
            actDelete = QAction( "Delete", self )
            actDelete.triggered.connect( lambda: self.deleteConnection(item) )
            menu.addAction( actDelete )
        menu.exec_( self.mapToGlobal( pos ) )

    def openConnectDialog( self, config ):
        dialog = connectDialog( self.mainWindow, config )
        dialog.exec()

    def deleteConnection( self, item ):
        config = item.data( 0, Qt.UserRole )
        name = config.get( "name", "" )
        if QMessageBox.question( self, "Delete Connection",
                f"Connection: {name}\nParameters: {str(config.get('params',''))}\n\nAre you sure delete it?",
                QMessageBox.Yes|QMessageBox.Cancel ) != QMessageBox.Yes:
            return
        if config.get("src","") == "saved":
            self.listSaved.removeChild( item )
            del Config["SavedSessions"][ name ]
        elif config.get("src","") == "edit":
            self.listRecent.removeChild( item )

    def refreshSaved( self ):
        self.setUpdatesEnabled( False )
        for c in self.listSaved.takeChildren():
            self.listSaved.removeChild( c )
        savedSessions = Config[ "SavedSessions" ]
        for c in savedSessions:
            item = QTreeWidgetItem( [ c ] )
            params = literalEval( savedSessions[c] )
            item.setData( 0, Qt.UserRole, dict( src="saved", name=c, params=params ) )
            item.setToolTip( 0, str(params) )
            self.listSaved.addChild( item )
        self.listSaved.sortChildren( 0, Qt.AscendingOrder )
        self.setUpdatesEnabled( True )

    def refreshTns( self ):
        self.setUpdatesEnabled( False )
        for c in self.listTns.takeChildren():
            self.listTns.removeChild( c )
        for c in self.data.tnsnames():
            item = QTreeWidgetItem( [ c ] )
            item.setData( 0, Qt.UserRole, dict( src="tns", name=c, params=dict(dsn=c) ) )
            self.listTns.addChild( item )
        #self.listTns.sortChildren( 0, Qt.AscendingOrder )
        self.setUpdatesEnabled( True )

    def addRecent( self, config ):
        name = config.get( "name", "-noname-" )
        item = QTreeWidgetItem( [ name ] )
        item.setData( 0, Qt.UserRole, config )
        item.setToolTip( 0, str( config.get("params","") ) )
        self.listRecent.insertChild( 0, item )

    def sizeHint( self):
        """ need to specify start size of connect-list dock widget """
        return QSize( 144, 256 )
