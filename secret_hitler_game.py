#!/usr/bin/env python3
# Classes and Methods for the main game engine
import random

class Player:
	"""docstring for Player"""
	def __init__(self, name, uid, uname):
		self.name = name
		self.uid = uid
		self.uname = uname
		self._faction = None
		self._is_hitler = False
		self._is_dead = False

	@property
	def faction(self):
		""" Here goes the faction attribute of the Player """
		return self._faction

	@faction.setter
	def faction(self, value):
		self._faction = value

	@faction.deleter
	# not used usually in our case. Just here as a reminder it exists
	def faction(self):
		del self._faction


	@property
	def is_hitler(self):
		return self._is_hitler
	
	@is_hitler.setter
	def is_hitler(self, value):
		self._is_hitler = value

	@property
	def is_dead(self):
		return self._is_dead
	
	@is_dead.setter
	def is_dead(self, value):
		self._is_dead = value
	

class Game:
	"""docstring for Game"""
	def __init__(self):
		self.players = []
		self.round = 0
		self.numplayers = len(self.players)		
		self.is_setup = False
		# Deck with policy cards that are still available
		self.deck = ["Liberal" for _ in range(6)] + ["Facist" for _ in range(11)]
		random.shuffle(self.deck)
		# active hand
		self._active_hand = []
		# discarded cards
		self._discarded_cards = []
		# active policies
		self.policies = []

	@property
	def active_hand(self):
		return self._active_hand

	@active_hand.setter
	def active_hand(self, cards):
		self._active_hand = cards

	@property
	def discarded_cards(self):
		return self._discarded_cards
	
	@discarded_cards.setter
	def discarded_cards(self, cards):
		self._discarded_cards = cards

	@property
	def round(self):
		return self._round
	
	@round.setter
	def round(self, round):
		self._round = round


	def add_player(self, name, uid, uname):
		# Spieler Obj zur Liste aller Spieler hinzufügen
		for existing_player in self.players:
			if existing_player.name == name:
				print("Spieler mit Namen {} bereits vorhanden.".format(existing_player.name))	
				return False

		self.players.append(Player(name, uid, uname))
		self.numplayers = len(self.players)
		print("Spieler mit Namen {} hinzugefügt.".format(self.players[-1].name))
		return True

	def remove_player(self, uid):
		# Spieler Obj von Liste entfernen
		for existing_player in self.players:
			if existing_player.uid == uid:
				print(self.players.pop())
				self.numplayers = len(self.players)
				return True
			else:
				print("Spieler nicht gefunden")
				return False

	def setup(self):
		# Initiales Setup
		if self.numplayers >= 5:
			# calculation number of liberals and facists
			numliberals = int(self.numplayers/2)+1
			
			# shuffle playerlist once
			random.shuffle(self.players)
			
			# assing liberals to first players in list
			for i in range(numliberals):
				self.players[i].faction = "Liberal"

			# assing facist to other players in list
			for i in range(numliberals, self.numplayers):
				self.players[i].faction = "Facist"

			# pick one facist to be hitler
			rn = random.randint(numliberals, self.numplayers-1)
			self.players[rn].is_hitler = True
			
			# shuffle playerlist to hide who is who
			random.shuffle(self.players)

			# End Setup
			self.is_setup = True
			return True

		else:
			return False

	def reset(self):
		self.players = []
		self.numplayers = 0
		self.round = 0
		self.is_setup = False
		return True

	def shuffle(self):	
		# shuffle remaining cards in deck
		random.shuffle(self.deck)
		return True

	def draw(self, i):
		# ziehe i Karten vom Stapel
		if self.is_setup:
			# reset active hand
			self.active_hand = []
			
			# do i times
			for _ in range(i):
				# enough cards in deck
				if len(self.deck)>0:	
					self.active_hand.append(self.deck.pop())
				
				# deck needs reshuffle
				else:
					print("Deck leer. Mische neu.")
					for discarded in self.discarded_cards:
						self.deck.append(discarded)
					self.discarded_cards = []
					random.shuffle(self.deck)
					self.active_hand.append(self.deck.pop())
			return True

	def count_facist_policies(self):
		# count the active facist policies
		num_policies = 0
		for policy in self.policies:
			if policy == 'Facist':
				num_policies += 1

		return num_policies

	def count_liberal_policies(self):
		# count the active liberal policies
		num_policies = 0
		for policy in self.policies:
			if policy == 'Liberal':
				num_policies += 1

		return num_policies

def main():
	game = Game()
	print(game.deck)



if __name__ == '__main__':
	main()