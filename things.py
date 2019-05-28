import asyncio
import common
import json
from common import questions
from common import s2c
from common import messageQueue
import roommanager as rmg
import cardsmanager as cmg
from cardsmanager import Rule
import random
correct_answer_key = "a0"
_CARDS_COUNT_ON_START = 17
class Room(object):
	"""docstring for Room"""
	_max_players_count_ = 2
	_global_id_  = 0
	# def __new__(cls):
	# 	print("__new__", cls == Room)
	# 	return super(Room,cls).__new__(cls)

	# def __call__(self):
	# 	print("__call__", self,super(Room,self))

	def __init__(self):
		super(Room,self).__init__()
		Room._global_id_  += 1
		self._id = Room._global_id_
		self._players = {}
		self._cards = None
		self._landlord_pos = -1
		self._pre_landlord_pos = -1
		self._players_pos = {}
		self._cur_pos = 1
		self._start_pos = -1
		self._start_take = False
		self._last_rule = None
		self._last_discard_pos = -1
		self._round = 0
		self._multiple = 1
		self.enter_points = 100
		self.base_points = 50

	@property
	def id(self):
		return self._id
	@property
	def cur_pos(self):
		return self._cur_pos
	

	def add_player(self,player):
		if self.isfull():
			return
		self._players[player.id] = player
		for x in range(1,Room._max_players_count_+1):
			if self._players_pos.get(x) == None:
				self._players_pos[x] = player
				player.room_pos = x
				break
		player.roomid = self.id
		for _,pl in self._players.items():
			msg = "%s enter room %s at pos %s points %s"%(player.nickname,self._id,player.room_pos,player.points)
			pl.sendmessage(s2c.message,0,msg)

	def remove_player(self,player):
		del self._players[player.id]
		del self._players_pos[player.room_pos]
		player.roomid = 0
		player.room_pos = -1
		for _,pl in self._players.items():
			msg = "%s leave room %s"%(pl.nickname,self._id)
			pl.sendmessage(s2c.message,0,msg)

		self.check_players()

	def isfull(self):
		return len(self._players) >= Room._max_players_count_

	def start_game(self):
		for _,pl in self._players.items():
			if pl.ready == False:
				return False
		self.shuffle_cards()
		for _,pl in self._players.items():
			pl.add_points(-self.enter_points)
			msg = "game start you got following cards:\n%s"%(cmg.tostr(pl.cards_list))
			pl.sendmessage(s2c.message,0,msg)
		self.roll_landlord(False)

	def roll_landlord(self,takeornot):
		if self._start_pos < 0 :
			self._cur_pos = random.choice(range(Room._max_players_count_)) + 1
			self._pre_landlord_pos = self._cur_pos
			self._start_pos = self._cur_pos
			print("roll_landlord",self._start_pos,self._cur_pos)
			player = self._players_pos[self._cur_pos]
			player.askquestion(3)
		else:
			print("roll_landlord1",takeornot,self._start_pos,self._cur_pos)
			player = self._players_pos[self._cur_pos]
			if takeornot:
				self._multiple *= 2
				msg = 'brave !,%s run for landlord! points x%s' %(player.nickname,self._multiple)
			else:
				msg = '%s give up landlord!' %(player.nickname)
			for _,pl in self._players.items():
				pl.sendmessage(s2c.message,0,msg)

			
			if takeornot :
				self._pre_landlord_pos = self._cur_pos
				if self._cur_pos == self._start_pos:
					self._start_take = True

			# print("roll_landlord2",self.get_next_pos(),self._pre_landlord_pos,self._start_pos)
			if self.get_next_pos() == self._start_pos :
				if self._pre_landlord_pos < 0 or self._pre_landlord_pos == self._start_pos :
					self._landlord_pos = self._start_pos
				elif self._start_take == False:
					self._landlord_pos = self._pre_landlord_pos

			if self._cur_pos == self._start_pos and self._round == 1:
				if takeornot:
					self._landlord_pos = self._start_pos
				else:
					self._landlord_pos = self._pre_landlord_pos

			if self._landlord_pos >= 0:
				self._pre_landlord_pos = -1
				self._start_pos = -1

				player = self._players_pos[self._landlord_pos]
				self.assign_left_cards()
				for _,pl in self._players.items():
					msg = "%s become the landlord!"%(player.nickname)
					pl.sendmessage(s2c.message,0,msg)

				self.roll_discard(self._landlord_pos)
			else:
				player = self.next_pos()
				player.askquestion(3)
				return


	def next_pos(self):
		self._cur_pos = self.get_next_pos()
		if self._cur_pos == self._start_pos:
			self._round += 1
		return self._players_pos[self._cur_pos]

	def get_next_pos(self):
		next_pos = self._cur_pos + 1
		if next_pos > Room._max_players_count_:
			next_pos = 1
		return next_pos


	def check_players(self,playerid=None):
		more =  Room._max_players_count_ - len(self._players)
		if more > 0:
			for _,pl in self._players.items():
				if playerid != None:
					if pl.id == playerid :
						pl.askquestion(2,more)
				else:
					pl.askquestion(2,more)

	def on_player_disconnect(self,player):
		for _,pl in self._players.items():
			if pl.id != player.id :
				pl.sendmessage(s2c.message,0,"%s lose connection"%(player.nickname))

	def on_player_reconnected(self,player):
		for _,pl in self._players.items():
			if pl.id == player.id :
				if player.room_pos ==  player.room_pos:
					if self._last_discard_pos < 0 or self._last_discard_pos == pl.room_pos:
						player.showcards("your turn to discard",s2c.handle)
					else:
						player.showcards("your turn to discard,or pass(0)",s2c.handle)
				else:
					player.showcards("waiting for %s to discard ..."%(player.nickname))
			else:
				pl.sendmessage(s2c.message,0,"%s reconnected"%(player.nickname))



	def shuffle_cards(self):
		self._cards = cmg.CARDS.copy()
		for _,pl in self._players.items():
			self._cards,cards = cmg.sample(self._cards,_CARDS_COUNT_ON_START)
			pl.add_cards(cards)

	def assign_left_cards(self):
		player = self._players_pos[self._landlord_pos]
		player.add_cards(self._cards)
		self.cards = []

	def roll_discard(self,pos=None):
		player = None
		if pos == None:
			player = self.next_pos()
		else:
			self._cur_pos = pos
			player = self._players_pos[self._cur_pos]

		for _,pl in self._players.items():
			if pl.room_pos ==  player.room_pos:
				if self._last_discard_pos < 0 or self._last_discard_pos == pl.room_pos:
					pl.showcards("your turn to discard",s2c.handle)
				else:
					pl.showcards("your turn to discard,or pass(0)",s2c.handle)
			else:
				pl.showcards("waiting for %s to discard ..."%(player.nickname))
				
		

	def try_discards(self,player,rule):
		if rule == None:
			for _,pl in self._players.items():
				msg = "%s passed!"%(player.nickname)
				pl.sendmessage(s2c.message,0,msg)
			self.roll_discard()
			return
		valid = False
		if self._last_rule == None or self._last_discard_pos == player.room_pos:
			valid = True
		elif self._last_rule != None:
			if rule.fit(self._last_rule):
				valid = rule > self._last_rule
				if not valid:
					print("error fit ",rule.rule,rule.value,self._last_rule.rule,self._last_rule.value)
			else:
				player.showcards("can't do that,try again!",s2c.handle)
				return
		if valid :
			self._last_rule = rule
			self._last_discard_pos = player.room_pos
			player.discards(rule)
			if len(player.cards_list) == 0:
				self.endgame(player)
			else:
				for _,pl in self._players.items():
					msg = "%s discard %s"%(player.nickname,cmg.tostr(rule.cards))
					pl.sendmessage(s2c.message,0,msg)

				self.roll_discard()
		else:
			player.showcards("too small, try again!",s2c.handle)

	def endgame(self,winner):
		self._cards = None
		self._landlord_pos = -1
		self._pre_landlord_pos = -1
		self._cur_pos = 0
		self._start_pos = -1
		self._start_take = False
		self._last_rule = None
		self._last_discard_pos = -1
		self._round = 0
		msg = "farmers"
		landlord_win = -1
		if winner.room_pos == self._landlord_pos:
			landlord_win = 1
			msg = "landlord"
		for _,pl in self._players.items():
			pl.ready = False
			if pl.room_pos == self._landlord_pos:
				pl.add_points(self.base_points * self._multiple * landlord_win * (Room._max_players_count_ - 1))
			else:
				pl.add_points(self.base_points * self._multiple * (-landlord_win))
				
			pl.askquestion(4,msg,pl.points)




