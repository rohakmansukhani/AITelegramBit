import os
import telegram
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, MessageHandler, Filters, CallbackQueryHandler
from Bard import Chatbot
import logging

from link_handler import get_related_links

# Set up Telegram bot and Bard API
TELEGRAM_TOKEN = os.environ['TELEGRAM_TOKEN']
BARD_TOKEN = os.environ['BARD_TOKEN']
bot = telegram.Bot(token=TELEGRAM_TOKEN)
chatbot = Chatbot(BARD_TOKEN)

# Define the message handler function
def message_handler(update, context):
    # Save the user's message for later use
    context.user_data['user_message'] = update.message.text

    # Ask the user if they want a full or short response
    keyboard = [
        [InlineKeyboardButton("Full response", callback_data='full')],
        [InlineKeyboardButton("Short response", callback_data='short')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    bot.send_message(chat_id=update.effective_chat.id, text="Do you want a full or short response?", reply_markup=reply_markup)

def callback_handler(update, context):
    # Get the user's choice from the callback query
    query = update.callback_query
    choice = query.data

    # Get the user's message from the context
    user_message = context.user_data.get('user_message', '')

    # Call the Bard API to get a response
    response = None
    if choice == 'full':
        response = chatbot.ask(user_message)
    elif choice == 'short':
        response = chatbot.ask(user_message)
        response['content'] = ' '.join(response['content'].split()[:32])

    # Send the response back to the user
    if response:
        bot.send_message(chat_id=query.message.chat_id, text=response['content'])
    else:
        bot.send_message(chat_id=query.message.chat_id, text="Sorry, I couldn't understand your message. Please try again.")

    # Ask the user if they want related links
    if choice == 'full' or choice == 'short':
        keyboard = [
            [InlineKeyboardButton("Yes", callback_data='links')],
            [InlineKeyboardButton("No", callback_data='no_links')]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        bot.send_message(chat_id=query.message.chat_id, text="Do you want related links?", reply_markup=reply_markup)

        # Save the response for later use
        context.user_data['response'] = response
    elif choice == 'links':
        # Get the related links
        links = get_related_links(user_message)

        # Send the related links to the user
        if links:
            bot.send_message(chat_id=query.message.chat_id, text=links)
        else:
            bot.send_message(chat_id=query.message.chat_id, text="Sorry, I couldn't find any related links.")


def link_callback_handler(update, context):
    # Get the user's choice from the callback query
    query = update.callback_query
    choice = query.data

    # Get the response from the context
    response = context.user_data.get('response', None)

    # Get the related links
    links = None
    if choice == 'links':
        links = get_related_links(response['content'])

    # Send the related links to the user
    if links:
        bot.send_message(chat_id=query.message.chat_id, text=links)
    else:
        bot.send_message(chat_id=query.message.chat_id, text="Sorry, I couldn't find any related links.")

# Set up the message handler with the bot
updater = Updater(token=TELEGRAM_TOKEN, use_context=True)
dispatcher = updater.dispatcher
dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, message_handler))
dispatcher.add_handler(CallbackQueryHandler(callback_handler))
dispatcher.add_handler(CallbackQueryHandler(link_callback_handler, pattern='^links$'))

# Define a logger
logger = logging.getLogger(__name__)

# Error handling
def error_handler(update, context):
    """Log the error and send a message to the user"""
    logger.error(f"Update {update} caused error {context.error}")

    # Send an error message to the user
    bot.send_message(chat_id=update.effective_chat.id, text="Sorry, something went wrong. Please try again later.")
# Start the bot
updater.start_polling()
updater.idle()
