import urllib
import json
import os.path
import urllib2
import time as time_
import math
import os
from selenium import webdriver
from selenium.webdriver.common.keys import Keys
#from gps import *

# configuration for url path
down_path = '/root/work/raspberry pi/videos/'
url = 'http://localhost/video'
html_path = 'file:///root/work/raspberry%20pi/'
threshold = 5000 # 5Km


def download_video(url, filename):
	'''
	download video with url to downpath
	return True if success, False if not
	'''
	try:
		mp4file = urllib2.urlopen(url)
		with open(down_path+filename, 'wb') as output:
			while True:
				data = mp4file.read(8192)
				if data:
				    output.write(data)
				else:
				    break
		return True
	except IOError:
		return False	        
		        
		        
def get_gps():
	'''
	return gps value
	'''
	#gpsc = GpsController()
	#gpsc.start()
	#return [gpsc.fix.latitude, gpsc.fix.longitude]
	#gpsc.stopController()
	return [6.928318, 79.8881236] 
	
	     
def get_distance(pos1, pos2):
	'''
	calculate the distance between two gps positions (latitude, longitude)
	'''
	lat1 = pos1[0]
	lon1 = pos1[1]
	lat2 = float(pos2[0])
	lon2 = float(pos2[1])
	
	R = 6371  # Radius of the earth in km
	dLat = math.radians(lat2-lat1)  # deg2rad below
	dLon = math.radians(lon2-lon1) 
	a = math.sin(dLat/2) * math.sin(dLat/2) + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dLon/2) * math.sin(dLon/2)
	 
	c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a)) 
	return R * c * 1000 # Distance in m
	
		
def delete_old_files():
	'''
	delete files older than 7 days
	'''
	now = time_.time()
	# check the downloaded files except default file
	for f in os.listdir(down_path):
		if f != 'default.mp4':
			if os.stat(os.path.join(down_path,f)).st_mtime < now - 7 * 86400:
				os.remove(down_path+f)
	
	
browser = webdriver.Firefox()
browser.get(html_path + 'video_auto.html')
#browser.maximize_window()
time_.sleep(0.3)
elem = browser.find_element_by_id('myVideo')
elem.send_keys(Keys.F11)

videos = []
tracker = 0
pre_filename = ''

while True:
	pos = get_gps()
	# every minute
	if tracker % 4 == 0:		
		try:
			# get the json from the server api
			res = urllib.urlopen(url)
			data = json.loads(res.read())
			videos = data['videos']
		except IOError:
			time_.sleep(15)
			continue
			
		# calculate new priority based on the gps value and the original priority
		for video in videos:
			if 'center' in video:
				video['priority'] += (get_distance(pos, video['center'].split(',')) - threshold) / 100
			
		#sort the video according to the gps value and priority
		video_list = sorted(videos, key=lambda k: k['priority']) 
		
		flag_continue = False
		# download the video with highest priority which is not downloaded
		for video in video_list:
			video_url = video['url']
			# get the exact filename	
			filename = video_url.split('/')[-1]
			# if not downloaded download it
			if not os.path.isfile(down_path+filename):
				if download_video(video_url, filename) == False:
					flag_continue = True
					break
					
				if 'center' in video:
					break
				json_element = {'file': filename, 'priority': video['priority']}
				#push({"teamId":"4","status":"pending"});
				browser.execute_script("videoSource.push(%s)" % json.dumps(json_element))
				break
		if flag_continue:
			continue
			pre_filename = ''
					
	time_.sleep(15)
	tracker += 1
	
	# loop through the json and check whether it is in the range 
	# if it is, check it is playing now and play the video
	for video in videos:
		if 'center' in video:
			if get_distance(pos, video['center'].split(',')) <= video['radius']:				
				video_url = video['url']
				# get the exact filename	
				filename = video_url.split('/')[-1]
				if pre_filename != filename:
					pre_filename = filename
					browser.execute_script("videoPlay('%s');" % filename)
				break
		
	# delete files older than 7 days	
	# check twice a day
	if tracker >= 2880:
		tracker = 0
		delete_old_files()


