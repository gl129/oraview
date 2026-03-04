import os
import sys
import signal
import traceback
import oracledb
from PySide2.QtCore import QTimer
from PySide2.QtWidgets import QApplication, QMessageBox

from .ui.main_window import MainWindow


"""Created by (c) Gennady Lapin, 2025-2026"""


oracledb.init_oracle_client()


def sigIntHandler( signum, frame ):
    """Ctrl-C handler"""
    QApplication.quit()
    print( "Terminated" )


def exceptionHandler( exc, val, trbk ):
    """Common exception handler with Details button"""

    def detailsHandler( btn ):
        if btn.text() == "Details":
            text = "\n".join(
                              [f"Exception: {str(exc)}",f"Value: {str(val)}",""]
                            + traceback.format_exception(exc,val,trbk)
                            )
            QMessageBox.information( None, "Exception traceback", text )
            print( text )

    msgBox = QMessageBox()
    msgBox.setIcon( QMessageBox.Critical )
    msgBox.setWindowTitle( f"{exc.__name__}" )
    msgBox.setText( f"Exception: {exc.__name__}\nValue: {val}" )
    msgBox.setStandardButtons( QMessageBox.Cancel )
    msgBox.addButton( "Details", QMessageBox.ActionRole )
    msgBox.buttonClicked.connect( detailsHandler )
    msgBox.exec()


if __name__ == "__main__":

    os.environ[ "QT_LOGGING_RULES" ] = "*.debug=false;qt.qpa.*=false"
    signal.signal( signal.SIGINT, sigIntHandler )
    sys.excepthook = exceptionHandler

    app = QApplication( sys.argv )

    timer = QTimer()
    timer.timeout.connect( lambda: None ) # do nothing, just wake up event loop to react for Ctrl-C
    timer.start( 100 )

    window = MainWindow( )
    window.show()

    sys.exit( app.exec_() )
