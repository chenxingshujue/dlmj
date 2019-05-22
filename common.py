import pandas as pd
from queue import Queue
import roommanager as rmg
from enum import Enum
class c2s(Enum):
    login  = 1
    quest = 2 
    handle = 3 

class s2c(Enum):
    login  = 1
    quest = 2 
    respone_quest = 20
    handle = 3
    respone_handle = 30
    message = 100

messageQueue = Queue()



questions = pd.read_csv('questions.csv',index_col =0)

def toint(answer):
	try:
		answer = int(answer)
	except Exception as e:
		answer =None

	return answer

def on_room_choose(player,questid,answer):
	answer = toint(answer)
	if answer == 1 :
		return player.quick_start()
	elif answer == 2 :
		msg = "Please Type the target room Number!"
		return player.sendmessage(s2c.message,0,msg)
	elif answer == 3 :
		msg = "Please Setup your room password!"
		return player.sendmessage(s2c.message,0,msg)
	msg = "wrong answer,please try again!"
	return player.sendmessage(s2c.message,1,msg)

def on_room_waiting(player,questid,answer):
	answer = toint(answer)
	if answer == 1:
		player.leave_room()
		player.askquestion(1)
	else:
		msg = "invalid input!"
		return player.sendmessage(s2c.message,1,msg)

def onlandlord_choose(player,questid,answer):
	answer = toint(answer)
	room  = rmg.get_or_create_room(player)
	room.roll_landlord(answer == 1)

def on_game_continue(player,questid,answer):
	answer = toint(answer)
	if answer == 2:
		player.leave_room()
		player.askquestion(1)
	else:
		player.ready = True
		room = rmg.get_or_create_room(player)
		room.start_game()



answer_handlers = {}
answer_handlers[1] = on_room_choose
answer_handlers[2] = on_room_waiting
answer_handlers[3] = onlandlord_choose
answer_handlers[4] = on_game_continue

def answer_question(player,questid,answer):
	handler = answer_handlers.get(questid)
	if handler != None:
		return handler(player,questid,answer)
