from PySide2.QtCore import Qt, QSize
from PySide2.QtGui import QIcon
from PySide2.QtWidgets import QDialog, QVBoxLayout

class childWin( QDialog ):

    def __init__( self, mainWindow, title, conn=None ):
        super().__init__( None )
        self.mainWindow = mainWindow
        self.mainWindow.windowsList.append( self )
        self.setWindowTitle( title )
        self.setWindowIcon( self.mainWindow.windowIcon() )
        self.setSizeGripEnabled( True )
        self.setLayout( QVBoxLayout( self ) )
        if conn:
            self.cursor = conn.cursor()

    def sizeHint( self ):
        return QSize( 800, 500 )

    def keyPressEvent( self, event ):
        if event.key() == Qt.Key_Escape:
            self.close()
        else:
            super().keyPressEvent( event )

    def showEvent( self, event ):
        self.setWindowIcon( QIcon(self.grab()) )

    def closeEvent( self, event ):
        self.mainWindow.windowsList.remove( self )
