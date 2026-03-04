import oracledb
from PySide2.QtGui import QFont, QIcon
from PySide2.QtCore import Qt, QTimer
from PySide2.QtWidgets import QHBoxLayout, QVBoxLayout, QFormLayout, QSpacerItem, QSizePolicy, QWidget, QTextBrowser, QPushButton, QComboBox, QMessageBox, QApplication

from ..ui.win import childWin


"""Created by (c) Gennady Lapin, 2025-2026"""


class dbComboBox( QComboBox ):

    def __init__( self, cursor, sql, binds ):
        super().__init__()
        self.cursor = cursor
        self.sql = sql
        self.binds = binds
        self.populated = False
        self.currentIndexChanged.connect( self.indexChanged )

    def mousePressEvent( self, event ):
        if not self.populated:
#            opt = QStyleOptionComboBox()
#            self.initStyleOption( opt )
#            sc = self.style().hitTestComplexControl( QStyle.CC_ComboBox, opt, event.pos(), self )
#            if sc == QStyle.SC_ComboBoxArrow:
            self.populateList()
        super().mousePressEvent( event )

    def indexChanged( self, index ):
        tooltip = self.itemData( index, Qt.ToolTipRole )
        if tooltip is None:
            tooltip = self.itemText( index )
        self.setToolTip( tooltip )

    def populateList( self ):
        self.clear()
        self.addItem( None )
        rows = self.cursor.execute( self.sql, self.binds ).fetchall()
        for value,tooltip in rows:
            self.addItem( QIcon(), str(value), value )
            self.setItemData( self.count()-1, None if tooltip is None else str(tooltip), Qt.ToolTipRole )
        #self.addItems( str(r[0]) for r in rows )
        self.populated = True


class winReport( childWin ):

    def __init__( self, mainWindow, oracle, sqlite, beg, end ):
        super().__init__( mainWindow, f"ASH Report from {beg} to {end}", oracle )
        self.beg = beg
        self.end = end

        sql = "SELECT distinct {col}, null FROM ash WHERE {col} IS not null AND sample_time BETWEEN :beg AND :end ORDER by 1"
        sql_hint = "SELECT distinct {ash_col}, {hint_col} FROM ash LEFT JOIN {hint_tab} ON {hint_id}={ash_id} WHERE {ash_col} IS not null AND sample_time BETWEEN :beg AND :end ORDER by 1"
        binds = dict( beg=self.beg, end=self.end )

        lyTop = QHBoxLayout()

        lyParams1 = QFormLayout()
        self.dropSid = dbComboBox( sqlite.cursor(), sql_hint.format(ash_col="SESSION_ID",hint_tab="dba_users",hint_col="USERNAME",hint_id="dba_users.USER_ID",ash_id="ash.USER_ID"), binds )
        lyParams1.addRow( "Session Id", self.dropSid )
        self.dropSqlId = dbComboBox( sqlite.cursor(), sql_hint.format(ash_col="ash.SQL_ID",hint_tab="v$sql",hint_col="substr(sql_text,1,100)",hint_id="v$sql.SQL_ID",ash_id="ash.SQL_ID"), binds )
        lyParams1.addRow( "Sql Id", self.dropSqlId )
        self.dropPlSqlEntry = dbComboBox( sqlite.cursor(), sql_hint.format(ash_col="PLSQL_ENTRY_OBJECT_ID",hint_tab="dba_objects",hint_col="OBJECT_TYPE||' '||OWNER||'.'||OBJECT_NAME",hint_id="OBJECT_ID",ash_id="PLSQL_ENTRY_OBJECT_ID"), binds )
        lyParams1.addRow( "PlSql Entry Id", self.dropPlSqlEntry )
        self.dropWaitClass = dbComboBox( sqlite.cursor(), sql.format(col="WAIT_CLASS"), binds )
        lyParams1.addRow( "WaitClass", self.dropWaitClass )
        lyTop.addLayout( lyParams1 )

        lyParams2 = QFormLayout()
        self.dropClientId = dbComboBox( sqlite.cursor(), sql.format(col="CLIENT_ID"), binds )
        lyParams2.addRow( "Client Id", self.dropClientId )
        self.dropService = dbComboBox( sqlite.cursor(), sql.format(col="SERVICE_HASH"), binds )
        lyParams2.addRow( "Service Hash", self.dropService )
        self.dropModule = dbComboBox( sqlite.cursor(), sql.format(col="MODULE"), binds )
        lyParams2.addRow( "Module", self.dropModule )
        self.dropAction = dbComboBox( sqlite.cursor(), sql.format(col="ACTION"), binds )
        lyParams2.addRow( "Action", self.dropAction )
        lyTop.addLayout( lyParams2 )

        lyTop.addItem( QSpacerItem( 1, 1, QSizePolicy.Expanding, QSizePolicy.Preferred ) )

        btnRefresh = QPushButton( "Refresh" )
        btnRefresh.clicked.connect( self.refreshData )
        lyTop.addWidget( btnRefresh )
        lyTop.setAlignment( btnRefresh, Qt.AlignRight|Qt.AlignBottom )

        self.layout().addLayout( lyTop )
        self.reportHtml = QTextBrowser()
        self.layout().addWidget( self.reportHtml )

        QTimer.singleShot( 100, self.refreshData )


    def refreshData( self ):
        QApplication.setOverrideCursor( Qt.WaitCursor )
        try:
            try:
                html = '\n'.join(
                    r[0] if r[0] is not None else '' for r in
                        self.cursor.execute(
                            "SELECT output FROM table( dbms_workload_repository.ash_report_html( sys_context('userenv','dbid'), sys_context('userenv','instance'), :beg, :end, 0, 0, :sid, :sqlid, :waitclass, :service, :module, :action, :clientid, :plsqlentry ) )",
                            dict( beg=self.beg, end=self.end, sid=self.dropSid.currentData(), sqlid=self.dropSqlId.currentData(), waitclass=self.dropWaitClass.currentData(), service=self.dropService.currentData(), module=self.dropModule.currentData(), action=self.dropAction.currentData(), clientid=self.dropClientId.currentData(), plsqlentry=self.dropPlSqlEntry.currentData() )
                        ).fetchall()
                )
                self.reportHtml.setHtml( html )
            finally:
                QApplication.restoreOverrideCursor()
        except oracledb.DatabaseError as e:
            if str(e).find( 'invalid identifier' ):
                QMessageBox.critical( self, "Invalid identifier", f"Logged user lack 'OEM_MONITOR' role\n\n{e}" )
            else:
                raise
#        finally:
#            self.cursor.rollback()
