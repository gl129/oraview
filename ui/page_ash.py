import numpy
import pandas
from datetime import timedelta
from matplotlib import dates
from PySide2.QtCore import Qt, QSize, QItemSelectionModel
from PySide2.QtGui import QIcon, QCursor, QPalette
from PySide2.QtWidgets import QWidget, QMenu, QAction, QMessageBox, QFileDialog
from PySide2.QtWidgets import QSplitter, QSpacerItem, QSizePolicy, QHBoxLayout, QVBoxLayout, QFormLayout
from PySide2.QtWidgets import QLabel, QGroupBox, QPushButton, QComboBox, QLineEdit, QTableView, QHeaderView, QScrollBar

from ..cf.conf import Config, loadConfig, saveConfig
from ..db.provider import dataProvider
from ..db.model import rawdataModel, groupModel, groupQueries
from ..db.cache import dbcache
from ..ui.plot import ashPlot
from ..ui.tttableview import ToolTipTableView
from ..ui.delegates import delegateLoadCell, delegateLeftElide
from ..ui.session import winSession
from ..ui.sql import winSql
from ..ui.report import winReport
from ..ut.debug import debug


def num2date( num ):
    return dates.num2date( num  ).replace( tzinfo=None )


class ashPage( QSplitter ):

    def __init__( self, mainWindow, dataProvider ):
        super().__init__( Qt.Orientation.Vertical )
        self.mainWindow = mainWindow
        self.data = dataProvider
        self.data.signalLoadCompleteAsh.connect( self.dataReady )

#        self._sqlite = sqlite
#        self._mutex = mutex
        #
        self.groups = groupModel( self )
        self.rawdata = rawdataModel( self )
        #
        if True:
            """top splitted area"""
            wPlot = QWidget()
            lyPlot = QVBoxLayout( wPlot )
            if True:
                """plot part"""
                self.plotAsh = ashPlot( self, self.data._sqlite )
                self.plotAsh.onselect_connect( self.selectedPlot )
                self.plotAsh.setMinimumHeight( 220 )
                lyPlot.addWidget( self.plotAsh )
                self.scrollAsh = QScrollBar( Qt.Horizontal )
                self.scrollAsh.setMinimum( -18000 )
                self.scrollAsh.setMaximum( 0 )
                self.scrollAsh.setPageStep( 3600 )
                self.scrollAsh.setSingleStep( 600 )
                #self.scrollAsh.setValue( 0 )
                self.scrollAsh.setTracking( True )
                self.scrollAsh.valueChanged.connect( self.scrollAshChanged )
                lyPlot.addWidget( self.scrollAsh )
            if True:
                """plot control part"""
                #wPlotControl = QWidget()
                #lyPlotControl = QHBoxLayout( wPlotControl )
                lyPlotControl = QHBoxLayout( )
                lyPlotControl.addWidget( QLabel("Selection From:") )
                self.editPlotSelBeg = QLineEdit()
                self.editPlotSelBeg.returnPressed.connect( self.selectedPlotEditsChanged )
                lyPlotControl.addWidget( self.editPlotSelBeg )
                lyPlotControl.addWidget( QLabel("To:") )
                self.editPlotSelEnd = QLineEdit()
                self.editPlotSelEnd.returnPressed.connect( self.selectedPlotEditsChanged )
                lyPlotControl.addWidget( self.editPlotSelEnd )
                lyPlotControl.addItem( QSpacerItem( 1, 1, QSizePolicy.Expanding, QSizePolicy.Preferred ) )
                self.btnReport = QPushButton( "ASH Report" )
                self.btnReport.clicked.connect( self.clickedReport )
                lyPlotControl.addWidget( self.btnReport )
                self.btnRefresh = QPushButton( "Refresh Now" )
                self.btnRefresh.clicked.connect( self.dataRefresh )
                lyPlotControl.addWidget( self.btnRefresh )
                self.btnPause = QPushButton( "Pause" )
                self.btnPause.setCheckable( True )
                self.btnPause.setChecked( False)
                self.btnPause.clicked.connect( self.clickedPause )
                lyPlotControl.addWidget( self.btnPause )
                lyPlot.addLayout( lyPlotControl )
                #lyPlot.addWidget( wPlotControl )
            self.addWidget( wPlot )
        if True:
            """bottom splitted area - text part"""
            spText = QSplitter( Qt.Orientation.Horizontal )
            if True:
                """load groups"""
                wGroups = QWidget()
                wGroups.setMinimumWidth( 200 )
                lyGroups = QVBoxLayout( wGroups )
