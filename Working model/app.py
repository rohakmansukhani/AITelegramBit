import os
import telegram
from Bard import Chatbot
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, MessageHandler, Filters, CallbackQueryHandler

# Set up Telegram bot and Bard API
TELEGRAM_TOKEN = os.environ['TELEGRAM_TOKEN']
BARD_TOKEN = os.environ['BARD_TOKEN']
bot = telegram.Bot(token=TELEGRAM_TOKEN)
chatbot = Chatbot(BARD_TOKEN)

# Define the message handler function
def message_handler(update, context):
    # Ask the user if they want a full or short response
    keyboard = [
        [InlineKeyboardButton("Full response", callback_data='full')],
        [InlineKeyboardButton("Short response", callback_data='short')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    bot.send_message(chat_id=update.effective_chat.id, text="Do you want a full or short response?", reply_markup=reply_markup)

    # Save the user's message for later use
    context.user_data['user_message'] = update.message.text

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
    bot.send_message(chat_id=query.message.chat_id, text=response['content'])

# Set up the message handler with the bot
updater = Updater(token=TELEGRAM_TOKEN, use_context=True)
dispatcher = updater.dispatcher
dispatcher.add_handler(MessageHandler(Filters.text & ~Filters.command, message_handler))
dispatcher.add_handler(CallbackQueryHandler(callback_handler))

# Start the bot
updater.start_polling()
updater.idle()
