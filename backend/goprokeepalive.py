from goprocam import GoProCamera
from goprocam import constants
import time
gopro = GoProCamera.GoPro("detect","10.5.5.101")
gopro.stream('udp://127.0.0.1:10000','high')