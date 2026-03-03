from PySide2.QtCore import Qt
from PySide2.QtGui import QIcon

def updateWinIcon( win ):
    pixmap = win.grab().scaled( 256, 256, Qt.KeepAspectRatio )
    win.setWindowIcon( QIcon(pixmap) )
