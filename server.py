import asyncio
from threading import Thread
import websockets
import http.server
import socketserver
import json
import roommanager as rmg
from things import Player
from hashlib import md5
from common import *
import logging
# PORT = 80

# Handler = http.server.SimpleHTTPRequestHandler

# with socketserver.TCPServer(("",PORT),Handler) as httpd:
# 	print("serving at port",PORT)
# 	httpd.serve_forever()

print("server starting...")
 


clients = {}
websockets_to_id = {}
cmd_handlers = {}

async def card_server(websocket,path):
	print(f"new client connection at {path}")
	while True:
		try:
			cmd = await websocket.recv()
			print(f" < {cmd}")
			cmd = json.loads(cmd)

			playerid = websockets_to_id.get(websocket)
			if playerid != None:
				player = clients.get(playerid)
				if player != None :
					protolid = player.get_protocol_id()
					if  protolid != None and cmd_handlers[protolid] != None:
						cmd_handlers[protolid](player,cmd.get("data"))
			else:
				login(websocket,cmd)

		except websockets.exceptions.ConnectionClosed as e :
			logout(websocket)
			break
		except Exception as e:
			print(e)
			logging.exception(e)
			break


	
def login(websocket,cmd):
	username = cmd.get("username")
	secretid = cmd.get("secretid") or 0

	playerid = None;

	ret = 0
	col = get_player_info(username)
	if col != None:
		playerid,_,saved_secretid,points = col
		if saved_secretid != secretid :
			ret = 2
		else :
			ret = 0
	else:
		confirm_secretid = cmd.get("confirm_secretid")
		if confirm_secretid == secretid:
			ret = 0
		else:
			ret = 1

	msg = {}
	msg["id"] = s2c.login.value
	msg["ret"] = ret
	msg["secretid"] = secretid
	msg["username"] = username
	if ret == 0:
		player = None;
		if playerid != None:
			player = clients.get(playerid)
		if player == None:	 #new login
			player = create_player(secretid,username,playerid)
			player.websocket = websocket
			clients[player.id] = player
			websockets_to_id[websocket] = player.id
			msg["playerid"] = player.id
			msg["points"] = player.points
			msg = json.dumps(msg)
			print(">",msg)
			messageQueue.put(websocket.send(msg))
			player.askquestion(1)
		else:                #reconnect
			msg["playerid"] = player.id
			msg["points"] = player.points
			msg = json.dumps(msg)
			print(">",msg)
			messageQueue.put(websocket.send(msg))

			player.websocket = websocket
			websockets_to_id[websocket] = player.id
			room = rmg.get(player.roomid)
			if room != None:
				room.on_player_reconnected(player)
			else:
				player.askquestion(1)

	else:
		msg = json.dumps(msg)
		print(">",msg)
		messageQueue.put(websocket.send(msg))





def create_player(secretid,username,playerid):
	points = 1000
	player = Player(playerid)
	player.add_points(points)
	player.secretid = secretid
	player.username = username
	player.online = 1

	if playerid == None:
		player.add_points(points)
		create_player_info(player)

	return player




def logout(websocket):
	print("logout")
	playerid = websockets_to_id.get(websocket)
	if playerid != None:
		del websockets_to_id[websocket]
		player = clients.get(playerid)
		if player != None:
			player.online = 0
			room = rmg.get(player.roomid)
			if room != None:
				room.on_player_disconnect(player)



def on_client_answer(player,data):
	return player.answerquestion(data)

def on_client_handle(player,data):
	return player.handle(data)

def on_client_chat(player,data):
	room = rmg.get(player.roomid)
	if room != None:
		room.on_player_chat(player,data)
	else:
		player.sendmessage(s2c.chat,0,data)


def register_cmds():
	cmd_handlers[c2s.login] = login
	cmd_handlers[c2s.quest] = on_client_answer
	cmd_handlers[c2s.handle] = on_client_handle
	cmd_handlers[c2s.chat] = on_client_chat


register_cmds()
@asyncio.coroutine
def sendmessage():
	while True:
		yield 
		if not messageQueue.empty():
			yield from messageQueue.get()


async def login_robot():
	while True:
		await asyncio.sleep(5)
		rmg.login_robot()


# t = Thread(target=start_loop, args=(new_loop,))
# t.start()
# print('TIME: {}'.format(time.time() - start))

start_server = websockets.serve(card_server,"0.0.0.0",8765)

# async def main():
	# while True:
	# 	await sendmessage()
		# login_robot()

tasks = [
	start_server,
	login_robot(),
	sendmessage()
]
loop.run_until_complete(asyncio.wait(tasks))
# loop.run_until_complete(start_server)
# asyncio.run_coroutine_threadsafe(sendmessage(), loop)
# asyncio.run_coroutine_threadsafe(login_robot(), loop)
loop.run_forever()