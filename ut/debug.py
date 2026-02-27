

def debug( widget ):
    meta = widget.metaObject()

    for i in range( meta.propertyCount() ):
        prop = meta.property( i )
        name = prop.name()
        value = widget.property( name )
        print( f"{name} ({type(value)}) = {str(value)}" )
