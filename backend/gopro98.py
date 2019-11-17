import sys
import socket
import urllib
import os
#import socketio
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
#sio = socketio.Client()

def get_command_msg(id):
	return "_GPHD_:%u:%u:%d:%1lf\n" % (0, 0, 2, 0)

## for wake_on_lan
GOPRO_IP = '10.10.10.98'
GOPRO_MAC = 'DEADBEEF0000'
CAMNUM = "1"
LOCALPORT="10098"



def gopro_live():
	UDP_IP = "10.10.10.98"
	UDP_PORT = 8554
	KEEP_ALIVE_PERIOD = 2500
	KEEP_ALIVE_CMD = 2

	MESSAGE = get_command_msg(KEEP_ALIVE_CMD)
	try:
		response_raw = urlopen('http://'+UDP_IP+'/gp/gpControl').read().decode('utf-8')
		jsondata=json.loads(response_raw)
		response=jsondata["info"]["firmware_version"]
	except urllib.error.URLError as e: 
		ResponseData = e.reason
		print("connection to "+CAMNUM+" failed because of {0} exiting".format(ResponseData))
#		sio.emit('SS_CAM_FALLBACK', CAMNUM)												
#		sio.disconnect()
		sys.exit(0)
	if "HD4" in response or "HD3.2" in response or "HD5" in response or "HX" in response or "HD6" or "HD7" in response:
		urlopen("http://"+UDP_IP+"/gp/gpControl/execute?p1=gpStream&a1=proto_v2&c1=restart").read()
		## GoPro HERO4 Session needs status 31 to be greater or equal than 1 in order to start the live feed.
		if "HX" in response:
			connectedStatus=False
			print("retryinig connection")
			while connectedStatus == False:
				req=urlopen("http://"+UDP_IP+"/gp/gpControl/status")
				data = req.read()
				encoding = req.info().get_content_charset('utf-8')
				json_data = json.loads(data.decode(encoding))
				if json_data["status"]["31"] >= 1:
					connectedStatus=True
				print("-")
		subprocess.Popen("ffmpeg -i udp://10.10.10.100:"+LOCALPORT+" -fflags nobuffer -probesize 512  -c:v copy -b:v 5M -pix_fmt yuv420p -g 0 -an -f hls -hls_time 2 -hls_list_size 2 -hls_allow_cache 0 -hls_flags delete_segments /project/kiosk-app/streaming/gopro_"+CAMNUM+"_.m3u8", shell=True)
		#subprocess.Popen("ffmpeg -i 'udp://"+UDP_IP+":8555' -fflags nobuffer -f:v mpegts -probesize 8192 -an -vcodec copy /tmp/streaming/str", shell=True)
		#subprocess.Popen("ffmpeg -i 'udp://"+UDP_IP+":8555' -fflags nobuffer  -probesize 512 -b 2000k -minrate 2000k -maxrate 2000k  -an -c:v libx264 -tune zerolatency -g 0 -f hls -hls_time 2 -hls_list_size 2 -hls_flags delete_segments /project/kiosk-app/streaming/gopro.m3u8", shell=True)		
		if sys.version_info.major >= 3:
			MESSAGE = bytes(MESSAGE, "utf-8")
		print("\nRunning. Press ctrl+C to quit this application.\n")
		mtime=0	
		countcheck=0
		camDisabled=1
		while True:
			if countcheck <6:
				try:
					stat = os.stat('/project/kiosk-app/streaming/gopro_'+CAMNUM+'_.m3u8')				
					if stat.st_mtime != mtime:
						mtime=stat.st_mtime
						countcheck=0
						print('.')
						if camDisabled==1:
							camDisabled=0
#							sio.emit('SS_RESTART_CAM', CAMNUM)																		
					else:						
						countcheck=countcheck+1
				except FileNotFoundError:				
					countcheck=countcheck+1
			else:
				print('Process hanged. Exiting')
#				sio.emit('SS_CAM_FALLBACK', CAMNUM)												
#				sio.disconnect()
				sys.exit(0)
			try:
				sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
				sock.sendto(MESSAGE, (UDP_IP, UDP_PORT))
				sleep(KEEP_ALIVE_PERIOD/1000)		
			except OSError:
				sys.exit(0)

def quit_gopro(signal, frame):
	print("Exiting..")
#	sio.disconnect()
	sys.exit(0)

def wake_on_lan(macaddress):
	"""switches on remote computers using WOL. """
	#check macaddress format and try to compensate
	if len(macaddress) == 12:
		pass
	elif len(macaddress) == 12 + 5:
		sep = macaddress[2]
		macaddress = macaddress.replace(sep, '')
	else:
		raise ValueError('Incorrect MAC Address Format')
	#Pad the sync stream
	data = ''.join(['FFFFFFFFFFFF', macaddress * 20])
	send_data = bytes.fromhex(data)
	try:
		sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
		sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
		sock.sendto(send_data, (GOPRO_IP, 9))
	except OSError:
		sys.exit(0)

if __name__ == '__main__':
	#while True:
		print('start of cycle.. sleep')
		sleep(5) #in order not to start too often in FATAL cause
		print('wake up, Neo! connecting to server')
#		try:
#			sio.connect('http://kiosk.varius.local:3443')
#		except socketio.exceptions.ConnectionError:
#			print('cant start socket service')
#			sys.exit(0)
		wake_on_lan(GOPRO_MAC)
		signal.signal(signal.SIGINT, quit_gopro)
		print('cleaning')
		killemall = subprocess.Popen("rm -rf /project/kiosk-app/streaming/gopro_"+CAMNUM+"_*", shell=True)
		while killemall.poll() is None:
			pass				
		try:
			lsofret = subprocess.check_output("lsof -ti udp:"+LOCALPORT, shell=True).decode('utf-8')
			if lsofret:
				killffmpeg = subprocess.Popen("kill -9 "+lsofret, shell=True)
				while killffmpeg.poll() is None:
					pass							
		except subprocess.CalledProcessError as e:
			pass	
		print('starting main cycle')
		gopro_live()
		