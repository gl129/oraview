
from PySide2.QtCore import Qt
from PySide2.QtGui import QFontMetrics
from PySide2.QtWidgets import QTableView


class ToolTipTableView( QTableView ):

    def __init__( self, parent=None ):
        super().__init__( parent )
        self.setMouseTracking( True )

    def mouseMoveEvent( self, event ):
        index = self.indexAt( event.pos() )
        if index.isValid( ) and self.model().data( index, Qt.ToolTipRole ) is None:
            text = str( self.model().data( index, Qt.DisplayRole ) )
            metrics = QFontMetrics( self.font() )
            text_width = metrics.horizontalAdvance( text )
            cell_width = self.visualRect( index ).width( )
            if text_width > cell_width:
                self.setToolTip(text)
            else:
                self.setToolTip("")
        super().mouseMoveEvent( event )
