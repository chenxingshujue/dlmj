import asyncio
import websockets
import http.server
import socketserver
import json
import roommanager as rmg
from things import Player
from hashlib import md5
from common import *
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
	print(path)
	while True:
		try:
			cmd = await websocket.recv()
			print(f" < {cmd}")
			cmd = json.loads(cmd)
			protolid = cmd.get("id")
			if  protolid != None and type(protolid) == int and cmd_handlers[protolid] != None:
				cmd_handlers[protolid](websocket,cmd)
		except websockets.exceptions.ConnectionClosed as e :
			logout(websocket)
			break

		while not messageQueue.empty():
			await messageQueue.get()
	
def login(websocket,cmd):
	username = cmd.get("username")
	secretid = cmd.get("secretid") or 0

	playerid = None;

	ret = 0
	col = get_player_info(username)
	if col != None:
		playerid,_,secretid,points = col
		saved_secretid = secretid
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
	playerid = websockets_to_id.get(websocket)
	del websockets_to_id[websocket]
	if playerid != None:
		player = clients.get(playerid)
		if player != None:
			player.online = 0

		room = rmg.get(player.roomid)
		if room != None:
			room.on_player_disconnect(player)


def on_client_answer(websocket,cmd):
	playerid = websockets_to_id.get(websocket)
	if playerid != None:
		player = clients.get(playerid)
		if player != None :
			return player.answerquestion(cmd.get("data"))

def on_client_handle(websocket,cmd):
	playerid = websockets_to_id.get(websocket)
	if playerid != None:
		player = clients.get(playerid)
		if player != None :
			return player.handle(cmd.get("data"))



def register_cmds():
	cmd_handlers[c2s.login.value] = login
	cmd_handlers[c2s.quest.value] = on_client_answer
	cmd_handlers[c2s.handle.value] = on_client_handle


register_cmds()


start_server = websockets.serve(card_server,"0.0.0.0",8765)
loop = asyncio.get_event_loop()
loop.run_until_complete(start_server)
loop.run_forever()