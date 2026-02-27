from ..ui.win import childWin


class winSession( childWin ):

    def __init__( self, main, conn, sid, serial ):
        super().__init__( main, "Session detailed info", conn )
