#!/usr/bin/env python3

###IMPORTS
import psutil as ps 
import time, datetime, os
import logging
from telegram import (InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove, ParseMode)
from telegram.ext import (Updater, CommandHandler, MessageHandler, Filters,
                          ConversationHandler, CallbackQueryHandler)

import secret_hitler_game as shgame


# Enable logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', 
					level=logging.INFO)

logger = logging.getLogger(__name__)


# Setup Telegram Bot
try:
	with open("TOKEN") as f:
		TOKEN = f.readline()

except Exception:
     logger.critical('TOKEN not found')
     #continue if file not found

game = shgame.Game()

# Special Keyboards
GAMEKEYBOARD = [["/gesetze", "/karten"], 
				["/show_president", "/help"]
				]

PRESIDENT_KEYBOARD = [['/wahl', '/ziehen'], 
					['/next_round', '/president_powers']]

# Konstanten für convo handling
DISCARD, CANCELOR, LAW, PLAYER, CANDIDATE, VOTE = range(6)

# Constants to handle permissions
PEEK_BOOL = False
LOYALTY_BOOL = False
KILL_BOOL = False
VOTING_BOOL = False	
GOT_FORCED = False

# Methoden zur Kommunikation
def start(update, context):
	#Willkommenstext versenden 
	welcome_text = ("Willkommen beim Secret Hitler Bot für Telegram. \n\n"
					"Die verfügbaren Befehle kannst du mit /help aufrufen.\n"
					"Tritt einer Runde mit /beitreten bei.\n"
					"Wenn alle Spieler da sind (/show_player) Spielsetup mit /setup aufrufen."
					)
	reply_keyboard = [['/beitreten', '/setup'], 
						['/help', '/show_player']]
	logger.info('{} hat /start aufgerufen'.format(update.message.from_user.username))
	context.bot.send_photo(chat_id=update.message.from_user.id, photo="https://i.imgur.com/g7jtYmA.png")
	update.message.reply_text(text=welcome_text, reply_markup=ReplyKeyboardMarkup(reply_keyboard))

def add_player(update, context):
	# Adds to requesting Player to the game
	if game.add_player(update.message.from_user.first_name, update.message.from_user.id, update.message.from_user.username):
		update.message.reply_text("Du bist der Gruppe beigetreten!\nViel Spass!")
	else:
		update.message.reply_text("Das hat nicht geklappt.\nBist du vielleicht schon in der Gruppe? /show_player")

def remove_player(update, context):
	# removes Player with his message uid
	if game.remove_player(update.message.from_user.id):
		update.message.reply_text("Du wurdest aus der Gruppe entfernt.")
		logger.info("Spieler {} wurde entfernt".format(update.message.from_user.first_name))
	else:
		update.message.reply_text("Das hat nicht geklappt.")
		logger.info("Spieler konnte nicht entfernt werden")

def show_player(update, context):
	# Lists all enrolled Players
	logger.info("{} requesting show_player".format(update.message.from_user.first_name))
	if game.numplayers > 0:
		update.message.reply_text("Die Spieler in dieser Runde heißen:")
		for player in game.players:
			logger.info(player.__dict__)
			update.message.reply_text(text="{}".format(player.name))
	else:
		update.message.reply_text("Keine Spieler registriert.")

def show_game(update,context):
	# prints the game dict to the log
	logger.info(game.__dict__)
	return True

def fill_party(update, context):
	# Fills Party to have at least 5 players; Debugging only
	if not game.is_setup:
		rn_names = ["John", "Lucie", "Kyle", "Maria", "Mitchel"]
		for i in range(5-game.numplayers):
			game.add_player(rn_names[i], -i, None)
		update.message.reply_text('Party aufgefüllt.')
		logger.info("jetzt sind es {} Spieler".format(game.numplayers))
	else:
		update.message.reply_text('Spiel bereits gestartet.')

