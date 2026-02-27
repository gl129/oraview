import sqlparse
from PySide2.QtGui import QFont
from PySide2.QtWidgets import QSpacerItem, QHBoxLayout, QSizePolicy, QPlainTextEdit, QTextEdit, QPushButton
#from pygments import highlight
#from pygments.lexers import SqlLexer
#from pygments.formatters import HtmlFormatter
from ..ui.win import childWin


class winSql( childWin ):

    sqlBeautifierParams = dict(
            keyword_case = "upper",
            identifier_case = "lower",
            #reindent = True,
            reindent_aligned = True,
            wrap_after = 100
            #compact = True
            )

    def __init__( self, main, conn, sqlId ):
        super().__init__( main, f"SQL Information: {sqlId}", conn )
        self.sqlId = sqlId
        lyTop = QHBoxLayout()
        lyTop.addItem( QSpacerItem( 1, 1, QSizePolicy.Expanding, QSizePolicy.Preferred ) )
        btnRefresh = QPushButton( "Refresh" )
        #btnRefresh.setText( "Refresh" )
        btnRefresh.clicked.connect( self.refreshData )
        lyTop.addWidget( btnRefresh )
        btnBeautify = QPushButton( "Beautify" )
        #btnBeautify.setText( "Beautify" )
        btnBeautify.clicked.connect( self.beautify )
        lyTop.addWidget( btnBeautify )
        #btnColorize = QPushButton( "Colorize" )
        #btnColorize.clicked.connect( self.colorize )
        #lyTop.addWidget( btnColorize )
        self.layout().addLayout( lyTop )
        self.fullText = QTextEdit()
        self.fullText.setLineWrapMode( QTextEdit.NoWrap )
        self.fullText.setReadOnly( False )
        font = QFont('monospaced')
        font.setStyleHint( QFont.TypeWriter )
        font.setFixedPitch( True )
        self.fullText.setFont( font )
        self.layout().addWidget( self.fullText )
        self.refreshData()

    def refreshData( self ):
        clobFullText = self.cursor.execute( "SELECT sql_fulltext FROM v$sql where sql_id=:sqlid", {"sqlid":self.sqlId} ).fetchone()[0]
        self.fullText.setPlainText( clobFullText.read() )

    def beautify( self ):
        text = self.fullText.toPlainText()
        parserText = sqlparse.format( text, **self.sqlBeautifierParams )
        self.fullText.setPlainText( parserText )

    def colorize( self ):
        text = self.fullText.toPlainText()
        self.fullText.clear()
        #self.fullText.setStylesheet( )
        #html = highlight( text, SqlLexer(), HtmlFormatter( full=True, noclasses=True, nobackground=True ) )
        #print( html )
        #self.fullText.setHtml( html )

