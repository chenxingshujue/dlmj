from things import Room
from things import Player
import common
from hashlib import md5
_rooms = {}
_waiting_rooms = {}


def create():
	room = Room()
	_rooms[room.id] = room
	return room

def get(roomid):
	return _rooms.get(roomid)

def get_or_create_room(player):
	room = None
	if player.roomid != 0:
		room = _rooms.get(player.roomid)
		if room != None:
			return room
	if len(_waiting_rooms) > 0:
		_,room = _waiting_rooms.popitem()
	else:
		room = create()
	room.add_player(player)
	if not room.isfull():
		_waiting_rooms[room.id] = room
		room.check_players()
	else:
		room.start_game()
	return room

def check_room_conditions(player):
	room = rmg.get(player.roomid)
	if player.points < room.enter_points:
		player.sendmessage(s2c.message,0,"not enough points!")
		return False
	return True
