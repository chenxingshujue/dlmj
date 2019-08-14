import asyncio
import common
import json
from common import *
import roommanager as rmg
import cardsmanager as cmg
from cardsmanager import Rule
from cardsmanager import pattern
import random
correct_answer_key = "a0"
_CARDS_COUNT_ON_START = 17
class Room(object):
	"""docstring for Room"""
	_max_players_count_ = 3
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
		self._status = 0
		self.passwords = None

	@property
	def id(self):
		return self._id
	@property
	def cur_pos(self):
		return self._cur_pos
	@property
	def cur_player(self):
		return self._players_pos[self._cur_pos]
	@property
	def last_discard_player(self):
		return self._players_pos[self._last_discard_pos]
	

	@property
	def last_rule(self):
		return self._last_rule
	
	

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
		for _,pl in self._players.items():
			msg = "%s leave room %s"%(player.nickname,self._id)
			pl.sendmessage(s2c.message,0,msg)

		print("remove_player",player.room_pos)
		player.roomid = 0
		player.room_pos = -1
		self.check_players()

	def isfull(self):
		return len(self._players) >= Room._max_players_count_

	def isempty(self):
		return len(self._players) == 0

	def stillneed(self):
		return Room._max_players_count_ - len(self._players)


	def start_game(self):
		for _,pl in self._players.items():
			if pl.ready == False:
				return False
		self._status = 1
		self.shuffle_cards()
		for _,pl in self._players.items():
			pl.add_points(-self.enter_points)
			msg = "game start you got following cards:\n%s"%(cmg.tostr(pl.cards_list))
			pl.sendmessage(s2c.message,0,msg)
		self.roll_landlord(False)

	def ask_landlord(self,player):
		for _,pl in self._players.items():
			if player.id == pl.id :
				player.askquestion(3)
			else:
				msg = "waiting for %s in landlord race"%(player.nickname)
				pl.sendmessage(s2c.message,0,msg)

		

	def roll_landlord(self,takeornot):
		if self._start_pos < 0 :
			self._cur_pos = random.choice(range(Room._max_players_count_)) + 1
			self._pre_landlord_pos = self._cur_pos
			self._start_pos = self._cur_pos
			print("roll_landlord",self._start_pos,self._cur_pos)
			player = self._players_pos[self._cur_pos]
			self.ask_landlord(player)
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
				self.ask_landlord(player)
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
				if not pl.ready:
					continue
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
		if self._status > 0 :
			for _,pl in self._players.items():
				pl.sendmessage(s2c.message,0,"%s reconnected to room %s"%(player.nickname,self.id))
				if pl.id == player.id :
					if self._status > 1:
						if player.room_pos ==  player.room_pos:
							if self._last_discard_pos < 0 or self._last_discard_pos == pl.room_pos:
								player.showcards(discard_words,s2c.handle)
							else:
								player.show_last_discards()
								player.showcards(try_discard_words,s2c.handle)
						else:
							player.showcards("waiting for %s to discard ..."%(player.nickname))
					else:
						if player.room_pos ==  player.room_pos:
							player.showcards("your cards:")
							player.askquestion(3)
						else:
							player.showcards("waiting for %s in landlord race"%(player.nickname))

		else:
			self.check_players()

	def on_player_chat(self,player,msg):
		for _,pl in self._players.items():
			pl.sendmessage(s2c.chat,0,"%s say: %s"%(player.nickname,msg))



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
		self._status = 2
		player = None
		if pos == None:
			player = self.next_pos()
		else:
			self._cur_pos = pos
			player = self._players_pos[self._cur_pos]

		for _,pl in self._players.items():
			if pl.room_pos ==  player.room_pos:
				if self._last_discard_pos < 0 or self._last_discard_pos == pl.room_pos:
					pl.showcards(discard_words,s2c.handle)
				else:
					pl.showcards(try_discard_words,s2c.handle)
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
					print("error fit ",rule.rule_type,rule.value,self._last_rule.rule_type,self._last_rule.value)
			else:
				player.showcards("can't do that,try again!",s2c.handle)
				return
		if valid :
			self.discards(player,rule)
		else:
			player.showcards("too small, try again!",s2c.handle)

	def discards(self,player,rule):
		self._last_rule = rule
		self._last_discard_pos = player.room_pos
		player.discards(rule)
		if len(player.cards_list) == 0:
			self.endgame(player)
		else:
			for _,pl in self._players.items():
				pl.show_last_discards()
			self.roll_discard()


	def endgame(self,winner):
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

		self._cards = None
		self._landlord_pos = -1
		self._pre_landlord_pos = -1
		self._cur_pos = 0
		self._start_pos = -1
		self._start_take = False
		self._last_rule = None
		self._last_discard_pos = -1
		self._round = 0
		self._status = 0



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
		self._questid = None
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
		if self.cards_list == None:
			return
		msg = msg or ''
		msg = "%s\n%s"%(msg,cmg.tostr(self.cards_list))
		if e_s2c == None :
			self.sendmessage(s2c.message,0,msg)
		else:
			self.sendmessage(e_s2c,0,msg)
	
	def show_last_discards(self):
 		room = rmg.get(self.roomid)
 		if room != None and room.last_rule != None:
 			msg = "%s discard %s"%(room.last_discard_player.nickname,cmg.tostr(room.last_rule.cards))
 			self.sendmessage(s2c.message,0,msg)


	def askquestion_with_msg(self,msg,questid,*params):
		print("askquestion_with_msg",questid,self.questid,params)
		self.questid = questid
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
		if self.questid == None:
			return
		questid = self.questid
		self.questid = None
		common.answer_question(self,questid,answer)

	def quick_start(self):
		room = rmg.get_or_create_room(self)

	def leave_room(self):
		rmg.remove_player(self)

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
			valid = rule.rule_type != None
			if valid:
				valid = self.validate(rule)

		if valid :
			room.try_discards(self,rule)
		else:
			self.showcards("wrong cards,try again!",s2c.handle)	

	def save_to_db(self):
		common.save_player_info(self)


	def get_protocol_id(self):
		if self._questid != None:
			return c2s.quest
		if rmg.is_active_player(self):
			return c2s.handle
		return c2s.chat