def game_setup(update, context):
	# for the game setup, each player gets a random faction plus one facist get hitler role
	if not game.is_setup:
		if game.numplayers >= 5: 
			# setup function of Game class
			game.setup()

			# telling the players who they are
			# telling the facist who the other facists are. If there are 7-10 players, Hitler doesnt get to know the facists
			for player in game.players:
				if player.uid > 0:
					# LIBERALS
					if player.faction == 'Liberal':
						# send Liberal image
						context.bot.send_photo(chat_id=player.uid, photo='https://i.imgur.com/8UFUhzR.png', reply_markup=ReplyKeyboardMarkup(GAMEKEYBOARD))
					
					# HITLER
					elif player.faction == 'Facist' and  player.is_hitler:
						# send Hitler image					
						if len(game.players) < 7:
							other_facists = [other_player.name for other_player in game.players if other_player.faction == 'Facist' and other_player.name != player.name]
						
							facist_string = ''

							if len(other_facists) > 0: 
								facist_string = "andere Faschisten: " + ' '.join(other_facists) + "  "
						else:
							facist_string = ''

						context.bot.send_photo(chat_id=player.uid, caption=facist_string, photo='https://i.imgur.com/5M3dklF.png', reply_markup=ReplyKeyboardMarkup(GAMEKEYBOARD))

					# OTHER FACISTS
					else:
						# send Facist image
						other_facists = [other_player.name for other_player in game.players if other_player.faction == 'Facist' and other_player.name != player.name and not other_player.is_hitler]
						hitler = [other_player.name for other_player in game.players if other_player.faction == 'Facist' and other_player.name != player.name and other_player.is_hitler]
						facist_string = ''

						if len(other_facists) > 0: 
							facist_string = "andere Faschisten: " + ' '.join(other_facists) + "  "
						
						if len(hitler) > 0:
							facist_string = facist_string + "Hitler: " + ''.join(hitler)	

						context.bot.send_photo(chat_id=player.uid, caption=facist_string, photo='https://i.imgur.com/6Imx62Z.png', reply_markup=ReplyKeyboardMarkup(GAMEKEYBOARD))
			
			# broadcast the first president
			for player in game.players:
				if player.uid > 0 and player.uid != game.president.uid:
					context.bot.send_message(chat_id=player.uid,
										text = "Der erste Präsident ist {}".format(game.president.name),
										reply_markup=ReplyKeyboardMarkup(GAMEKEYBOARD))			

			if game.president.uid > 0:
				context.bot.send_message(chat_id=game.president.uid,
									text="Du bist der erste Präsident.\nStarte die Runde mit /wahl\nDanach kannst du drei Gesetze /ziehen\nFalls du durch die Gesetzgebung eine spezielle Aktion durchführen drafst, schau in /president_powers nach.\nBeende die Runde mit /next_round",
									reply_markup=ReplyKeyboardMarkup(PRESIDENT_KEYBOARD)
									)

			# END setup
			logger.info('Spiel Setup erfolgreich.')
		
		else: 
			# Something went wrong
			update.message.reply_text('nicht genügend Spieler vorhanden.\nAktuelle Spieler -> /show_player')
	else:
		update.message.reply_text('Spiel bereits vorbereitet. /reset um es zurückzusetzen.')

def draw_three(update, context):
	# draws top three cards from deck.
	logger.info("{} versucht drei Karten zu ziehen".format(update.message.from_user.username))
	if game.is_setup and len(game.active_hand) == 0 and update.message.from_user.id == game.president.uid:
		if game.chancellor:
			game.draw(3)
			update.message.reply_text("Drei Karten gezogen:")
			for card in game.active_hand:
				update.message.reply_text(card)

			text = "Welche Karte möchtest du <b>ablegen</b>?"
			reply_keyboard = [['{}'.format(card)] for card in game.active_hand]
			update.message.reply_text(text=text, reply_markup=ReplyKeyboardMarkup(reply_keyboard), one_time_keyboard=True, parse_mode=ParseMode.HTML)

			# pass discarded card to discard func
			return DISCARD 
		
		else:
			update.message.reply_text(text='Es wurde noch kein Kanzler gewählt!\n/wahl', 
									reply_markup=ReplyKeyboardMarkup(PRESIDENT_KEYBOARD))
			return ConversationHandler.END

	else:
		# drawing fails
		update.message.reply_text(text="Du kannst keine Karten aufnehmen.", reply_markup=ReplyKeyboardMarkup(GAMEKEYBOARD))

		ConversationHandler.END

def discard(update, context):
	# discards the selected card from "draw_three"
	card = update.message.text
	logger.info("{} will be discarded".format(card))
	# discard func goes here
	for i in range(len(game.active_hand)):
		if game.active_hand[i] == card:
			game.discarded_cards.append(game.active_hand.pop(i))
			break
	logger.info("aktive Karten: {}".format(game.active_hand))
	
	# list_of_players = [[player.name] for player in game.players]
	update.message.reply_text(text='{} wurde abgelegt.'.format(update.message.text),
							reply_markup=ReplyKeyboardMarkup(PRESIDENT_KEYBOARD))

	contact_chancellor(update, context)

	return ConversationHandler.END  

