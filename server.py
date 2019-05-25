import asyncio
import websockets
import http.server
import socketserver
import json
import roommanager as rmg
from things import Player
from hashlib import md5
from common import c2s
from common import s2c
from common import messageQueue
# PORT = 80

# Handler = http.server.SimpleHTTPRequestHandler

# with socketserver.TCPServer(("",PORT),Handler) as httpd:
# 	print("serving at port",PORT)
# 	httpd.serve_forever()

import pymysql

print("server starting...")
 
# 连接database
mysql_conn = pymysql.connect(
    host="127.0.0.1",
    user="root",password="Chenxing11",
    database = "shaoyou",
    charset = 'utf8')

print("database connected")
cursor = mysql_conn.cursor() 
get_max_id = "select max(id) from players;"
cursor.execute(get_max_id)
Player._global_id_ = cursor.fetchone()[0] or 0
print("max_player_id",Player._global_id_)

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
	sql = f"select * from players where username ='{username}';"
	cursor.execute(sql)

	playerid = None;

	ret = 0
	col = cursor.fetchone()
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




def get_playerid_in_db():
	sql = "select last_insert_id();"
	cursor.execute(sql)
	col = cursor.fetchone()
	print("last_insert_id",col)

def create_player(secretid,username,playerid):
	points = 1000
	player = Player(playerid)
	player.add_points(points)
	player.secretid = secretid
	player.username = username
	player.online = 1

	if playerid == None:
		sql = f"insert into players values('{player.id}','{username}','{secretid}','{points}');"
		player.add_points(points)
		cursor.execute(sql)
		mysql_conn.commit()
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