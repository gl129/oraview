import sqlite3
import oracledb

from ..cf.conf import Config


cache_tables = { "users": "dba_users", "services": "dba_services", "objects": "dba_objects", "sqls": "v$sql" }


class dbcache():

    def __init__( self, db=None, cache=None ):
        self.connect( db, cache )

#    def prepareTable( self, 'createTable' ):
#        None

    def connect( self, db, cache ):
        self._db = db
        self._cache = cache
        if self._db and self._cache:
            """precreate cache tables"""
            self.get( "dba_users", ["USERNAME"], [("USER_ID",0)] )
            self.get( "dba_services", ["NAME"], [("NAME_HASH",0)] )
            self.get( "dba_objects", ["OBJECT_TYPE","OWNER","OBJECT_NAME"], [("OBJECT_ID",-1)] )
            self.get( "v$sql", ["SQL_TEXT"], [("SQL_ID","")] )
            cfg = Config["Oracle_prepopulate"]
            for key in cfg:
                if cfg.get(key,'N') == 'Y':
                    self.populate( cache_tables.get(key,'') )
        return self

    def close( self ):
        self.connect( None, None )

    def populate( self, table ):
        """table have to be present in cache"""
        if self._db and self._cache and table:
            cacheCursor = self._cache.cursor()
            cacheCursor.execute( f"PRAGMA table_info({table})" )
            rows = cacheCursor.fetchall()
            columns = [ r[1] for r in rows if r[1][0]!="_" ]
            index = [ f"{r[1]} is not null" for r in rows if r[3]==1 ]
            stmSelect = f"SELECT distinct {','.join(columns)} FROM {table} WHERE {'AND'.join(index)}"
            stmInsert = f"INSERT INTO {table}({','.join(columns)}) VALUES({','.join(['?' for c in columns])})"
            cacheCursor.execute( f"DELETE FROM {table}" )
            dbCursor = self._db.cursor()
            dbCursor.execute( stmSelect )
            while True:
                rows = dbCursor.fetchmany( 1000 )
                if not rows:
                    break
#                for row in rows:
#                    srow = tuple( str(c) if not c is None else None for c in row )
#                    cacheCursor.execute( stmInsert, srow )
                cacheCursor.executemany( stmInsert, rows )
                self._cache.commit()


    def get( self, table, cols, conds ):
        """one-table one-row selects only"""
        columns = ', '.join( cols )
        condition = 'AND '.join( [ str(c[0]) + '=:' + str(i) for i,c in enumerate(conds,start=1) ] )
        query = f"SELECT {columns} FROM {table} WHERE {condition}"
        binds = [ c[1] for c in conds ]
        row = None
        if self._cache:
            """cache database opened"""
            cacheCursor = self._cache.cursor()
            try:
                cacheCursor.execute( query, binds )
                row = cacheCursor.fetchone()
            except sqlite3.OperationalError as e:
                if self._db: # and str(e).find("no such"):
                    """no such table or column - wrong table structure and we have main database connection"""
                    pk_cols = [ c[0] for c in conds ]
                    all_columns = ', '.join( pk_cols + cols )
                    pk_columns = ', '.join( pk_cols )
                    createTable = f"CREATE TABLE {table} ( {all_columns}, _stamp DATE default current_date, PRIMARY KEY ({pk_columns})) WITHOUT ROWID"
                    cacheCursor.execute( f"DROP TABLE IF EXISTS {table}" )
                    cacheCursor.execute( createTable )
                else:
                    raise
        if self._db:
            """main database opened"""
            if not row:
                dbCursor = self._db.cursor()
                dbCursor.execute( statement=query, parameters=binds )
                row = dbCursor.fetchone()
                if not row:
                    """we want to cache even not-existent values"""
                    row = [ None for c in cols ]
                row = [ c.read() if isinstance(c,oracledb.LOB) else c for c in row ]
                pk_cols = [ c[0] for c in conds ]
                values  = [ c[1] for c in conds ] + list(row)
                all_columns = ', '.join( pk_cols + cols )
                val_places = ','.join( ':' + str(i) for i,v in enumerate(values,start=1) )
                insert = f"INSERT INTO {table} ( {all_columns} ) VALUES ( {val_places} )"
                try:
                    cacheCursor.execute( insert, values )
                    self._cache.commit()
                except:
                    self._cache.rollback()
                    raise
        if not row:
            row = [ None for c in cols ]
        return row
