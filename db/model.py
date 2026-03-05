import sys
import numpy
import pandas
import matplotlib.dates as dates
from datetime import datetime
from PySide2.QtCore import Qt, QAbstractTableModel, QModelIndex

from ..ut.kilomega import toKMGbytes
from ..cf.const import constWaitLabels


"""Created by (c) Gennady Lapin, 2025-2026"""


class frameModel( QAbstractTableModel ):

    def __init__( self, parent=None ):
        super().__init__( parent )
        self.setFrame( pandas.DataFrame() )

    def setFrame( self, data ):
        self.beginResetModel()
        self._data = data
        self._columns = self._data.columns
        self.meta()
        self.endResetModel()

    def meta( self ):
        pass

    def rowCount( self, parent=QModelIndex() ):
        if parent.isValid():
            return 0
        return self._data.shape[0]

    def columnCount( self, parent=QModelIndex() ):
        if parent.isValid():
            return 0
        return len( self._columns )
        #return self._data.shape[1]

    def columnByName( self, name ):
        return self._columns.get_loc( name )

    def columnById( self, id ):
        return self._columns[ id ]

    def locateFirst( self, cols, vals ):
        colNums = [ c if isinstance(c,int) else self.columnByName(c) for c in cols ]
        for r in range( self.rowCount() ):
            colVals = [ self.cellData(r,c) for c in colNums ]
            if colVals == vals:
                return r

    def cellData( self, row, column ):
        if not isinstance( column, int ):
            column = self.columnByName( column )
        val = self._data.iat[ row, column ]
        if pandas.isnull( val ):
            return None
        elif isinstance( val, (float,numpy.number) ) and int( val ) == val:
            return int( val )
        else:
            return val

    def data( self, index, role=Qt.DisplayRole ):
        if index.isValid():
            if role == Qt.DisplayRole:
                return self.cellData( index.row(), index.column() )
        return None

    def headerData(self, section, orientation=Qt.Horizontal, role=Qt.DisplayRole ):
        if role == Qt.DisplayRole or role == Qt.ToolTipRole:
            if orientation == Qt.Horizontal:
                return self._columns[ section ]
                #return self._data.columns[ section ]
        return None

#    def setData( self, index, value, role ):
#        row = self._data.index[ index.row() ]
#        col = self._data.columns[ index.column() ]
#        dtype = self._data[col].dtype
#        if dtype != object:
#            value = None if value == '' else dtype.type(value)
#        self._data.set_value( row, col, value )
#        return True

#    def sort( self, column, order):
#        colname = self._data.columns.tolist()[column]
#        self.layoutAboutToBeChanged.emit()
#        self._data.sort_values(colname, ascending= order == QtCore.Qt.AscendingOrder, inplace=True)
#        self._data.reset_index(inplace=True, drop=True)
#        self.layoutChanged.emit()


class tableModel( frameModel ):

    def data( self, index, role=Qt.DisplayRole ):
        if index.isValid():
            columnName = self.columnById( index.column() )
            val = super().cellData( index.row(), index.column() )
            if val is not None and not pandas.isnull( val ):
                if role == Qt.DisplayRole:
                    return str( val )
                if role == Qt.TextAlignmentRole:
                    return Qt.AlignRight if isinstance( val, (int,float,numpy.number) ) or val.isdigit() or columnName == 'SAMPLE_TIME' else Qt.AlignLeft
#                if role == Qt.ToolTipRole and len( str(val) ) > 20:
#                        return str(val)
        return None

    def headerData(self, section, orientation=Qt.Horizontal, role=Qt.DisplayRole ):
        if role == Qt.DisplayRole and orientation == Qt.Vertical:
                return '[]'
        return super().headerData( section, orientation, role )


