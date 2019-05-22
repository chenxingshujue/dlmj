import asyncio
import websockets
import http.server
import socketserver
import json
import roommanager
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

clients = {}
websockets_to_secretid = {}
cmd_handlers = {}

async def card_server(websocket,path):
	print(path)
	while True:
		try:
			cmd = await websocket.recv()
			print(f" < {cmd}")
			cmd = json.loads(cmd)
			id = cmd.get("id")
			if  id != None and type(id) == "int" :
				id = int(cmd.id)
			if  id > 0 and cmd_handlers[id] != None:
				cmd_handlers[id](websocket,cmd)
		except websockets.exceptions.ConnectionClosed as e :
			logout(websocket)
			break

		while not messageQueue.empty():
			await messageQueue.get()
	
def login(websocket,cmd):
	secretid = cmd.get("secretid") or 0
	websockets_to_secretid[websocket] = secretid
	if clients.get(secretid) != None:
		return
	player = Player()
	player.nickname = cmd.get("username")
	player.secretid = cmd.get("secretid")
	player.online = 1
	player.websocket = websocket
	clients[player.secretid ] = player

	msg = {}
	msg["id"] = s2c.login.value
	msg["ret"] = 0
	msg["secretid"] = player.secretid
	msg["playerid"] = player.id
	msg = json.dumps(msg)
	print(">",msg)
	messageQueue.put(websocket.send(msg))
	player.askquestion(1)

def logout(websocket):
	secretid = websockets_to_secretid.get(websocket)
	if secretid != None and clients.get(secretid) != None:
		clients.get(secretid).online = 0
		del websockets_to_secretid[websocket]


def on_client_answer(websocket,cmd):
	secretid = websockets_to_secretid.get(websocket)
	player = clients.get(secretid)
	if player != None :
		return player.answerquestion(cmd.get("data"))

def on_client_handle(websocket,cmd):
	secretid = websockets_to_secretid.get(websocket)
	player = clients.get(secretid)
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