class Robot(Player):


	def save_to_db(self):
		print("save robot")

	def sendmessage(self,e_s2c,ret,data):
		pass
		# print("sendmessage robot",data)

	def askquestion_with_msg(self,msg,questid,*params):
		print("askquestion_with_msg robot",msg,questid,*params)
		if questid == None:
			return
		if questid == 3 or questid == 4:
			self.questid = questid
			answer = questions.at[questid,"a0"]

			loop.call_later(1,self.answer_question_soon,questid,answer)

		

	def answer_question_soon(self,questid,answer):
		common.answer_question(self,questid,answer)
		self.questid = None
		

	def showcards(self,msg,e_s2c = None):
		loop.call_later(1,self.showcards_soon,msg,e_s2c)

	def showcards_soon(self,msg,e_s2c = None):
		if self.cards_list == None:
			return
		if e_s2c != None :
			room = rmg.get(self.roomid)
			if msg == discard_words:
				rule = self.get_rule_nearly(None)
				room.discards(self,rule)
			else:
				rule = self.get_rule_nearly(room.last_rule)
				if rule != None:
					room.discards(self,rule)
				else:
					room.try_discards(self,None)

	def get_rule_nearly(self,last_rule):
		if self._cards_list == None:
			return
		rule = None
		if last_rule == None:
			card = self._cards_list[len(self._cards_list)-1]
			got_count = self._cards_flat.get(card) or 0
			discards = [card] * got_count
			rule = Rule(discards,True)
		else:
			index = len(self._cards_list)-1
			card = 0
			while index >= 0:
				card = self._cards_list[index]
				if  card > last_rule.origin_value :
					discards = self.get_cards_nearly(index,last_rule)
					if discards != None:
						rule = Rule(discards,True)
						break
				index -= 1

		return rule

	def get_cards_nearly(self,index,last_rule):
		card = self._cards_list[index]
		got_count = self._cards_flat.get(card) or 0
		if last_rule.rule_type == pattern.single:
			return [card]
		elif last_rule.rule_type == pattern.double:
			if got_count >= 2:
				return [card] * 2
		elif last_rule.rule_type == pattern.triple:
			if got_count >= 3:
				return [card] * 3
		elif last_rule.rule_type == pattern.triple_with_single:
			count = len(self._cards_list)
			if got_count >= 3 and  count >= 4:
				i = count -1
				while i >= 0 :
					if self._cards_list[i] != card:
						cards = [card] * 3
						cards.append(self._cards_list[i])
						return cards
					i -= 1
		elif last_rule.rule_type == pattern.triple_with_two:
			count = len(self._cards_list)
			if got_count >= 3 and  count >= 5:
				i = count -1
				while i >= 0 :
					if self._cards_list[i] != card:
						sec_got_count = self._cards_flat.get(self._cards_list[i]) or 0
						if sec_got_count >= 2:
							cards = [card] * 3
							cards.append(self._cards_list[i])
							cards.append(self._cards_list[i])
							return cards
					i -= 1
		elif last_rule.rule_type == pattern.fourfold_with_single:
			count = len(self._cards_list)
			if got_count >= 4 and  count >= 5:
				i = count -1
				while i >= 0 :
					if self._cards_list[i] != card:
						cards = [card] * 4
						cards.append(self._cards_list[i])
						return cards
					i -= 1

		elif last_rule.rule_type == pattern.fourfold_with_two:
			count = len(self._cards_list)
			if got_count >= 4 and  count >= 6:
				cards = [card] * 4
				i = count -1
				while i >= 0 :
					if self._cards_list[i] != card:
						cards.append(self._cards_list[i])
					if len(cards) >= 6:
						break
					i -= 1
				return cards
		elif last_rule.rule_type == pattern.fourfold_with_two_pairs:
			count = len(self._cards_list)
			if got_count >= 4 and  count >= 8:
				cards = [card] * 4
				i = count -1
				tempdic = {}
				while i >= 0 :
					if self._cards_list[i] != card and tempdic.get(self._cards_list[i]) == None:
						sec_got_count = self._cards_flat.get(self._cards_list[i]) or 0
						if sec_got_count >= 2:
							tempdic[self._cards_list[i]] = sec_got_count - 2
							cards.append(self._cards_list[i])
							cards.append(self._cards_list[i])
					if len(cards) >= 8:
						break
					i -= 1
				return cards
		elif last_rule.rule_type == pattern.straight:
			count = len(self._cards_list)
			if count >= last_rule.count:
				cards = [card]
				for x in range(card - last_rule.count + 1,card):
					sec_got_count = self._cards_flat.get(x) or 0
					if sec_got_count > 0:
						cards.append(x)
					else:
						return None
				if len(cards) == last_rule.count:
					return cards
		elif last_rule.rule_type == pattern.straight_pairs:
			count = len(self._cards_list)
			if got_count >= 2 and count >= last_rule.count:
				cards = [card] * 2
				for x in range(card - last_rule.flatcount + 1,card):
					sec_got_count = self._cards_flat.get(x) or 0
					if sec_got_count >= 2:
						cards.append(x)
						cards.append(x)
					else:
						return None
				if len(cards) == last_rule.count:
					return cards
		elif last_rule.rule_type == pattern.plane:
			count = len(self._cards_list)
			if got_count >= 3 and count >= last_rule.count:
				cards = [card] * 3
				for x in range(card - last_rule.flatcount + 1,card):
					sec_got_count = self._cards_flat.get(x) or 0
					if sec_got_count >= 3:
						cards.extend([x,x,x])
					else:
						return None
				if len(cards) == last_rule.count:
					return cards
		elif last_rule.rule_type == pattern.plane_with_single:
			count = len(self._cards_list)
			if got_count >= 3 and count >= last_rule.count:
				cards = [card] * 3
				for x in range(card - last_rule.count // 4 + 1,card):
					sec_got_count = self._cards_flat.get(x) or 0
					if sec_got_count >= 3:
						cards.extend([x,x,x])
					else:
						return None
				i = count -1
				while i >= 0 :
					if self._cards_list[i] != card:  # if meet bomb . forget it 
						cards.append(self._cards_list[i])
					if len(cards) >= last_rule.count:
						return cards
					i -= 1
		elif last_rule.rule_type == pattern.plane_with_pairs:
			count = len(self._cards_list)
			if got_count >= 3 and count >= last_rule.count:
				cards = [card] * 3
				for x in range(card - last_rule.count // 5 + 1,card):
					sec_got_count = self._cards_flat.get(x) or 0
					if sec_got_count >= 3:
						cards.extend([x,x,x])
					else:
						return None
				tempdic = {}
				i = count -1
				while i >= 0 :
					if self._cards_list[i] != card and tempdic.get(self._cards_list[i]) == None:         # if meet super bomb . forget it 
						sec_got_count = self._cards_flat.get(self._cards_list[i]) or 0
						if sec_got_count >= 2:
							tempdic[self._cards_list[i]] = sec_got_count - 2
							cards.extend([self._cards_list[i],self._cards_list[i]])
					if len(cards) >= last_rule.count:
						return cards
					i -= 1
