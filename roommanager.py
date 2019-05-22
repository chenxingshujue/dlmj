from things import Room
from things import Player
from hashlib import md5
_rooms = {}
_waiting_rooms = {}


def create():
	room = Room()
	_rooms[room.id] = room
	return room


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

