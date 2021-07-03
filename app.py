#!/usr/bin/python3
import datetime
import json
import os
import random
import re
import time

from argparse import ArgumentParser
from mgsv_emulator.emulator.client import Client


dir_path = os.path.dirname(os.path.realpath(__file__))

info_list_re = re.compile("I=C=cmn-col-.*?\|")

p = ArgumentParser()
p.add_argument('-d', '--delay', action='store_true')
args = p.parse_args()
if args.delay:
    delay = random.randrange(600, 2400)
    time.sleep(delay)

def save_nukes_data(update_time, nuke_amount, platform):
	f = open("{}.txt".format(platform), "a")
	f.write('{},{}\n'.format(update_time, nuke_amount))
	f.close()

def get_nuke_data(platform):
	f = open("{}.txt".format(platform), 'r').read().split('\n')
	text = ""
	for line in f:
		if line == "":
			continue
		full_date, value = line.split(',')
		date, hours = full_date.split(" ")
		text += "{" + " x: '{}', y: {}, group:'{}'".format(
			date,
			value,
			platform
			) + '},\n'
	return text.rstrip(',')

def get_fob_info(data):
	fob_event_main = ""
	event_id = data['fob_event_task_result_param']['one_event_param'][0]['event_id']
	english_text = list(filter(lambda x: x['language']=='en', data['server_texts']))

	# gross
	if len(str(event_id)) != 2:
		event_id_str = '0' + str(event_id)
	fob_event_main += "<p>Name: " + list(filter(lambda x: x['identifier'] == "mb_fob_event_name_{}".format(event_id_str), english_text ))[0]['text'] + '</p>'
	fob_event_main += "<p>Description: " + list(filter(lambda x: x['identifier'] == "mb_fob_event_info_{}".format(event_id_str), english_text ))[0]['text'].replace('\n',' ') + '</p>'
	fob_event_main += "<p>" + list(filter(lambda x: x['identifier'] == "ranking_evnt_term", english_text ))[0]['text'] + '</p>'

	fob_event_others = ""
	for i in english_text:
		if 'event_name' in i['identifier']:
			if 'event_name_{}'.format(event_id_str) not in i['identifier']:
				fob_event_others += '<p>Name: ' + i['text'] + '</p>'

		if 'event_info' in i['identifier']:
			if 'event_info_{}'.format(event_id_str) not in i['identifier']:
				fob_event_others += '<p>Description: ' + i['text'] + '</p><hr>'

	return (fob_event_main, fob_event_others)


def get_info_list_data(data):
	result = ""
	for i in data['data']['info_list']:
		result += "<p>ID: {}</p>".format(i['info_id'])
		text = info_list_re.sub('',i['mes_body']).replace('\r','')
		text = text.replace('<','').replace('>','').replace('\n','<br>')
		result += "<p>Message: {}</p><hr>\n".format(text)
	return result

def gather_data():
	nuke_amount = {'stm':-1, 'ps3':-1,'ps4':-1}

	steam_client = Client()
	steam_client.login()
	nukes = steam_client.get_nuclear()[0]
	login_info = steam_client.get_login_data()[0]
	info_list = steam_client.get_info_list()[0]

	nuke_amount['stm'] = nukes['data']['info']['num']

	ps3_client = Client(platform='ps3')
#	ps3_client.login()
	ps3_nukes = ps3_client.get_nuclear()[0]
	nuke_amount['ps3'] = ps3_nukes['data']['info']['num']

	ps4_client = Client(platform='ps4')
	ps4_nukes = ps4_client.get_nuclear()[0]
	nuke_amount['ps4'] = ps4_nukes['data']['info']['num']

	update_time = datetime.datetime.utcnow().strftime('%Y-%m-%d %H:00')

	save_nukes_data(update_time, nuke_amount['stm'], 'stm')
	save_nukes_data(update_time, nuke_amount['ps3'], 'ps3')
	save_nukes_data(update_time, nuke_amount['ps4'], 'ps4')
	nuke_data_steam = get_nuke_data('stm')
	nuke_data_ps3 = get_nuke_data('ps3')
	nuke_data_ps4 = get_nuke_data('ps4')

	fob_info = get_fob_info(login_info['data'])
	fob_info_main = fob_info[0]
	fob_info_others = fob_info[1]

	infolist = get_info_list_data(info_list)

	# should use .format of something like that
	template = open(os.path.join(dir_path,'template.html'),'r').read()
	out = template.replace('-nukes_steam-', str(nuke_amount['stm']))
	out = out.replace('-nukes_ps3-', str(nuke_amount['ps3']))
	out = out.replace('-nukes_ps4-', str(nuke_amount['ps4']))
	out = out.replace('-fob_event_main-',str(fob_info_main))
	out = out.replace('-fob_event_others-',str(fob_info_others))
	out = out.replace('-last_nuke_update-',str(update_time))
	out = out.replace('-infolist-',str(infolist))
	out = out.replace('-nuke_data_steam-',nuke_data_steam)
	out = out.replace('-nuke_data_ps3-',nuke_data_ps3)
	out = out.replace('-nuke_data_ps4-',nuke_data_ps4)

	f = open(os.path.join(dir_path,'index.html'),'w')
	f.write(out)
	f.close()

gather_data()



# fob_event_task_list 		# tpp_fob.eng.lng2
# online_challenge_task 	# list of online mission tasks
# server_product_params  	# list of price fixes
