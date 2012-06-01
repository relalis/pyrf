#!/usr/bin/env python
# -*- coding: utf-8 -*-

# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.


#rapidshare config
USER = ''
PASS = ''
USSL = False

import sys
import os
import urllib
import time
import re
import argparse
import md5

def say(message):
	print message

def error(message):
	print 'ERROR: ' + message

def progress(done, ind_size, size):
	total = float((done * ind_size * 100) / size)
	progress = float(done * ind_size / 1024)
	speed = (float(done * ind_size) / float(time.time() - starttime)) / 1024
	sys.stdout.write('Progress: %.0f%%, Complete: %.2fKb, Speed: %.3fkb/s\r' % (total, progress, speed))
	sys.stdout.flush()

def download(src, dest):
	global starttime
	starttime = time.time()
	filename, headers = urllib.urlretrieve(src, dest, progress)
	sys.stdout.write('Complete: 100%\n')
	sys.stdout.flush()
	for a in headers:
		if a.lower() == 'content-disposition':
			filename = headers[a][headers[a].find('filename=') + 9:]
	urllib.urlcleanup()
	return filename

# Based on rsapiget by George Notaras
def rsdl(link, USER=None, PASS=None):
	try:
		rapidshare, files, fileid, filename = link.rsplit('/') [-4:]
	except ValueError:
		error('Invalid Rapidshare link')
		return
	if not rapidshare.endswith('rapidshare.com') or files != 'files':
		error('Invalid Rapidshare link')
		return
	if USSL:
		proto = 'https'
	else:
		proto = 'http'
	say('Downloading: %s' % link)
	if filename.endswith('.html'):
		target_filename = filename[:-5]
	else:
		target_filename = filename
	say('Save file as: %s' % target_filename)
	
	params = {
		'sub': 'download',
		'fileid': fileid,
		'filename': filename,
		'try': '1',
		'withmd5hex': '0',
		}
	if USER and PASS:
		params.update({
			'login': USER,
			'password': PASS,
			})
	params_string = urllib.urlencode(params)
	api_url = '%s://api.rapidshare.com/cgi-bin/rsapi.cgi' % proto
	conn = urllib.urlopen('%s?%s' % (api_url, params_string))
	data = conn.read()
	conn.close()
	try:
		key, value = data.split(':')
	except ValueError:
		error(data)
		return
	try:
		server, dlauth, countdown, remote_md5sum = value.split(',')
	except ValueError:
		error(data)
		return
	#free account wait
	if int(countdown):
		for t in range(int(countdown), 0, -1):
			sys.stdout.write('Waiting for %s seconds..\r' % t)
			sys.stdout.flush()
			time.sleep(1)
		say('Waited for %s seconds, downloading' % countdown)
	
	dl_params = {
		'sub': 'download',
		'fileid': fileid,
		'filename': filename,
		}
	if USER and PASS:
		dl_params.update({
			'login': USER,
			'password': PASS,
			})
	else:
		dl_params.update({
			'dlauth': dlauth,
			})
	dl_params_string = urllib.urlencode(dl_params)
	download_link = '%s://%s/cgi-bin/rsapi.cgi?%s' % (proto, server, dl_params_string)
	downloaded_filename = download(download_link, target_filename)

def mfdl(link):
	conn = urllib.urlopen(link)
	data = conn.read()
	conn.close()
	dlink = re.search("kNO = \"(.*)\";", data).group(0)
	dlink = dlink[7:-2]
	filename = dlink.split('/')[5:]
	say('Downloading: %s' % filename[0])
	downloaded_filename = download(dlink, filename[0])

def hfdl(link, USER=None, PASS=None):
	apilink = 'http://api.hotfile.com/?action=getdirectdownloadlink'
	if USER and PASS:
		conn = urllib.urlopen(apilink + '&username=' + USER + '&password=' + PASS)
		data = conn.read()
		conn.close()
		if "premium required" in data:
			error('A premium account is required to download from hotfile.')
			return
		say('Downloading: %s' % filename)
		downloaded_filename = download(data, filename)

def checkLink(link, USER=None, PASS=None):
	if "rapidshare.com" in link:
		rsdl(link, USER, PASS)
	elif "mediafire.com" in link:
		mfdl(link)
	elif "hotfile.com" in link:
		if USER or PASS:
			hfdl(link, USER, PASS)
		else:
			error('You need to enter a username and password for hotfile')
			return
	else:
		error('Invalid or unsupported link')
		return

def main():
	parser = argparse.ArgumentParser(description='Command-line Python Rapidshare, Mediafire and Hotfile downloader.')
	parser.add_argument('file_url')
	parser.add_argument('--user', '-u')
	parser.add_argument('--password', '-p')
	
	USER = parser.parse_args().user
	PASS = parser.parse_args().password
	file_link = parser.parse_args().file_url

	if ".txt" in file_link and not "http://" in file_link:
		f = open(file_link, 'r')
		if f.read(1) == '\xef':
			f.seek(3)
		file_list = list(f.readlines())
		for item in file_list:
			checkLink(item.strip('\n'), USER, PASS)
	else:
		checkLink(file_link, USER, PASS)

if __name__ == '__main__':
	try:
		main()
	except KeyboardInterrupt:
		error('\nAborted')
		sys.exit(1)