class dataModel( tableModel ):

    def __init__( self, parent ):
        super().__init__( parent )
        self._conn = None
        self._cache = None
        self._query = None

    def setConn( self, conn=None, cache=None ):
        self._conn = conn
        self._cache = cache
        if self._conn is None:
            self.emptyModel()

    def emptyModel( self ):
        self.setFrame( pandas.DataFrame() )
        self.layoutChanged.emit()

    def isCacheConnected( self ):
        return ( self._cache is not None )

    def setQuery( self, query ):
        self._query = query

    def refreshModel( self, params ):
        if self._conn and self._query:
            #self.parent().setStatus( "Compositing frame" )
            self.setFrame( pandas.read_sql( self._query, self._conn, params=params ) ) #.convert_dtypes() )
            self.layoutChanged.emit()


class timedModel( dataModel ):

    def __init__( self, parent ):
        super().__init__( parent )
        self._select = None
        self._order = None

    def setConn( self, conn=None, cache=None, query=None, order=None ):
        super().setConn( conn, cache )
        self.setQuery( )

    def setQuery( self, query=None, order=None ):
        self._select = query
        self._order = order

    def refreshModel( self, beg, end, cols=[], vals=[] ):
        if self._select:
            self._query = self._select
            #
            if not isinstance( beg, datetime ):
                beg = dates.num2date( beg )
            if not isinstance( end, datetime ):
                end = dates.num2date( end )
            secs = ( end - beg ).total_seconds()
            params = dict( beg=beg, end=end, secs=secs )
            #
            if len( cols ) > 0:
                def pythonize( val ):
                    return val.item() if isinstance( val, numpy.number ) else val
                #groupCond = ''.join( [ f' AND "{cols[i]}"=:gid{i}' for i in range(len(cols)) ] )
                groupCond = ''.join( [ f' AND "{col}"=:gid{i}' for i,col in enumerate(cols) ] )
                self._query += groupCond
                #groupParam = { f"gid{i}": pythonize(vals[i]) for i in range(len(vals)) }
                groupParam = { f"gid{i}": pythonize(val) for i,val in enumerate(vals) }
                params.update( groupParam )
            if self._order:
                self._query += self._order
            #
            super().refreshModel( params )


class sqlLookupTimedModel ( timedModel ):

    def getSession( self, row, column=0 ):
        return ( self.cellData( row, self.columnByName("SESSION_ID") ), self.cellData( row, self.columnByName("SESSION_SERIAL#") ) )

    def getSqlId( self, row, column ):
        columnName = self.columnById( column )
        if columnName.find("SQL_ID") >= 0 or columnName == "Sql":
            return self.cellData( row, column )
        return None

    def getObjectId( self, row, column ):
        columnName = self.columnById( column )
        if columnName == "CURRENT_OBJ#" or columnName.find("OBJECT_ID")>=0 or ( columnName == "Object" and val.isdigit() ):
            return self.cellData( row, column )
        return None

    def lookup( self, column ):
        pass

    def populate( self, table ):
        if self._cache:
            self._cache.populate( table )

    def data( self, index, role=Qt.DisplayRole ):
        if index.isValid() and role == Qt.ToolTipRole:
            columnName = self.columnById( index.column() )
            # because of cache data indexing
            val = self.cellData( index.row(), index.column() )
            if val is not None and self._cache:
                if columnName.find("SQL_ID") >= 0 or columnName == "Sql":
                    return self._cache.get( "v$sql", ["SQL_TEXT"], [("SQL_ID",val)] )[0]
                if columnName == "SQL_EXEC_START":
                    sqlTime = datetime.fromisoformat( val )
                    sampleTime = datetime.fromisoformat( self.cellData( index.row(),"SAMPLE_TIME" ) )
                    lag = str(sampleTime-sqlTime).split('.')[0] # cut subseconds
                    return f"{lag} before sample"
                if isinstance(val,(int,float,numpy.number)):
                    # check necessarity (was error in USER_ID column because of int64 not supported)
                    val = int( val )
                    if columnName in [ "USER_ID", "User" ]:
                        return self._cache.get( "dba_users", ["USERNAME"], [("USER_ID",val)] )[0]
                    if columnName in [ "SERVICE_HASH", "Service" ]:
                        return self._cache.get( "dba_services", ["NAME"], [("NAME_HASH",val)] )[0]
                    if columnName in [ "CURRENT_OBJ#", "Object" ] or columnName.find("OBJECT_ID")>=0:
                        ans = self._cache.get( "dba_objects", ["OBJECT_TYPE","OWNER","OBJECT_NAME"], [("OBJECT_ID",val)] )
                        if ans[0] is not None:
                            return f"{ans[0]} {ans[1]}.{ans[2]}"
                    if columnName.find("ALLOCATED") >= 0 or columnName.find("BYTES") >= 0:
                        if val >= 1024:
                            return toKMGbytes( val )
        return super().data( index, role )


