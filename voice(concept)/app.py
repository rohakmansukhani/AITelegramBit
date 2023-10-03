import io
import os
import requests
import logging
from pydub import AudioSegment
# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

import telegram
import speech_recognition as sr
from Bard import Chatbot
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackQueryHandler

# Set up Telegram bot and Bard API
TELEGRAM_TOKEN = os.environ['TELEGRAM_TOKEN']
BARD_TOKEN = os.environ['BARD_TOKEN']
bot = telegram.Bot(token=TELEGRAM_TOKEN)
chatbot = Chatbot(BARD_TOKEN)

# Define the command handler function for starting the bot
def start_handler(update, context):
    bot.send_message(chat_id=update.effective_chat.id, text="Hello! I am a chatbot. Please send me a message or a voice recording.")

# Define the message handler function for text messages
def text_handler(update, context):
    # Get the user's message from the update
    user_message = update.message.text

    # Call the Bard API to get a response
    response = chatbot.ask(user_message)

    # Send the response back to the user as a text message with a button
    keyboard = [
        [InlineKeyboardButton("Full response", callback_data='full')],
        [InlineKeyboardButton("Short response", callback_data='short')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    bot.send_message(chat_id=update.effective_chat.id, text=response['content'], reply_markup=reply_markup)

    # Store the user's message in the context for later use
    context.user_data['user_message'] = user_message

# Define the callback handler function for button presses
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

    # Send the response back to the user with a new set of buttons
    keyboard = [
        [InlineKeyboardButton("Full response", callback_data='full')],
        [InlineKeyboardButton("Short response", callback_data='short')],
        [InlineKeyboardButton("No thanks, I'm done", callback_data='done')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if response is None:
        bot.send_message(chat_id=query.message.chat_id, text="Sorry, there was an error processing your request.", reply_markup=reply_markup)
    else:
        content = response.get('content', '')
        bot.send_message(chat_id=query.message.chat_id, text=content, reply_markup=reply_markup)

# Define the message handler function for voice messages
def voice_handler(update, context):
    # Check if the message is an audio message
    if not update.message.voice:
        bot.send_message(chat_id=update.effective_chat.id, text="Please send me your message as a voice recording.")
        return

    # Download the audio file
    file = bot.get_file(update.message.voice.file_id)
    file_path = file.file_path
    audio_file = requests.get(file_path)

    # Convert the audio file to a format that speech_recognition can handle
    audio = AudioSegment.from_file(io.BytesIO(audio_file.content), format='ogg')
    audio = audio.set_frame_rate(16000).set_channels(1)
    audio_bytes = audio.export(format='wav').read()

    # Use speech recognition to convert the audio file to text
    r = sr.Recognizer()
    with sr.AudioFile(io.BytesIO(audio_bytes)) as source:
        audio = r.record(source)

    # Use the Google speech recognition API to convert audio to text
    try:
        user_message = r.recognize_google(audio)
    except sr.UnknownValueError:
        bot.send_message(chat_id=update.effective_chat.id, text="Sorry, I could not understand what you said.")
        return
    except sr.RequestError as e:
        bot.send_message(chat_id=update.effective_chat.id, text="Sorry, could not process your request. Please try again later.")
        return

    # Call the chatbot API to get a response
    response = chatbot.ask(user_message)

    # Send the response back to the user as a text message with a button
    keyboard = [
        [InlineKeyboardButton("Full response", callback_data='full')],
        [InlineKeyboardButton("Short response", callback_data='short')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    bot.send_message(chat_id=update.effective_chat.id, text=response['content'], reply_markup=reply_markup)

# Define the error handler function
def error_handler(update, context):
    """Log the error and send a message to the user."""
    logger.error(msg="Exception while handling an update:", exc_info=context.error)
    bot.send_message(chat_id=update.effective_chat.id, text="Sorry, there was an error processing your request.")

# Set up the Telegram bot updater with the command and message handlers
updater = Updater(token=TELEGRAM_TOKEN, use_context=True)
dispatcher = updater.dispatcher
dispatcher.add_handler(CommandHandler('start', start_handler))
dispatcher.add_handler(MessageHandler(Filters.text, text_handler))
dispatcher.add_handler(MessageHandler(Filters.voice, voice_handler))
dispatcher.add_handler(CallbackQueryHandler(callback_handler))
dispatcher.add_error_handler(error_handler)

# Start the bot
updater.start_polling()
updater.idle()