def contact_chancellor(update, context):
	# asks chancellor what active card to activate
	if len(game.active_hand) == 2:
		# broadcast the process
		info_text = "Kanzler {} wählt ein Gesetz aus.".format(game.chancellor.name)
		broadcast(context, info_text)
		
		# this starts a new convo with the chancellor
		# send chancellor the message to chose the card
		# prepare markupKeyboard
		cards = [[card] for card in game.active_hand]
		context.bot.send_message(chat_id=game.chancellor.uid,
						 text="Du hast die Wahl!\naktive Gesetze mit /gesetze anzeigen", 
						 reply_markup=ReplyKeyboardMarkup(cards), 
						 one_time_keyboard=True)


		if update.message.from_user.id == game.president.uid:
			return ConversationHandler.END

	else:
		ConversationHandler.END

def pass_law(update, context):
	global GOT_FORCED

	if update.message.from_user.id == game.chancellor.uid:
		# passes law
		law = update.message.text
		logger.info("ausgewählt: {}".format(law))

		# pass law
		game.policies.append(law)
		game.round += 1

		# add discarded to discarded pile
		if game.active_hand[0] == law:
			# if first law is correct: 
			game.discarded_cards.append(game.active_hand[1])
		else:
			game.discarded_cards.append(game.active_hand[0])
		
		# empty hand
		game.active_hand = []
		GOT_FORCED = False
		# Rueckmeldung geben
		update.message.reply_text(text="{} verabschiedet".format(law), reply_markup=ReplyKeyboardMarkup(GAMEKEYBOARD))

		# allen Spielern Bescheid sagen
		for player in game.players:
			if player.uid > 0:
				context.bot.send_message(chat_id=player.uid, text="{} wurde von {} erlassen".format(law, update.message.from_user.first_name))

		# check wincondition
		if game.count_liberal_policies() == 5:
			win_announcement(context, 'Liberal', '5 liberale Gesetze wurden erlassen!')

		if game.count_facist_policies() == 6:
			win_announcement(context, 'Facist', '6 faschistische Gesetze wurden erlassen!')

		check_policies(context)
		logger.info("pass law schleife ends")

	else:
		update.message.reply_text('Nur der Kanzler kann Gesetze erlassen.')

def next_round(update, context):
	if update.message.from_user.id == game.president.uid:
		game.round += 1
		game.chancellor = None
		game.candidate = None

		# find next president
		pos = 0
		for player in game.players:
			if player.uid == game.president.uid:
				break
			else:
				pos += 1

		logger.info('aktueller Präsident an Pos {}'.format(pos))
		
		if pos < (len(game.players) - 1):
			game.president = game.players[pos + 1]

		elif pos == len(game.players) - 1:
			game.president = game.players[0]

		else:
			broadcast(context, "Konnte keinen neuen Präsident wählen.")

		# inform him about his powers
		if game.president.uid > 0:
			context.bot.send_message(chat_id=game.president.uid, 
									text="Du bist neuer Präsident.\nStarte die Runde mit /wahl\nDanach kannst du drei Gesetze /ziehen\nFalls du durch die Gesetzgebung eine spezielle Aktion durchführen drafst, schau in /president_powers nach.\nBeende die Runde mit /next_round",
									reply_markup=ReplyKeyboardMarkup(PRESIDENT_KEYBOARD))

		# tell everyone whos the new president and that the round has endet
		text = "Runde {} ist zu Ende. {} ist neuer Präsident".format(game.round, game.president.name)
		broadcast(context, text)

	else:
		update.message.reply_text('Nur der Präsident kann die Runde beenden.')

def force_law(update, context):
	# if 3 elections fail in a row, the top policy is passed
	global GOT_FORCED

	if game.is_setup and len(game.active_hand) == 0:
		if not game.chancellor:
			game.draw(1)
			policy = game.active_hand.pop()
			game.policies.append(policy)

			text = '{} wurde gezwungenermaßen erlassen. Die Sonderregeln sind nicht aktiv.'.format(policy)
			broadcast(context, text)
			GOT_FORCED = True
			check_policies(context)
		else:
			update.message.reply_text('Es gibt einen aktiven Kanzler!')
	else:
		update.message.reply_text('du kannst jetzt kein Gesetz erzwingen')

