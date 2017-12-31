#!/usr/bin/env python3
#
# pymm is a python port of mediamicroservices
#
# this is a set of functions used by pymm scripts
#

import json
import subprocess
import os
import sys
import configparser
from datetime import date
import time
from ffmpy import FFprobe, FFmpeg

################################################################
# READ config.ini 
pymmDirectory = os.path.dirname(os.path.abspath(__file__))
configPath = os.path.join(pymmDirectory,'config','config.ini') 
if not os.path.isfile(configPath):
	print('''
		CONFIGURATION PROBLEM:\n
		YOU HAVE NOT YET SET CONFIG.INI OR IT IS MISSING.\n
		RUN pymmconfig.py TO CREATE CONFIG.INI AND CHOOSE YOUR DESIRED SETTINGS.\n
		NOW EXITING.
		''')
	sys.exit(1)

	# open(configPath,'x')
	# with open(configPath,'w+') as config:
	# 	config.write('''
	# 		[paths]\routdir_ingestfile:\raip_storage:\rresourcespace_deliver:\rpymm_scriptdir:
	# 		\r\r[database settings]\rpymm_db:\rpymm_db_user_profile:\rpymm_db_name:
	# 		\r\r[logging]\rpymm_log_dir:
	# 		''')
globalConfig = configparser.SafeConfigParser()
globalConfig.read(configPath)

# check for the existence of required output paths
requiredPaths = {'outdir_ingestfile':'the ingestfile output path','aip_storage':'the AIP storage path',
				'resourcespace_deliver':'the resourcespace output path'}
missingPaths = 0
for path in requiredPaths.items():
	if not os.path.isdir(globalConfig['paths'][path[0]]):
		missingPaths += 1
		print('''CONFIGURATION PROBLEM:\n
			You have not yet set a directory for "+path[0]+". Please run config.py,\n
			edit the config file directly,\n
			or use '--"+path[0]+"' to set "+path[1]
			''')
if missingPaths > 0:
	print("You are missing some required file paths and we have to quit. Sorry.")
	sys.exit()
################################################################

today = str(date.today())
now = time.strftime("%Y-%m-%d_%H:%M:%S")
pymmLogPath =  globalConfig['logging']['pymm_log_dir']+'/pymm_log.txt'

def check_pymm_log_exists():
	if not os.path.isfile(pymmLogPath):
		print('wait i need to make a logfile')
		open(pymmLogPath,'x')
		with open(pymmLogPath,'w+') as pymmLog:
			pymmLog.write(
				((("#"*75)+'\n')*2)+((' ')*4)+'THIS IS THE LOG FOR PYMEDIAMICROSERVICES'
				'\n\n'+((' ')*4)+'THIS COPY WAS STARTED ON '+today+'\n'+((("#"*75)+'\n')*2)+'\n'
				)
	else:
		return True

def ingest_log(ingestLogPath,mediaID,filename,operator,message,status):
	if message == 'start':
		message = 'onwards and upwards'
		status = 'STARTING TO INGEST '+filename
		startToday = ('#'*50)+'\r\r'+str(date.today())
	with open(ingestLogPath,'a+') as ingestLog:
		ingestLog.write(today+' '+status+'  Filename: '+filename+'  mediaID: '+mediaID+'  operator: '+operator+'  MESSAGE: '+message+'\n')
		# LOG SOME SHIT

def pymm_log(filename,mediaID,operator,message,status):
	# mm log content = echo $(_get_iso8601)", $(basename "${0}"), ${STATUS}, ${OP}, ${MEDIAID}, ${NOTE}" >> "${MMLOGFILE}"
	check_pymm_log_exists()
	with open(pymmLogPath,'a') as log:
		if status == 'STARTING':
			prefix = ('&'*50)+'\n\n'
			suffix = '\n'
		elif status == 'ENDING' or status == 'ABORTING':
			prefix = ''
			suffix = '\n\n'+('#'*50)
		else:
			prefix = ''
			suffix = '\n'
		log.write(prefix+today+' '+'Filename: '+filename+'  mediaID: '+mediaID+'  operator: '+operator+'  MESSAGE: '+message+' STATUS: '+status+suffix+'\n')

# def cleanup():
# 	status = 'ABORTING'
# 	pymm_log(mediaID,status,"Something went wrong and the process was aborted.")
# 	exit()

def is_video(inputFile):
	# THIS WILL RETURN TRUE IF FILE IS VIDEO BECAUSE
	# YOU ARE TELLING FFPROBE TO LOOK FOR VIDEO STREAM
	# WITH INDEX=0, AND IF v:0 DOES NOT EXIST,
	# ISPO FACTO, YOU DON'T HAVE A RECOGNIZED VIDEO FILE.
	ffprobe = FFprobe(
	inputs={inputFile:'-v error -print_format json -show_streams -select_streams v:0'}
	)
	FR = ffprobe.run(stdout=subprocess.PIPE)
	output = json.loads(FR[0].decode('utf-8'))
	try:
		indexValue = output['streams'][0]['index']
		if indexValue == 0:
			return True
	except:
		return False

def is_audio(inputFile):
	print('¿maybe this is an audio file?')
	# DO THE SAME AS ABOVE BUT '-select_streams a:0'
	# ... HOPEFULLY IF v:0 DOESN'T EXIST BUT a:0 DOES,
	# YOU HAVE AN AUDIO FILE ON YOUR HANDS. WILL HAVE
	# TO CONFIRM... COULD THIS RETURN TRUE IF v:0 IS BROKEN/CORRUPT?
	ffprobe = FFprobe(
	inputs={inputFile:'-v error -print_format json -show_streams -select_streams a:0'}
	)
	FR = ffprobe.run(stdout=subprocess.PIPE)
	output = json.loads(FR[0].decode('utf-8'))
	indexValue = output['streams'][0]['index']
	try:
		if indexValue == 0:
			print("This appears to be an audio file!")
			return True
	except:
		print("THIS DOESN'T SMELL LIKE AN AUDIO FILE EITHER")
		return False

def phase_check(inputFile):
	# THE FFPROBE/FFMPEG DOCUMENTATION IS SO RIDICULOUS. I CAN'T GET
	# THE MM COMMAND TO FUNCTION AS EXPECTED USING FFMPY,
	# BUT THIS PRINTS THE LAVFI.APHASEMETER.PHASE VALUE PLUS 'PTS_TIME' VALUE:
	#
	# [Parsed_ametadata_1 @ 0x7fd720d01dc0] frame:128  pts:131072  pts_time:2.97215
	# [Parsed_ametadata_1 @ 0x7fd720d01dc0] lavfi.aphasemeter.phase=-0.634070
	# 
	# GOING TO HAVE TO RETURN TO THIS ONE LATER.
	ffpmpeg = FFmpeg(
		inputs={'''
		/path/to/file':'-af aphasemeter=video=0,ametadata=print:key=lavfi.aphasemeter.phase -f null -'
		'''
		}
		)
	

