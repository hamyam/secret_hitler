#!/usr/bin/env python3

###IMPORTS
import psutil as ps 
import time, datetime, os
import logging
from telegram import (InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, ReplyKeyboardRemove)
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

GAMEKEYBOARD = [["/ziehen", "/gesetze"], 
				["/karten", "/help"]
				]

# Konstanten für convo handling
DISCARD, CANCELOR, PASSLAW, PLAYER = range(4)


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
		logger.info("Spieler {} wurde entfernt".format(update.message.from_user.name))
	else:
		update.message.reply_text("Das hat nicht geklappt.")
		logger.info("Spieler konnte nicht entfernt werden")

def show_player(update, context):
	# Lists all enrolled Players
	logger.info("{} requesting show_player".format(update.message.from_user.name))
	if game.numplayers > 0:
		update.message.reply_text("Die Spieler in dieser Runde heißen:")
		for player in game.players:
			logger.info(player.__dict__)
			update.message.reply_text(text="{}".format(player.name))
	else:
		update.message.reply_text("Keine Spieler registriert.")

def fill_party(update, context):
	# Fills Party to have at least 5 players; Debugging only
	rn_names = ["John", "Lucie", "Kyle", "Maria", "Mitchel"]
	for i in range(5-game.numplayers):
		game.add_player(rn_names[i], 0, None)
	update.message.reply_text('Party aufgefüllt.')
	logger.info("jetzt sind es {} Spieler".format(game.numplayers))

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
						sonderregel = "Wenn drei aktive faschistische Gesetze verabschiedet wurden und du zum Kanzler gewählt wirst: /reveal_hitler"
						context.bot.send_message(chat_id=player.uid, text=sonderregel)

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
	if game.is_setup:
		game.draw(3)
		update.message.reply_text("Drei Karten gezogen:")
		for card in game.active_hand:
			update.message.reply_text(card)

		text = "Welche Karte möchtest du ablegen?"
		reply_keyboard = [['{}'.format(card)] for card in game.active_hand]
		update.message.reply_text(text=text, reply_markup=ReplyKeyboardMarkup(reply_keyboard), one_time_keyboard=True)

		return DISCARD

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
	# hand over other 2 cards 


	# Inform Player
	list_of_players = [[player.name] for player in game.players if player.uid != update.message.from_user.id]
	# list_of_players = [[player.name] for player in game.players]
	update.message.reply_text(text='{} wurde abgelegt. Wer ist Kanzler?'.format(update.message.text),
					reply_markup=ReplyKeyboardMarkup(list_of_players), one_time_keyboard=True
					)
	
	return CANCELOR  # name of chancellor

def find_chancellor(update, context):
	# asks chancellor what active card to activate
	update.message.reply_text(text='{} wählt aus'.format(update.message.text), reply_markup=ReplyKeyboardMarkup(GAMEKEYBOARD))
	chancellor = update.message.text
	chat_id = None
	
	# find chancellor id to send message
	for player in game.players:
		if player.name == chancellor:
			chat_id = player.uid
			logger.info('Kanzler: {}  chat_id: {}'.format(chancellor, chat_id))
			break
	
	# send chancellor the message to chose the card
	if chat_id: # ID exists
		# prepare markupKeyboard
		cards = [[card] for card in game.active_hand]
		context.bot.send_message(chat_id=chat_id, text="Du hast die Wahl!\naktive Gesetze mit /gesetze anzeigen", reply_markup=ReplyKeyboardMarkup(cards), one_time_keyboard=True)
	else:
		logger.info('chat_id von Kanzler nicht gefunden.')

	return PASSLAW 

def pass_law(update, context):
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

	logger.info("pass law schleife ends")
	return ConversationHandler.END

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

def cancel(update, context):
	logger.info("got conv cancel from {}".format(update.message.from_user.username))
	update.message.reply_text("Abgebrochen", reply_markup=ReplyKeyboardMarkup(GAMEKEYBOARD))
	return ConversationHandler.END

