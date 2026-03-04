from ..ui.win import childWin


"""Created by (c) Gennady Lapin, 2025-2026"""


class winSession( childWin ):

    def __init__( self, main, conn, sid, serial ):
        super().__init__( main, "Session detailed info", conn )
