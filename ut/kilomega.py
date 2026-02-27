

suffixes = [ "", "k", "M", "G", "T", "P", "E", "Z", "Y", "B" ]
bytes_units = [ (1024**i,s) for i,s in enumerate(suffixes) ][::-1]


def toKMGbytes( value: int ):

    if value < 0:
        sign = -1
        absValue = -value
    else:
        sign = 1
        absValue = value

    if absValue <= 1024:
        return f"{value} b"

    for pow,suffix in bytes_units:
        for margin,precision in [ (100,0), (10,1), (0.95,2) ]:
            if absValue > margin * pow:
                return f"{value/pow:.{precision}f} {suffix}b"
        #if value > 100 * pow:
        #    return f"{value/pow:.0f} {suffix}b"
        #if value > 10 * pow:
        #    return f"{value/pow:.1f} {suffix}b"
        #if value > 0.8 * pow:
        #    return f"{value/pow:.2f} {suffix}b"
    raise Exception( "FAILED" )