def show_top_3(update, context):
	#peek top 3 cards if less then 7 player and 3 active facist policies
	if len(game.players) < 7 and game.count_facist_policies() == 3:
		top_cards = []
		for i in range(3):
			top_cards.append(game.deck[-i])
		update.message.reply_text("Top drei Karten sind {}".format(' '.join(top_cards)))
	else:
		update.message.reply_text("Es müssen weniger als sieben Spieler und genau 3 faschistische Gesetze verabschiedet sein.\n/show_player  /gesetze")

def check_loyalty(update, context):
	# check player faction if > 7 player and 2 facist policies OR > 9 player and 1 facist policy
	if (len(game.players) > 7 and game.count_facist_policies() == 2) or (len(game.players) > 9 and game.count_facist_policies() == 1):
		# prepare list of players
		list_of_players = [[player.name] for player in game.players if player.uid != update.message.from_user.id]

		# select player to inspect
		update.message.reply_text(text='Wen möchtest du überprüfen?', reply_markup=ReplyKeyboardMarkup(list_of_players))

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
	powers = (	"/show_top_3 zeigt die oberen drei Gesetze\n"
				"/loyalty decke die Faktion eines anderen Spielers auf\n"
				"/execute erschieße einen Spieler\n"
			)
	update.message.reply_text(powers)

def select_target(update, context):
	# kill player if 4 or 5 facist policies are passed
	if game.count_facist_policies() >= 4:
		# prepare list of players
		list_of_players = [[player.name] for player in game.players if player.uid != update.message.from_user.id]

		# select player to inspect
		update.message.reply_text(text='Wen möchtest du hinrichten?', reply_markup=ReplyKeyboardMarkup(list_of_players))

		return PLAYER

	else:
		update.message.reply_text(text='Es müssen min. 4 faschistische Gesetze aktiv sein.\n/gesetze')
		return ConversationHandler.END

def execute_target(update, context):
	# ausgewaehlten Spieler hinrichten.
	target = update.message.text
	wincondition = False
	for player in game.players:
		if player.name == target:
			wincondition = player.is_hitler
			player.is_dead = True
			player.name = player.name + '[TOT]'
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
	game.reset()
	update.message.reply_text("Spiel zurückgesetzt.")

def error(update, context):
	# Setup error logging
	logger.warning('Update "%s" caused error "%s"', update, context.error)

def cheat_fac_pol(update, context):
	# cheats in one facist policy to test stuff
	game.policies.append('Facist')
	update.message.reply_text("Facist policy cheated in /gesetze")

def reveal_hitler(update, context):
	# hitler reveals himself if he wins the game
	hitler_check = False
	for player in game.players:
		if player.uid == update.message.from_user.id:
			hitler_check = player.is_hitler

	if game.count_facist_policies() >= 3 and hitler_check:
		win_announcement(context, 'Facist', 'Hitler wurde zum Kanzler gewählt')
	else:
		update.message.reply_text('Entweder noch nicht genügend faschistische Gesetze erlassen oder du bist nicht Hitler.')

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
				context.bot.send_message(chat_id=player.uid, text=reason, reply_markup=ReplyKeyboardMarkup([['/reset']]))

def main():
	# updater & dispatcher initialisieren
	updater = Updater(token=TOKEN, use_context=True)
	dp = updater.dispatcher
	
	# Handler fuer Abläufe
	draw_handler = ConversationHandler(
		entry_points=[CommandHandler("ziehen", draw_three)],

		states = {
			DISCARD: [MessageHandler(Filters.regex('^(Facist|Liberal)$'), discard)],

			CANCELOR: [MessageHandler(Filters.text, find_chancellor)],

			PASSLAW: [MessageHandler(Filters.regex('^(Facist|Liberal)$'), pass_law)]
			},

		fallbacks=[CommandHandler('cancel', cancel)]

		)

	pass_handler = ConversationHandler(
		entry_points=[MessageHandler(Filters.regex('^(Facist|Liberal)$'), pass_law)],

		states = {
			PASSLAW: [MessageHandler(Filters.regex('^(Facist|Liberal)$'), pass_law)]
			},

		fallbacks=[CommandHandler('cancel', cancel)]

		)

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

	dp.add_handler(draw_handler)
	dp.add_handler(pass_handler)
	dp.add_handler(loyalty_handler)
	dp.add_handler(kill_handler)

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
				[["reveal_hitler"], reveal_hitler]
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