def policies(update, context):
	if game.is_setup and len(game.policies) > 0:
		update.message.reply_text('Folgende Gesetze sind aktiv:')
		for policy in game.policies:
			update.message.reply_text('{}'.format(policy))
	elif game.is_setup and len(game.policies) == 0:
		update.message.reply_text('Noch kein Gesetz erlassen')

def cards_left(update, context):
	if game.is_setup:
		update.message.reply_text('Es sind {} Gesetzeskarten übrig.'.format(len(game.deck)))

def show_president(update, context):
	# tells you the name of the current president
	update.message.reply_text('{} ist amtierender Präsident.'.format(game.president.name))

def show_chancellor(update, context):
	# tells you the name of the chancellor if there is one
	chancellor_name = game.chancellor.name

	if chancellor_name:
		update.message.reply_text('{} ist amtierender Kanzler.'.format(chancellor_name))

	else:
		update.message.reply_text('Gerade gibt es keinen amtierenden Kanzler.')

def cancel(update, context):
	logger.info("got conv cancel from {}".format(update.message.from_user.username))
	update.message.reply_text("Abgebrochen", reply_markup=ReplyKeyboardMarkup(GAMEKEYBOARD))
	return ConversationHandler.END

def show_top_3(update, context):
	#peek top 3 cards if less then 7 player and 3 active facist policies
	global PEEK_BOOL

	if PEEK_BOOL:
		top_cards = []
		for i in range(3):
			top_cards.append(game.deck[-i])
		update.message.reply_text("Top drei Karten sind: [{}]".format('] ['.join(top_cards)))
		PEEK_BOOL = False
	else:
		update.message.reply_text("Es müssen weniger als sieben Spieler und genau 3 faschistische Gesetze verabschiedet sein.\n/show_player  /gesetze")

def check_loyalty(update, context):
	# check player faction if > 7 player and 2 facist policies OR > 9 player and 1 facist policy
	global LOYALTY_BOOL

	if LOYALTY_BOOL:	
		# prepare list of players
		list_of_players = [[player.name] for player in game.players if player.uid != update.message.from_user.id]

		# select player to inspect
		update.message.reply_text(text='Wen möchtest du überprüfen?', reply_markup=ReplyKeyboardMarkup(list_of_players))

		LOYALTY_BOOL = False		

		return PLAYER
	else:
		update.message.reply_text(text='Voraussetzung nicht erfüllt.\n/show_player /gesetze')
		return ConversationHandler.END

def loyalty_of_player(update, context):
	# search for requested player
	for player in game.players:
		if player.name == update.message.text:
			faction = player.faction
			break

	update.message.reply_text(text='{} ist {}'.format(update.message.text, faction), 
					reply_markup=ReplyKeyboardMarkup(GAMEKEYBOARD))

	return ConversationHandler.END

def president_powers(update, context):
	powers = (	"/force_law um das oberste Gesetz zu erlassen\n"
				"/show_top_3 zeigt die oberen drei Gesetze\n"
				"/loyalty decke die Faktion eines anderen Spielers auf\n"
				"/execute erschieße einen Spieler\n"
			)
	update.message.reply_text(powers)

def select_target(update, context):
	# kill player if 4 or 5 facist policies are passed
	global KILL_BOOL

	if KILL_BOOL:
		# prepare list of players
		list_of_players = [[player.name] for player in game.players if player.uid != update.message.from_user.id]

		# select player to inspect
		update.message.reply_text(text='Wen möchtest du hinrichten?', reply_markup=ReplyKeyboardMarkup(list_of_players))

		# return playername to kill
		return PLAYER

	else:
		# check was not successfull
		update.message.reply_text(text='Es müssen min. 4 faschistische Gesetze aktiv sein.\n/gesetze')
		return ConversationHandler.END

def execute_target(update, context):
	# ausgewaehlten Spieler hinrichten.
	global KILL_BOOL

	target = update.message.text
	wincondition = False
	for player in game.players:
		if player.name == target:
			# execute order 66
			wincondition = player.is_hitler
			player.is_dead = True
			player.name = player.name + '[TOT]'
			KILL_BOOL = False
			break

	# Ausführung verkünden
	for player in game.players:
		if player.uid > 0:
			context.bot.send_message(chat_id=player.uid, 
				text="{} wurde von {} hingerichtet".format(target, update.message.from_user.first_name),
				reply_markup=ReplyKeyboardMarkup(GAMEKEYBOARD))

	# Checken ob er Hitler war
	if wincondition:
		win_announcement(context, 'Liberal', 'Hitler wurde hingerichtet')

	return ConversationHandler.END

