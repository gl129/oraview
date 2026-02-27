from PySide2.QtCore import Qt, QRect
from PySide2.QtGui import QPainter
from PySide2.QtWidgets import QStyledItemDelegate
from ..cf.const import constWaitColors


class delegateLoadCell( QStyledItemDelegate ):

    def __init__( self, model=None ):
        super().__init__( )
        self.model = model

    def paint( self, painter: QPainter, option, index ):
        super().paint( painter, option, index )
        if self.model.columnById( index.column() ) == "Load":
            row = index.row()
            start = index.column()+1
            values = self.model._data.iloc[ row, start: ]
            x, y, width, height = option.rect.getRect()
            ratio = (width-50) / self.model.maxLoad
            painter.save()
            try:
                for i,val in enumerate( values ):
                    width = val * ratio
                    rect = QRect( x+2, y+2, width, height-4 )
                    painter.fillRect( rect, constWaitColors[i] )
                    x += width
            finally:
                painter.restore()


class delegateLeftElide( QStyledItemDelegate ):

    def initStyleOption( self, option, index ):
        super().initStyleOption( option, index )
        if option.displayAlignment == Qt.AlignRight:
            option.textElideMode = Qt.ElideLeft