#                if True:
#                    """groups controls"""
#                    grLoads = QGroupBox( "Load groups" )
#                    lyLoads = QHBoxLayout( grLoads )
                if True:
                    #wLoads = QWidget()
                    #wLoads.setSizePolicy( QSizePolicy.Expanding, QSizePolicy.Preferred )
                    #lyLoads = QHBoxLayout( wLoads )
                    lyLoads = QHBoxLayout( )
                    self.dropGroupBy = QComboBox()
                    for q in groupQueries:
                        self.dropGroupBy.addItem( q["title"], q )
                        self.dropGroupBy.currentIndexChanged.connect( self.changedGroupBy )
                    lyLoads.addWidget( self.dropGroupBy )
                    lyLoads.addItem( QSpacerItem( 1, 1, QSizePolicy.Expanding, QSizePolicy.Preferred ) )
                    self.editSelectedGroup = QLineEdit()
                    self.editSelectedGroup.returnPressed.connect( self.selectedGroupEditChanged )
                    lyLoads.addWidget( self.editSelectedGroup )
                    self.btnClearSelectedGroup = QPushButton( QIcon.fromTheme("edit-clear"), "" )
                    self.btnClearSelectedGroup.clicked.connect( self.btnClearSelectedGroupPressed )
                    lyLoads.addWidget( self.btnClearSelectedGroup )
                    lyGroups.addLayout( lyLoads )
                    #lyGroups.addWidget( wLoads )
                if True:
                    """groups table"""
                    #self.tabGroups = tabLoadGroups( self )
                    #self.tabGroups.setModel( self.groups )
                    #self.tabGroups.pressed.connect( self.pressedTabGroups )
                    #self.tabGroups.horizontalHeader().sectionResized.connect( lambda index,oldSize,newSize: self.saveTabColumnSize(self.tabGroups,index,newSize) )

                    #self.tabGroups = QTableView( self )
                    self.tabGroups = ToolTipTableView( self )
                    self.tabGroups.setModel( self.groups )
                    self.tabGroups.pressed.connect( self.pressedTabGroups )
                    self.tabGroups.horizontalHeader().sectionResized.connect( lambda index,oldSize,newSize: self.saveTabColumnSize(self.tabGroups,index,newSize) )
                    self.tabGroups.verticalHeader().setDefaultSectionSize( self.tabGroups.verticalHeader().minimumSectionSize() )
                    self.tabGroups.verticalHeader().setVisible( False )
                    self.tabGroups.horizontalHeader().setDefaultAlignment( Qt.AlignLeft )
                    self.tabGroups.horizontalHeader().setStretchLastSection( True )
                    self.tabGroups.setSelectionBehavior( QTableView.SelectRows )
                    self.tabGroups.setSelectionMode( QTableView.SingleSelection )
                    self.tabGroups.setWordWrap( False )
                    self.tabGroups.setModel( self.groups )
                    self.tabGroups.setItemDelegate( delegateLoadCell(self.groups) )
                    lyGroups.addWidget( self.tabGroups )
                spText.addWidget( wGroups )
            if True:
                """rawdata part"""
                self.wRawdata = QWidget()
                self.wRawdata.setMinimumWidth( 200 )
                lyRawdata = QVBoxLayout( self.wRawdata )
                if True:
                    self.expandedVisibility = [ wPlot, wGroups ]
                    btnExpandRawdata = QPushButton( "Expand" )
                    btnExpandRawdata.setCheckable( True )
                    btnExpandRawdata.setChecked( False)
                    btnExpandRawdata.clicked.connect( self.clickedExpandRawdata )
                    lyRawdata.addWidget( btnExpandRawdata )
                    lyRawdata.setAlignment( btnExpandRawdata, Qt.AlignRight|Qt.AlignTop )
                if True:
                    #self.tabRawdata = QTableView( self )
                    self.tabRawdata = ToolTipTableView( self )
                    #headerHeight = self.tabRawdata.horizontalHeader().height()
                    #sectionHeight = self.tabRawdata.verticalHeader().defaultSectionSize()
                    self.tabRawdata.verticalHeader().setDefaultSectionSize( self.tabRawdata.verticalHeader().minimumSectionSize() )
                    self.tabRawdata.horizontalHeader().setDefaultAlignment( Qt.AlignLeft )
                    self.tabRawdata.setWordWrap( False )
                    self.tabRawdata.setModel( self.rawdata )
                    self.tabRawdata.horizontalHeader().sectionResized.connect( lambda index,oldSize,newSize: self.saveTabColumnSize(self.tabRawdata,index,newSize) )
                    self.tabRawdata.setContextMenuPolicy( Qt.CustomContextMenu )
                    self.tabRawdata.customContextMenuRequested.connect( lambda pos: self.contextRawdata(pos) )
                    self.tabRawdata.horizontalHeader().setContextMenuPolicy( Qt.CustomContextMenu )
                    self.tabRawdata.horizontalHeader().customContextMenuRequested.connect( lambda pos: self.contextRawheader(pos) )
                    self.tabRawdata.setItemDelegate( delegateLeftElide() )
                    lyRawdata.addWidget( self.tabRawdata )
                spText.addWidget( self.wRawdata )
            spText.setMinimumHeight( 200 )
            spText.setSizes( [300,400] )
            spText.setCollapsible( 0, False )
            spText.setCollapsible( 1, False )
            self.addWidget( spText )
        self.setSizes( [200,400] )
        self.setCollapsible( 0, False )
        self.setCollapsible( 1, False )
        #self.addWidget( spMain )
        self.viewportClear( )

    def scrollAshChanged( self, val ):
        self.scrollAsh.setEnabled( False )
        try:
            if val == 0:
                self.viewportRefresh()
            else:
                self.dataReady()
        finally:
            self.scrollAsh.setEnabled( True )

    def bgErrorStyle( self ):
        r, g, b, a = self.palette().color( QPalette.Base ).getRgb()
        return f"rgb({min(r+50,255)}, {max(g-50,0)}, {max(b-50,0)})"

    def selectedPlot( self, beg, end ):
        if self.plotAsh.selectorVisible():
            self.editPlotSelBeg.setText( num2date( beg ).isoformat(sep=" ") )
            self.editPlotSelEnd.setText( num2date( end ).isoformat(sep=" ") )
        else:
            self.editPlotSelBeg.setText( "" )
            self.editPlotSelEnd.setText( "" )
        self.editPlotSelBeg.setStyleSheet( "" )
        self.editPlotSelEnd.setStyleSheet( "" )
        self.refreshGroupData( )

    def selectedPlotEditsChanged( self ):
        def datestr2num( date ):
            return dates.datestr2num( date )
        self.editPlotSelBeg.setStyleSheet( "" )
        self.editPlotSelEnd.setStyleSheet( "" )
        try:
            str = self.editPlotSelBeg.text()
            beg = datestr2num( str ) if len( str ) > 0 else None
        except:
            self.editPlotSelBeg.setStyleSheet( f"background-color: {self.bgErrorStyle()};" )
            beg = None
        try:
            str = self.editPlotSelEnd.text()
            end = datestr2num( str ) if len( str ) > 0 else None
        except:
            self.editPlotSelEnd.setStyleSheet( f"background-color: {self.bgErrorStyle()};" )
            end = None
        if beg and end:
            self.plotAsh.setSelector( (beg, end) )
            self.refreshGroupData()

    def clickedReport( self ):
        if self.data._oracle is not None:
            beg, end = self.plotAsh.getSelector()
            winReport( self.mainWindow, self.data._oracle, self.data._sqlite, num2date(beg), num2date(end) ).show()

    def clickedPause( self, checked ):
        if checked:
            self.btnPause.setText( ">Paused<" )
        else:
            self.btnPause.setText( "Pause" )
            self.viewportRefresh()

    def changedGroupBy( self, idx ):
        self.editSelectedGroup.setStyleSheet( "" )
        self.editSelectedGroup.clear()
        if idx >= 0:
            self.groups.setQuery( self.dropGroupBy.currentData() )
            self.refreshGroupData()

    def selectedGroupEditChanged( self ):
        self.editSelectedGroup.setStyleSheet( "" )
        vals = self.editSelectedGroup.text()
        if len( vals ) > 0:
            cols = self.dropGroupBy.currentData()["rawdata_cols"]
            vals = vals.split( "," )
            if len( vals ) == len( cols ):
                vals = [ int(v) if v.isdigit() else v for v in vals ]
            else:
                self.editSelectedGroup.setStyleSheet( f"background-color: {self.bgErrorStyle()};" )
                cols = vals = []
        else:
            cols = vals = []
        self.restoreGroupSelection( cols, vals )
        self.refreshRawData()

    def btnClearSelectedGroupPressed( self ):
        self.editSelectedGroup.clear()
        self.tabGroups.clearSelection()
        self.refreshRawData()

    def pressedTabGroups( self, index ):
        if index.isValid():
            cols, vals = self.groupSelection()
            self.editSelectedGroup.setText( ','.join( map(str,vals) ) )
            self.editSelectedGroup.setStyleSheet( "" )
            self.refreshRawData()

    def clickedExpandRawdata( self, checked ):
        for w in self.expandedVisibility:
            w.setVisible( not checked )

    def contextRawheader( self, pos ):
        columnId = self.tabRawdata.horizontalHeader().logicalIndexAt( pos )
        if columnId is not None and columnId != -1:
            menu = QMenu()
            actHide = QAction( "Hide column", self )
            actHide.triggered.connect( lambda: self.tabRawdata.hideColumn(columnId) )
            menu.addAction( actHide )
            actShowAll = QAction( "Temporary unhide all columns", self )
            actShowAll.triggered.connect( lambda: self.unhideAllTabColumns(self.tabRawdata) )
            menu.addAction( actShowAll )
            menu.exec_( QCursor.pos() )

    def contextRawdata( self, pos ):
        index = self.tabRawdata.indexAt( pos )
        if index.isValid():
            if index.column() != -1:
                columnName = self.tabRawdata.model().columnById( index.column() )
                model = self.tabRawdata.model()
                menu = QMenu()
                sqlId = model.getSqlId( index.row(), index.column() )
                if sqlId is not None:
                    actSql = QAction( "Show SQL text", self )
                    actSql.triggered.connect( lambda: winSql(self.mainWindow,self.data._oracle,sqlId).show() )
                    menu.addAction( actSql )
                sid, serial = model.getSession( index.row(), index.column() )
                if sid is not None:
                    actSession = QAction( "Show session details", self )
                    actSession.triggered.connect( lambda: winSession(self.mainWindow,self.data._oracle,sid,serial).show() )
                    menu.addAction( actSession )
                    killSession = QAction( f"Kill session {sid},{serial}", self )
                    killSession.triggered.connect( lambda: self.killSession(sid,serial) )
                    menu.addAction( killSession )
                menu.exec_( QCursor.pos() )

    def viewportClear( self ):
        #self.stopAutoRefresh()
        #self.data.close()
        #self.currentConfig = None
        self.data = None
        self.cache = None
        #
        self.plotAsh.setConn( None )
        self.groups.setConn( None )
        self.rawdata.setConn( None )
        #self.editPlotSelBeg.setText( "" )
        #self.editPlotSelEnd.setText( "" )
        self.btnRefresh.setDisabled( True )
        self.btnPause.setText( "Pause" )
        self.btnPause.setChecked( False )
        self.btnPause.setDisabled( True )
        self.dropGroupBy.setCurrentIndex( 0 )
        self.editSelectedGroup.setText("")

    def viewportSetup( self, data, cache ):
        self.data = data
        self.cache = cache
        #
        self.plotAsh.setConn( self.data._sqlite )
        self.groups.setConn( self.data._sqlite, self.cache )
        self.groups.setQuery( self.dropGroupBy.currentData() )
        self.rawdata.setConn( self.data._sqlite, self.cache )
        self.rawdata.setQuery( self.data._sqliteQuery, " ORDER BY sample_time desc" )
        self.btnPause.setDisabled( False )
        self.btnRefresh.setDisabled( False )
        self.scrollAsh.setValue( 0 )

    def dataReady( self ):
        if self.data:
            self.mainWindow.setStatus( "Plotting" )
            end = self.data.lastSampleTime + timedelta( seconds=self.scrollAsh.value() )
            beg = end - timedelta( hours=1 )
            self.plotAsh.plotData( beg, end, self.mainWindow.interval )
            if not self.plotAsh.selectorVisible() and self.scrollAsh.value() == 0:
                self.refreshGroupData()

    def dataRefresh( self ):
        self.data.loadDataAsh()
        scrollSeconds = -( self.data.lastSampleTime - self.data.firstSampleTime - timedelta(hours=1) ).total_seconds()
        self.scrollAsh.setMinimum( scrollSeconds )

    def viewportRefresh( self ):
        if not self.btnPause.isChecked() and self.scrollAsh.value() == 0:
            self.dataRefresh()

    def groupSelection( self ):
        inds = self.tabGroups.selectedIndexes()
        if inds:
            """ some row selected """
            row = inds[0].row()
            idCols = self.dropGroupBy.currentData()["rawdata_cols"]
            idVals = [ self.groups.cellData( row, i ) for i,col in enumerate( idCols )  ]
            return ( idCols, idVals )
        else:
            return ( [], [] )

    def restoreGroupSelection( self, cols, vals ):
        self.tabGroups.clearSelection()
        if len(cols)>0 and len(vals)>0:
            row = self.groups.locateFirst( range(len(cols)), vals )
            if row is not None:
                index = self.groups.index( row, 0 )
                self.tabGroups.selectionModel().setCurrentIndex( index, QItemSelectionModel.SelectCurrent|QItemSelectionModel.Rows )

    def refreshGroupData( self ):
        self.tabGroups.setUpdatesEnabled( False )
        cols, vals = self.groupSelection()
        beg, end = self.plotAsh.getSelector()
        self.groups.refreshModel( beg, end )
        self.restoreTabColumnSizes( self.tabGroups )
        self.restoreGroupSelection( cols, vals )
        self.tabGroups.setUpdatesEnabled( True )
        self.refreshRawData()

    def refreshRawData( self ):
        self.tabRawdata.setUpdatesEnabled( False )
        beg, end = self.plotAsh.getSelector()
        cols, vals = self.groupSelection()
        self.rawdata.refreshModel( beg, end, cols, vals )
        self.restoreTabColumnSizes( self.tabRawdata )
        self.tabRawdata.setUpdatesEnabled( True )

    def hideTabColumn( self, tableView, columnId ):
        tableView.hideColumn( columnId )
        self.saveTabColumnSize( tableView, ColumnId, 0 )

    def saveTabColumnSize( self, tableView, index, size ):
        columnName = tableView.model().columnById( index )
        if self.updateColSizes and columnName[0] != "_" and columnName != 'Load':
            Config[ "ColumnSizes" ][ columnName ] = str( size )

    def restoreTabColumnSizes( self, tableView ):
        self.updateColSizes = False
        for i,column in enumerate( tableView.model()._columns ):
            if column[0] == "_":
                tableView.hideColumn( i )
            else:
               tableView.showColumn( i )
            if column in Config[ "ColumnSizes" ]:
                size = int( Config["ColumnSizes"][column] )
                if size > 0:
                    tableView.setColumnWidth( i, int(size) )
                else:
                    tableView.hideColumn( i )
        self.updateColSizes = True

    def unhideAllTabColumns( self, tableView ):
        self.updateColSizes = False
        for i,column in enumerate( tableView.model()._columns ):
            if column[0] != "_":
                tableView.showColumn( i )
        self.updateColSizes = True

    def killSession( self, sid, serial ):
        if self.data._oracle:
            if QMessageBox.critical(
                    self,
                    "Killing session",
                    f"You are going to kill session {sid},{serial}.\nThis is dangerous and can lead to unforeseen consequences.\nPlease confirm.",
                    QMessageBox.Yes|QMessageBox.Cancel,
                    QMessageBox.Cancel
                                    ) == QMessageBox.Yes:
                cursor = self.data._oracle.cursor()
                cursor.execute( f"ALTER SYSTEM DISCONNECT SESSION '{sid},{serial}' IMMEDIATE" )
                QMessageBox.information( self, "Killing session", f"Session {sid},{serial} was killed" )