def helpme(update, context):
	helptext = ("Du kannst folgendes tun:\n"
		"/start um die Startnachricht anzuzeigen\n"
		"/beitreten um einer Runde beizutreten\n"
		"/verlassen um die Runde zu verlassen\n"
		"/show_player um die angemeldeten Spieler aufzulisten\n"
		"/fill um die Party aufzufüllen. DEBUGGING ONLY\n"
		"/setup um das Setup zu starten. Dafür müssen alle Spieler angemeldet sein!\n"
		"/reset um das Spiel zurückzusetzen\n"
		"/gesetze um aktive Gesetze zu sehen\n"
		"/president_powers um Befehle für Präsident anzuzeigen"
		)
	update.message.reply_text(helptext)

def reset(update, context):
	# resets the game
	global VOTING_BOOL
	VOTING_BOOL = False
	game.reset()
	update.message.reply_text("Spiel zurückgesetzt.")

def error(update, context):
	# Setup error logging
	logger.warning('Update "%s" caused error "%s"', update, context.error)

def cheat_fac_pol(update, context):
	# cheats in one facist policy to test stuff
	game.policies.append('Facist')
	update.message.reply_text("Facist policy cheated in /gesetze")

def cheat_president(update, context):
	# cheats the requesting player to be president
	for player in game.players:
		if player.uid == update.message.from_user.id:
			game.president = player

	context.bot.send_message(chat_id=game.president.uid,
							text='Du wurdest zum neuen Präsident gecheatet',
							reply_markup=ReplyKeyboardMarkup(PRESIDENT_KEYBOARD))
	logger.warning("{} hat 'cheat_president' aufgerufen".format(update.message.from_user.first_name))

def cheat_election(update, context):
	# fills the votes with 'Ja!' votes
	missing = len(game.players) - len(game.votes) -1

	for _ in range(missing):
		game.votes.append(['dummy','Ja!'])

	logger.info('cheated {} votes'.format(missing))

def reveal_hitler(update, context):
	#### LEGACY
	# hitler reveals himself if he wins the game
	hitler_check = False
	for player in game.players:
		if player.uid == update.message.from_user.id:
			hitler_check = player.is_hitler

	if game.count_facist_policies() >= 3 and hitler_check:
		win_announcement(context, 'Facist', 'Hitler wurde zum Kanzler gewählt')
	else:
		update.message.reply_text('Entweder noch nicht genügend faschistische Gesetze erlassen oder du bist nicht Hitler.')

def select_candidate(update, context):
	# only president may start the election 
	# only start voting if there is not active voting already
	global VOTING_BOOL

	if not game.chancellor:
		if (update.message.from_user.id == game.president.uid) and not VOTING_BOOL:
			game.votes=[]

			list_of_players = [[player.name] for player in game.players if player.uid != update.message.from_user.id]
			
			# returns the vote to the counting method
			update.message.reply_text('Wähle deinen Kanzlerkandidaten', reply_markup=ReplyKeyboardMarkup(list_of_players))
			# set the 'voting is active' flag
			VOTING_BOOL = True

			# returns the chosen candidate to the vote method to start the vote Convo
			return CANDIDATE

		else:
			update.message.reply_text('Nur der Präsident kann die Abstimmung starten.')
			return ConversationHandler.END

	else: 
		update.message.reply_text('Es wurde bereit {} zum Kanzler gewählt.'.format(game.chancellor.name))
		return ConversationHandler.END

def start_election(update, context):
	# Sets candidate
	game.candidate = update.message.text
	
	# prepare text and keyboard
	text = "{} wurde von {} als Kanzlerkandidaten vorgeschlagen. Bitte stimme jetzt ab".format(update.message.text, game.president.name)
	keyboard = [['Ja!'],['Nein!']]

	# broadcast with custom reply Keyboard
	broadcast(context, text, keyboard)

	return ConversationHandler.END	

