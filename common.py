import pandas as pd
from queue import Queue
import roommanager as rmg
from enum import Enum
import asyncio
class c2s(Enum):
    login  = 1
    quest = 2 
    handle = 3 
    chat = 200 

class s2c(Enum):
    login  = 1
    quest = 2 
    respone_quest = 20
    handle = 3
    respone_handle = 30
    message = 100
    chat = 200

class Color:
	red ="FF0000"
	greed ="00FF00"
	white ="FFFFFF"
	blue ="6464FF"
	orange ="FFA500"

messageQueue = Queue()
loop = asyncio.get_event_loop()


discard_words = "<font color='#6464FF'>your turn to discard</font>"
try_discard_words = "<font color='#6464FF'>your turn to discard,or pass(0)</font>"

questions = pd.read_csv('questions.csv',index_col =0)



def color_html(s,c):
    return f'<font color="#{c}">{s}</font>'

def toint(answer):
	try:
		answer = int(answer)
	except Exception as e:
		answer =None

	return answer

def on_room_choose(player,questid,answer):
	answer = toint(answer)
	msg = None
	if rmg.check_room_conditions(player) :
		if answer == 1 :
			return player.quick_start()
		elif answer == 2 :
			return player.askquestion(5)
		elif answer == 3 :
			return rmg.create_room(player)
		else:
			msg = "wrong answer,please try again!"
			return player.askquestion_with_msg(msg,questid)


def on_room_waiting(player,questid,answer):
	answer = toint(answer)
	if answer == 0:
		player.leave_room()
		player.askquestion(1)
	else:
		msg = "invalid input!"
		player.sendmessage(s2c.message,0,msg)
		room = rmg.get(player.roomid)
		if room != None:
			room.check_players(player.id)

def onlandlord_choose(player,questid,answer):
	answer = toint(answer)
	room  = rmg.get(player.roomid)
	room.roll_landlord(answer == 1)

def on_game_continue(player,questid,answer):
	answer = toint(answer)
	if answer == 2:
		player.leave_room()
		player.askquestion(1)
	else:
		player.ready = True
		room =rmg.get(player.roomid)
		if rmg.check_room_conditions(player) :
			if not room.isfull():
				room.check_players()
			else:
				room.start_game()
		else:
			player.leave_room()
			player.askquestion(1)
			

def on_room_join(player,questid,answer):
	numbers = toint(answer)
	if numbers != None :
		if numbers == 0:
			player.askquestion(1)
		else:
			room = rmg.get(numbers)
			print("on_room_join",numbers)
			if room != None:
				rmg.add_player(room,player)
			else:
				msg = "room not exsits,try again!"
				return player.askquestion_with_msg(msg,questid)






answer_handlers = {}
answer_handlers[1] = on_room_choose
answer_handlers[2] = on_room_waiting
answer_handlers[3] = onlandlord_choose
answer_handlers[4] = on_game_continue
answer_handlers[5] = on_room_join

def answer_question(player,questid,answer):
	handler = answer_handlers.get(questid)
	if handler != None:
		return handler(player,questid,answer)


def str2numbers(s):
	if type(s) != str or s == ' ':
		return 
	numbers = []
	for word in s:
		try:
			numbers.append(int(word))
		except Exception as e:
			return None
	return numbers


import pymysql

# 连接database
mysql_conn = pymysql.connect(
    host="127.0.0.1",
    user="root",password="Chenxing0320!",
    database = "shaoyou",
    charset = 'utf8')

print("database connected")
cursor = mysql_conn.cursor() 
get_max_id = "select max(id) from players;"
cursor.execute(get_max_id)
max_player_id = cursor.fetchone()[0] or 0
print("max_player_id",max_player_id)

def get_player_info(username):
	sql = f"select * from players where username ='{username}';"
	cursor.execute(sql)
	col = cursor.fetchone()
	return col


def get_playerid_in_db():
	sql = "select last_insert_id();"
	cursor.execute(sql)
	col = cursor.fetchone()
	print("last_insert_id",col)

def create_player_info(player):
	sql = f"insert into players values('{player.id}','{player.username}','{player.secretid}','{player.points}','{player.freepoints}');"
	cursor.execute(sql)
	mysql_conn.commit()

def save_player_info(player):
	sql = f"update players set points = '{pl.points}' , freepoints = '{pl.freepoints}' where id = '{player.id}';"
	cursor.execute(sql)
	mysql_conn.commit()

