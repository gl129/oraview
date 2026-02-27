from PySide2.QtGui import QColor

from ..cf.conf import getConfig

constWaitLabels = [ "On CPU", "Scheduler", "System I/O", "User I/O", "Application", "Concurrency", "Commit", "Administrative", "Configuration", "Network", "Cluster", "Queueing", "Idle", "Other" ]
#constWaitColors = { l: QColor( Config["WaitColors"][l] ) for l in constWaitLabels }
constWaitColors = [ QColor( getConfig("WaitColors",l,'black') ) for l in constWaitLabels ]
