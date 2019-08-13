CARDS = [3,4,5,6,7,8,9,10,11,12,13,14,15,
		 3,4,5,6,7,8,9,10,11,12,13,14,15,
		 3,4,5,6,7,8,9,10,11,12,13,14,15,
		 3,4,5,6,7,8,9,10,11,12,13,14,15,16,17]

CARDS_MIN_VALUE = 3
CARDS_MAX_VALUE = 17

JOKER_R = 17
JOKER_r = 16

CARDS_TO_NAME = {10:"T",11:"J",12:"Q",13:"K",14:"A",15:"2",16:"b",17:"B"}
NAME_TO_CARDS = {"t":10,"j":11,"q":12,"k":13,"a":14}
for k,v in CARDS_TO_NAME.items():
	NAME_TO_CARDS[v]=k

STRAIGHT_SPECIALS = {15:True,16:True,17:True}

def sortFunc_0(t):
	return t[0]
def sortFunc_1(t):
	return t[1]

import random
def sample(cards,count):
	total = len(cards)
	if total < count:
		return
	temp = []
	while count > 0:
		index = random.randint(0,total-1)
		card = cards.pop(index)
		temp.append(card)
		count -= 1
		total -= 1
	return cards,temp

def tostr(cards):
	temp = []
	for card in cards:
		name = CARDS_TO_NAME.get(card) or str(card)
		temp.append(name)

	return "".join(temp)

def validate(discards):
	for card in discards:
		if type(card) != int:
			return False
		if card < CARDS_MIN_VALUE or card > CARDS_MAX_VALUE:
			return False
	return True
		
def str2card(s):
	if type(s) != str or s == ' ':
		return 
	card = NAME_TO_CARDS.get(s)
	if card != None:
		return card
	try:
		card = int(s)
		if card < CARDS_MIN_VALUE or card > CARDS_MAX_VALUE:
			return
		return card
	except Exception:
		return 

def flat_cards(cards):
	t = {}
	for c in cards:
		if t.get(c) == None:
			t[c] = 1
		else:
			t[c] += 1
	return t


from enum import Enum
class pattern(Enum):
    single  = 1
    double = 2 
    triple = 3 
    triple_with_single = 4
    triple_with_two = 5
    fourfold_with_single = 6
    fourfold_with_two = 7
    fourfold_with_two_pairs= 8
    straight = 9
    straight_pairs = 10
    plane = 11
    plane_with_single = 12
    plane_with_pairs = 13
    bomb = 1000

class Rule(object):
	"""docstring for Rule"""
	def __init__(self, cards,parse):
		super(Rule, self).__init__()
		cards.sort()
		self.count = len(cards)
		self.cards = cards
		self.flatcards= flat_cards(cards)
		self.cards_key = list(self.flatcards.keys())
		self.cards_key.sort()
		self.cards_key.sort(key=self.sort_by_count)
		self.cards_count = list(self.flatcards.values())
		self.cards_count.sort()
		self.flatcount = len(self.cards_count)
		self.value = 0
		self.origin_value = 0
		if parse:
			self.rule_type = self.parse_rule_type()
			if self.rule_type != None:
				self.origin_value = self.cards_key[self.flatcount-1]
				self.value = self.origin_value * self.rule_type.value

	def sort_by_count(self,card):
		return self.flatcards[card]


	def __lt__(self,other):
		return self.value < other.value
	def __gt__(self,other):
		return self.value > other.value

	def fit(self,other):
		if self.rule_type == pattern.bomb :
			return True
		return self.rule_type == other.rule_type

	def parse_rule_type(self):
		if self.parse_straight():
			return pattern.straight
		if self.parse_straight_pairs():
			return pattern.straight_pairs
		if self.count == 1:
			return pattern.single
		elif self.count == 2:
			if self.flatcount == 1:
				return pattern.double
			elif self.cards[0] == JOKER_r and self.cards[1] == JOKER_R:
				return pattern.bomb
		elif self.count == 3:
			if self.flatcount == 1:
				return pattern.triple

		elif self.count == 4:
			if self.flatcount == 1:
				return pattern.bomb
			elif self.flatcount == 2 and self.cards_count[0] != 2:
				return pattern.triple_with_single
		elif self.count == 5:
			if self.flatcount == 2:
				if self.cards_count[0] == 2 :
					return pattern.triple_with_two
				else:
					return pattern.fourfold_with_single
		elif self.count == 6:
			if self.cards_count[self.flatcount - 1] == 4:
				return pattern.fourfold_with_two
			if self.flatcount == 2:
				if self.cards_count[0] == 3:
					return pattern.plane
		elif self.count == 8:
			if self.cards_count[0] == 2 and self.cards_count[1] == 2 and self.cards_count[2] == 4:
				return pattern.fourfold_with_two_pairs


	def parse_straight(self,straight_count = 5):
		straight = False
		if self.count >= straight_count:
			if self.flatcount == self.count:
				straight = True
				if STRAIGHT_SPECIALS.get(self.cards[0]):
					straight = False
				else:
					for i in range(1,self.count):
						if STRAIGHT_SPECIALS.get(self.cards[i]):
							straight = False
							break
						if self.cards[i] - self.cards[i-1] != 1:
							straight = False
							break
		return straight
	def parse_straight_pairs(self):
		if self.count < 6:
			return False
		if self.count % 2 > 0:
			return False
		if self.flatcount < 3:
			return False
		for c in self.cards_count:
			if c != 2:
				return False
		if not Rule(self.cards_key,False).parse_straight(3):
			return False
		return True

