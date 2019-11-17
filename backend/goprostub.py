import sys
import socket
import urllib
import os
#from urllib.request import urlopen --> module import error
# https://stackoverflow.com/questions/2792650/python3-error-import-error-no-module-name-urllib2
try:
    # For Python 3.0 and later
    from urllib.request import urlopen
except ImportError:
    # Fall back to Python 2's urllib2
    from urllib2 import urlopen
import subprocess
from time import sleep
import signal
import json
import re
import http

def get_command_msg(id):
	return "_GPHD_:%u:%u:%d:%1lf\n" % (0, 0, 2, 0)

## for wake_on_lan
GOPRO_IP = '10.10.10.99'
GOPRO_MAC = 'DEADBEEF0000'


def gopro_live():
	UDP_IP = "10.10.10.99"
	UDP_PORT = 8554
	KEEP_ALIVE_PERIOD = 2500
	KEEP_ALIVE_CMD = 2

	subprocess.Popen("ffmpeg -i /project/kiosk-app/PresentationData/lynx300m.mp4 -fflags nobuffer -probesize 512  -c:v copy -b:v 5M -pix_fmt yuv420p -g 0 -an -f hls -hls_time 8 -hls_list_size 8 -hls_allow_cache 0 -hls_flags delete_segments /project/kiosk-app/streaming/goprostub.m3u8", shell=True)
	print("\nRunning. Press ctrl+C to quit this application.\n")
	mtime=0	
	countcheck=0
	while True:
		if countcheck <8:
			try:
				stat = os.stat('/project/kiosk-app/streaming/goprostub.m3u8')				
				if stat.st_mtime != mtime:
					mtime=stat.st_mtime
					countcheck=0						
				else:						
					countcheck=countcheck+1
			except FileNotFoundError:				
				countcheck=countcheck+1
		else:
			print('Process hanged. Exiting')
			sys.exit(0)
		sleep(2500/1000)
def quit_gopro(signal, frame):
	print("Exiting..")
	sys.exit(0)

if __name__ == '__main__':
	sleep(5) #in order not to start too often in FATAL cause
	signal.signal(signal.SIGINT, quit_gopro)
	print('cleaning')
	killemall = subprocess.Popen("rm -rf /project/kiosk-app/streaming/goprostub*.*", shell=True)
	while killemall.poll() is None:
		pass				
	gopro_live()
