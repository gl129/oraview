import pandas
from datetime import datetime, timedelta
from matplotlib import dates
from matplotlib.figure import Figure
from matplotlib.widgets import SpanSelector
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from PySide2.QtGui import QColor, QPalette
from PySide2.QtCore import Signal
from PySide2.QtWidgets import QWidget, QVBoxLayout

from ..cf.const import constWaitLabels, constWaitColors
from ..ut.debug import audit


"""Created by (c) Gennady Lapin, 2025-2026"""


def qcolor2mpl( qcolor ):
#    r, g, b, a = qcolor.getRgb()
#    mpl_color = (r / 255.0, g / 255.0, b / 255.0, a / 255.0)
    return tuple( c/255.0 for c in qcolor.getRgb() )


class visualPlot( QWidget ):

    signalSelectorChanged = Signal( datetime, datetime )

    def __init__( self, parent ):
        super().__init__( parent )
        #
        self.bgColor = qcolor2mpl( self.palette().color(QPalette.ColorRole.Window) )
        self.textColor = qcolor2mpl( self.palette().color(QPalette.ColorRole.WindowText) )
        self.buttonColor = qcolor2mpl( self.palette().color(QPalette.ColorRole.Button) )
        self.plotColors = [ qcolor2mpl(c) for c in constWaitColors ]
        #
        self._figure = Figure( constrained_layout=True )
        self._canvas = FigureCanvas( self._figure )
        layout = QVBoxLayout()
        layout.addWidget( self._canvas )
        self.setLayout( layout )
        self.ax = self._figure.add_subplot( 111 )
        self.selector = SpanSelector( self.ax, self._onselect, 'horizontal', props=dict(facecolor=self.textColor,alpha=0.3), useblit=True, interactive=True ) #, snap_values=self.ax.get_xlim() )
        self.plotEmpty()

    def _onselect( self, xmin, xmax ):
        sel = self.getSelector()
        self.signalSelectorChanged.emit( *sel )

    def selectorVisible( self ):
        return self.selector.visible

    def getSelector( self ):
        if self.selector.visible:
            xmin, xmax = self.selector.extents
            if xmin > xmax:
                xmin, xmax = xmax, xmin
        else:
            _, xmax = self.ax.get_xlim()
            xmin = xmax - 10/1440.0
        return ( xmin, xmax )

    def resetSelector( self ):
        self.selector.set_visible( False )
        self._canvas.draw_idle()
        #self.signalSelectorChanged.emit( None, None )

    def setSelector( self, sel ):
        self.selector.extents = sel
        self.selector.set_visible( True )
        self._canvas.draw_idle()

    def plotEmpty( self ):
        self.ax.clear()
        self.ax.set_xlim( datetime.now()-timedelta(hours=1), datetime.now() )
        self.ax.stackplot( [], [[] for l in constWaitLabels], labels=constWaitLabels, colors=self.plotColors )
        self.plotDecor( )
        self._canvas.draw()

    def plotData( self, data ):
        audit()
        self.ax.clear()
        self.ax.stackplot( data.index, data.T, labels=data.columns, colors=self.plotColors )
        self.plotDecor( )
        self._canvas.draw()

    def plotDecor( self ):
        self.ax.margins( x=0., y=0. )
        locator =  dates.MinuteLocator( byminute=range(0,60,10) )
        self.ax.xaxis.set_major_locator( locator )
        #self.ax.xaxis.set_minor_locator( dates.MinuteLocator() )
        self.ax.xaxis.set_major_formatter( dates.ConciseDateFormatter(locator) )
        # !!!
        #self.ax.set_xlim( datetime.now()-timedelta(hours=1), datetime.now() )
        self._figure.set_facecolor( self.buttonColor )
        self.ax.set_facecolor( self.bgColor )
        self.ax.xaxis.label.set_color( self.textColor )
        self.ax.tick_params( colors=self.textColor, labelcolor=self.textColor, grid_color=self.textColor, which='both' )
        self.ax.grid( which='major', linestyle=':') #, linewidth=0.2 ) #, alpha=0.5 )
        for spine in self.ax.spines.values():
            spine.set_color( self.textColor )
        self.ax.legend( reverse=True, loc='upper left', bbox_to_anchor=(1.01,1), borderaxespad=0., fontsize='small', borderpad=0, labelspacing=0, facecolor=self.bgColor, labelcolor=self.textColor, edgecolor=self.bgColor )
        #self._figure.tight_layout()


class ashPlot( visualPlot ):

    def __init__( self, parent, conn ):
        super().__init__( parent )
        self._conn = conn
        self._query = None

    def setConn( self, conn ):
        self.resetSelector()
        self._conn = conn
        if self._conn is None:
            self.plotEmpty()

    def buildQuery( self ):
        sampletimeColumn = "datetime((strftime('%s',sample_time)/:interval)*:interval,'unixepoch')"
        oncpuColumn = f'''sum( case when wait_class is null then 1 else 0 end )*1.0/:interval as "On CPU"'''
        labelColumns = [ f'''sum( case when wait_class='{l}' then 1 else 0 end )*1.0/:interval as "{l}"''' for l in constWaitLabels if l !='On CPU' ]
        #ashQuery = f"""SELECT {sampletimeColumn} as "SampleTime", {oncpuColumn}, {', '.join( labelColumns )} FROM ash WHERE sample_time between :beg and :end GROUP BY {sampletimeColumn} ORDER BY 1"""
        ashQuery = f"""
                WITH recursive timeline(dt) as (select :beg union all select datetime(dt,'+'||:interval||' second') from timeline where dt<:end)
                SELECT {sampletimeColumn} as "SampleTime", {oncpuColumn}, {', '.join( labelColumns )} 
                  FROM (select sample_time, wait_class from ash union all select dt, '-' from timeline)
                 WHERE sample_time between :beg and :end 
                 GROUP BY {sampletimeColumn} 
                 ORDER BY 1"""
        self._query = ashQuery

    def plotData( self, beg, end, interval ):
        if self._conn:
            if not self._query:
                self.buildQuery( )
            if beg and end and interval:
                data = pandas.read_sql_query( self._query, self._conn, params={"beg":beg,"end":end,"interval":interval}, parse_dates={"SampleTime":{"format":"%Y-%m-%d %H:%M:%S"}}, index_col=["SampleTime"] )
                super().plotData( data )