def vote(update, context):
	# takes the players votes
	global VOTING_BOOL 
	
	# checks if player has already voted
	for vote in game.votes:
		if vote[0] == update.message.from_user.first_name:
			update.message.reply_text(text='Du hast bereits abgestimmt',
								reply_markup=ReplyKeyboardMarkup(GAMEKEYBOARD))
			return ConversationHandler.END

	# takes the vote
	if VOTING_BOOL: 
		game.vote(update.message.from_user.first_name, update.message.text)
		
	if update.message.from_user.id == game.president.uid:
		update.message.reply_text(text='Deine Stimme wurde angenommen.',
						reply_markup=ReplyKeyboardMarkup(PRESIDENT_KEYBOARD))
	else:
		update.message.reply_text(text='Deine Stimme wurde angenommen.',
						reply_markup=ReplyKeyboardMarkup(GAMEKEYBOARD))


	# if all players have voted count the votes
	if len(game.votes) == len(game.players):
		# end voting
		VOTING_BOOL = False
		# count the votes
		num_yes = [vote[1] for vote in game.votes].count('Ja!')
		num_no = [vote[1] for vote in game.votes].count('Nein!')

	
		text = "Alle Spieler haben abgestimmt. "
		if num_yes > num_no:
			# election successfull
			# set elected chancellor atribute
			for player in game.players:
				if player.name == game.candidate:
					game.chancellor = player

			text += "{} wurde mit {} zu {} zum Kanzler gewählt.".format(game.chancellor.name, num_yes, num_no)
			# reset failed election counter
			game.failed_elections = 0

			# check if Hitler got elected
			# first get hitlers uid
			for player in game.players:
				if player.is_hitler:
					hitler_id = player.uid
			# check if the new chancellor is hitler
			if game.count_facist_policies() >= 3 and game.chancellor.uid == hitler_id:
				win_announcement(context, 'Facist', 'Hitler wurde zum Kanzler gewählt')

		else:
			# election failed
			text += "Die Wahl ist mit {}x Ja zu {}x Nein gescheitert.".format(num_yes, num_no)
			# add one to failed_elections counter
			game.failed_elections += 1

			# if critical amount of elections have failed, force top law
			if game.failed_elections == 3:
				# force law
				force_law(update, context)
				# reset failed elections
				game.failed_elections = 0

		# broadcast the result to all players
		broadcast(context, text, GAMEKEYBOARD)

		result = '\n'.join([': '.join([vote[0], vote[1]]) for vote in game.votes])
		for player in game.players:
			if player.uid > 0:
				if player.uid == game.president.uid:
					context.bot.send_message(chat_id=player.uid, 
											text=(result + '\nZiehe jetzt drei Karten /ziehen'),
											reply_markup=ReplyKeyboardMarkup(PRESIDENT_KEYBOARD),
											one_time_keyboard=True)
				else:
					context.bot.send_message(chat_id=player.uid, 
											text=result,
											reply_markup=ReplyKeyboardMarkup(GAMEKEYBOARD),
											one_time_keyboard=True)

		# end the election and unsetts the flag
		VOTING_BOOL = False
		game.candidate = None

def win_announcement(context, faction, reason):
	# shoutout to End the round, has to be called from inside bot method
	if faction == 'Liberal':
		# The good guys won
		pic = 'https://i.imgur.com/5HuSdCZ'
		text = 'Das Gute hat gesiegt!'

	else:
		# The bad guys won
		pic = 'https://i.imgur.com/8U9vjVX'
		text = 'Das Böse ist an der Macht!'

	# broadcast the message
	for player in game.players:
			if player.uid > 0:
				context.bot.send_photo(chat_id=player.uid, caption=text, photo=pic)
				context.bot.send_message(chat_id=player.uid, text=reason, reply_markup=ReplyKeyboardMarkup([['/reset'], ['/start']]))

def broadcast(context, text, keyboard=None, one_time_keyboard=True):
	# broadcasts a message to all listed players
	for player in game.players:
		if player.uid > 0:
			if keyboard:
				context.bot.send_message(chat_id=player.uid, text=text, reply_markup=ReplyKeyboardMarkup(keyboard), one_time_keyboard=True)
			else:
				context.bot.send_message(chat_id=player.uid, text=text)
	return True