class Player(object):
	"""docstring for Player"""
	def __init__(self,_id):
		super(Player, self).__init__()
		if _id == None:
			common.max_player_id += 1
			self._id = common.max_player_id
		else:
			self._id = _id
		self._username = 'player'
		self.secretid = 0
		self._online = 0
		self.websocket = None
		self._questid = 0
		self._roomid = 0
		self.room_pos = -1
		self._cards_flat = None
		self._cards_list = None
		self._points = 0
		self.ready = True

		
	@property
	def id(self):
		return self._id	
	@property
	def nickname(self):
		return  "%s(%s)"%(self._username,self.room_pos)

	@property
	def username(self):
		return self._username
	@username.setter
	def username(self,value):
		self._username = value

	@property
	def secretid(self):
		return self._secretid
	@secretid.setter
	def secretid(self,value):
		self._secretid = value
	@property
	def online(self):
		return self._online
	@online.setter
	def online(self,value):
		self._online = value

	@property
	def questid(self):
		return self._questid
	@questid.setter
	def questid(self,value):
		print("questid",self._questid,value)
		self._questid = value

	@property
	def roomid(self):
		return self._roomid
	@roomid.setter
	def roomid(self,value):
		self._roomid = value

	@property
	def cards_list(self):
		return self._cards_list

	@property
	def points(self):
		return self._points
	
	def add_points(self,points):
		self._points = self._points + points;
		if self._points < 0:
			self._points = 0
	
	def add_cards(self,cards):
		if self._cards_list == None:
			self._cards_list = cards
		else:
			self._cards_list.extend(cards)

		self._cards_flat = cmg.flat_cards(self._cards_list)
		self._cards_list.sort(reverse=True)


	def discards(self,rule):
		if self._cards_list == None:
			return
		else:
			cards = []
			self._cards_flat = {}
			rule_cards_flat = rule.flatcards.copy()
			for card in self._cards_list:
				count = rule_cards_flat.get(card) or 0
				if count > 0:
					rule_cards_flat[card] = count-1
					continue
				else:
					cards.append(card)
					if self._cards_flat.get(card) == None:
						self._cards_flat[card] = 1
					else:
						self._cards_flat[card] += 1 
				
			self._cards_list = cards
			self._cards_list.sort(reverse=True)

	def validate(self,rule):
		if rule.count == 0:
			return False
		if rule.count > len(self.cards_list):
			return False
		for card,count in rule.flatcards.items():
				got_count = self._cards_flat.get(card) or 0
				if count > got_count:
					return False
		return True

	def sendmessage(self,e_s2c,ret,data):
		msg = {}
		msg["id"] = e_s2c.value
		msg["ret"] = ret
		msg["data"] = data
		msg["websocket"] = id(self.websocket)
		msg = json.dumps(msg)
		print(">",msg)
		messageQueue.put(self.websocket.send(msg))

	def showcards(self,msg,e_s2c = None):
		msg = msg or ''
		msg = "%s\n%s"%(msg,cmg.tostr(self.cards_list))
		if e_s2c == None :
			self.sendmessage(s2c.message,0,msg)
		else:
			self.sendmessage(e_s2c,0,msg)

	def askquestion_with_msg(self,msg,questid,*params):
		self._questid = questid
		print("askquestion_with_msg",questid,self._questid,params)
		data = questions.at[questid,"quest"]
		if len(params) > 0 :
			data = data %(params)
		if data != None:
			if msg != None:
				data = msg + "\n" + data
			self.sendmessage(s2c.quest,0,data)


	def askquestion(self,questid,*params):
		self.askquestion_with_msg(None,questid,*params)

	def answerquestion(self,answer):
		print("answerquestion",self._questid,answer)
		if self._questid == None:
			return
		questid = self.questid
		self.questid = None
		common.answer_question(self,questid,answer)

	def quick_start(self):
		room = rmg.get_or_create_room(self)

	def leave_room(self):
		room = rmg.get(self.roomid)
		room.remove_player(self)

	def handle(self,data):
		data = data.strip()
		room = rmg.get(self.roomid)
		if room.cur_pos != self.room_pos:
			print("error handle,not your turn")
			return
		if len(data[0]) > 0 and data[0] == '0':
			room.try_discards(self,None)
			return

		discards = []
		for word in data:
			card = cmg.str2card(word)
			if card != None:
				discards.append(card)

		valid = cmg.validate(discards)
		rule = None
		if valid:
			rule = Rule(discards,True)
			if rule != None:
				valid = self.validate(rule)

		if valid :
			room.try_discards(self,rule)
		else:
			self.showcards("wrong cards,try again!",s2c.handle)	

	def save_to_db():
		common.save_player_info(player)