class groupModel( sqlLookupTimedModel ):

    def setQuery( self, qparts=None ):
        if qparts is not None:
            idCols = ",".join( [ f'a."{c}" _{i}'  for i,c in enumerate(qparts["rawdata_cols"]) ] )
            oncpuColumn = f'''sum( case when wait_class is null then 1 else 0 end ) / :secs as "On CPU"'''
            labelColumns = [ f'''sum( case when wait_class='{c}' then 1 else 0 end ) / :secs as "{c}"''' for c in constWaitLabels if c!='On CPU' ]
            query = f'''\
                SELECT {idCols}, {qparts["select"]}, count(*)/:secs "Load", {oncpuColumn},{','.join(labelColumns)} \
                  FROM ash a {qparts["joins"]} \
                 WHERE sample_time between :beg and :end \
                 GROUP BY {qparts["group"]} \
                 ORDER BY count(*) desc'''
            super().setQuery( query )

    def meta( self ):
        try:
            loadCol = self._data.columns.get_loc( "Load" )
            self._columns = self._data.columns[ 0 : loadCol+1 ]
            self.maxLoad = self._data["Load"].max()
        except KeyError:
            self._columns = []

    def data( self, index, role=Qt.DisplayRole ):
        val = super().data( index )
        columnName = self.columnById( index.column() )
        if role == Qt.DisplayRole and columnName == "Load" and val is not None:
            #return round( float(val), 3 )
            return round( float(val), 2 )
        return super().data( index, role )


class rawdataModel( sqlLookupTimedModel ):
    None

groupQueries=[
    dict(
        title="Sessions",
        select='''a.session_id||','||a."SESSION_SERIAL#" "Session", ifnull(u.username,a.user_id) "User"''',
        group='''session_id,"SESSION_SERIAL#"''',
        joins='''LEFT JOIN dba_users u ON u.user_id=a.user_id''',
        rawdata_cols=("SESSION_ID","SESSION_SERIAL#")
    ),
    dict(
        title="Users",
        select='''ifnull(u.username,a.user_id) "User"''',
        group='''a.user_id''',
        joins='''LEFT JOIN dba_users u ON u.user_id=a.user_id''',
        rawdata_cols=("USER_ID",)
    ),
    dict(
        title="SQLs",
        select='''sql_id "Sql"''',
        group='''sql_id''',
        joins='',
        rawdata_cols=("SQL_ID",)
        ),
    dict(
        title="Objects",
        select='''ifnull(o.object_name||' '||o.owner||' '||o.object_type,a."CURRENT_OBJ#") "Object"''',
        group='''a."CURRENT_OBJ#"''',
        joins='''LEFT JOIN dba_objects o ON o.object_id=a."CURRENT_OBJ#"''',
        rawdata_cols=("CURRENT_OBJ#",)
    ),
    dict(
        title="Wait Events",
        select='''ifnull(wait_class,'On CPU') "WaitClass", event "Event"''',
        group='''wait_class,event''',
        joins='',
        rawdata_cols=("WAIT_CLASS",)
    ),
    dict(
        title="Services",
        select='''ifnull(s.name,a.service_hash) "Service"''',
        group='''s.name,a.service_hash''',
        joins='''LEFT JOIN dba_services s ON s.name_hash=a.service_hash''',
        rawdata_cols=("SERVICE_HASH",)
    )
]