def check_policies(context):
	# checks the active policies. If something special happend, broadcast it
	global PEEK_BOOL
	global LOYALTY_BOOL
	global KILL_BOOL
	global GOT_FORCED

	if game.numplayers <= 6 and game.count_facist_policies() == 3 and not GOT_FORCED:
		# the top three cards may be eximinated by the president
		PEEK_BOOL = True
		text = "Es sind insgesamt drei faschistische Gesetze erlassen worden. Der Präsident darf daher die obersten drei Gesetze auf dem Stapel anschauen.\n/show_top_3"
		broadcast(context, text)

	elif (len(game.players) > 7 and game.count_facist_policies() == 2) or (len(game.players) > 9 and game.count_facist_policies() == 1) and not GOT_FORCED:
		# loyalty of one player may be investigated by the president
		LOYALTY_BOOL = True
		text = "Die Faktion eines Spielers darf nun vom Präsident untersucht werden.\n/loyalty"
		broadcast(context, text)

	elif game.count_facist_policies() >= 4:
		# one player must be executed by the president
		KILL_BOOL = True
		text = "Es wurden {} faschistische Gesetze erlassen. Der Präsident muss jemanden hinrichten.\n/execute"
		broadcast(context, text)

def main():
	# updater & dispatcher initialisieren
	updater = Updater(token=TOKEN, use_context=True)
	dp = updater.dispatcher
	
	# Handler fuer Abläufe
	draw_handler = ConversationHandler(
		entry_points=[CommandHandler("ziehen", draw_three)],

		states = {
			DISCARD: [MessageHandler(Filters.regex('^(Facist|Liberal)$'), discard)],
		},

		fallbacks=[CommandHandler('cancel', cancel)]

		)

	# select_law_handler = ConversationHandler(
	# 	entry_points=[MessageHandler(Filters.regex('^(Facist|Liberal)$'), contact_chancellor)],

	# 	states = {
	# 		LAW: [MessageHandler(Filters.regex('^(Facist|Liberal)$'), pass_law)], 

	# 		},

	# 	fallbacks=[CommandHandler('cancel', cancel)]

	# 	)

	loyalty_handler = ConversationHandler(
		entry_points=[CommandHandler('loyalty', check_loyalty)],

		states = {
			PLAYER: [MessageHandler(Filters.text, loyalty_of_player)]
		},

		fallbacks=[CommandHandler('cancel', cancel)]
		)

	kill_handler = ConversationHandler(
		entry_points=[CommandHandler('execute', select_target)],

		states = {
			PLAYER: [MessageHandler(Filters.text, execute_target)]
		},

		fallbacks=[CommandHandler('cancel', cancel)]
		)

	start_election_handler = ConversationHandler(
		entry_points=[CommandHandler('wahl', select_candidate)],

		states = {
			CANDIDATE: [MessageHandler(Filters.text, start_election)]
		},

		fallbacks=[CommandHandler('cancel', cancel)]
		)

	vote_handler = MessageHandler(Filters.regex('^(Ja!|Nein!)$'), vote)

	pass_law_handler = MessageHandler(Filters.regex('^(Liberal|Facist)$'), pass_law)

	dp.add_handler(draw_handler)
	# dp.add_handler(select_law_handler)
	dp.add_handler(loyalty_handler)
	dp.add_handler(kill_handler)
	dp.add_handler(start_election_handler)
	dp.add_handler(vote_handler)
	dp.add_handler(pass_law_handler)

	# Handler fuer die verschiedenen Methoden erschaffen
	commands = [
				[["start"], start],
				[["beitreten"], add_player],
				[["show_player"], show_player],
				[["fill"], fill_party],
				[["setup"], game_setup],
				[["verlassen"], remove_player],
				[["help"], helpme],
				[["gesetze"], policies],
				[["karten"], cards_left],
				[["reset"], reset],
				[["president_powers"], president_powers],
				[["show_top_3"], show_top_3],
				[["cheat_fac_pol"], cheat_fac_pol],
				[["reveal_hitler"], reveal_hitler],
				[["force_law"], force_law],
				[["cheat_president"], cheat_president],
				[["show_president"], show_president],
				[["show_chancellor"], show_chancellor],
				[["next_round"], next_round],
				[["cheat_election"], cheat_election],
				[["show_game"], show_game]
				]

	for command, function in commands:
		dp.add_handler(CommandHandler(command, function))


	callbacks = [
		['start', start]
	]

	for callback, function in callbacks:
		dp.add_handler(CallbackQueryHandler(pattern=callback, callback=function))

	dp.add_error_handler(error)

	# Starte Telegram Bot
	logger.info('Logged in as @{}'.format(updater.bot.getMe().username))
	logger.info('starting poll')
	updater.start_polling()
	updater.idle()


	logger.info('stopping Bot')

if __name__ == '__main__':
	main()