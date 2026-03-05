import os
import sys
#import inspect
from datetime import datetime


"""Created by (c) Gennady Lapin, 2025-2026"""


_debug = os.getenv( "DEBUG" )
DEBUG = (None if _debug in ["","0"] else _debug) 
AUDIT = (DEBUG is not None)
basedir = os.path.dirname( sys.argv[0] ) + '/'


def debug():
    return DEBUG

def strip_base_py( path ):
    if path[ -3: ] == ".py":
        path = path[ :-3 ]
    lb = len( basedir )
    if basedir == path[ :lb ]:
        return path[ lb: ]
    for i,(b,p) in enumerate( zip(basedir,path) ):
        if b != p:
            return path[i:]

def audit( val='' ):
    if AUDIT:
        stamp = datetime.now().isoformat( sep=' ' )
        caller = sys._getframe( 1 ).f_code
        #caller = inspect.currentframe().f_back.f_code
        file = strip_base_py( caller.co_filename )
        func = caller.co_name
        print( f"{stamp}: {file}{' '+func if func!='<module>' else ''}: {val}" )

#        print( caller )
#        print( f"{datetime.now().isoformat(sep=' ')}: {__name__} {val}" )

#def debug( widget ):
#    meta = widget.metaObject()
#
#    for i in range( meta.propertyCount() ):
#        prop = meta.property( i )
#        name = prop.name()
#        value = widget.property( name )
#        print( f"{name} ({type(value)}) = {str(value)}" )
