import json
import os

from flask import Flask, request
import telebot
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pprint
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

token = "5750019327:AAE4IbP-65njWFoq09Llr0DxSJSRhBsUOmY"

bot = telebot.TeleBot(token)
server = Flask(__name__)
# Authorize the API
scope = [
    'https://www.googleapis.com/auth/drive',
    'https://www.googleapis.com/auth/drive.file'
]
file_name = 'client_key.json'
creds = ServiceAccountCredentials.from_json_keyfile_name(file_name, scope)
client = gspread.authorize(creds)
def genStartMarkup() :
    markup = InlineKeyboardMarkup()
    markup.row_width = 2
    markup.one_time_keyboard = True
    markup.add(InlineKeyboardButton("Submit Story",callback_data="submitStory"))
    return markup
def genCheckMarkup(story, user):
    markup = InlineKeyboardMarkup()
    markup.row_width = 2
    markup.one_time_keyboard = True
    markup.add(InlineKeyboardButton('Yes', callback_data=json.dumps({"story": story, "user": user})))
    markup.add(InlineKeyboardButton('No', callback_data="submitStoryAgain"))
    return markup
def appendRowToSheet(story, user):
    sheet = client.open('Arts Night Idea Dump').sheet1
    content = sheet.get_all_records()
    nextIndex = len(content) + 2
    newRow = [story, user]
    sheet.insert_row(newRow, nextIndex)

@bot.message_handler(commands=['start'])
def start(message):
    bot.send_message(message.chat.id, "What do you want to do !", reply_markup=genStartMarkup())

@bot.callback_query_handler(func=lambda call: True)
def submitStory(call):
    if call.data == "submitStory":
        print(call)
        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
        bot.send_message(call.message.chat.id, "Whats your story")
        bot.register_next_step_handler_by_chat_id(call.message.chat.id, handle_question)
    elif call.data == "submitStoryAgain":
        bot.send_message(call.message.chat.id, "Ok try again. Whats your story?")
        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
        bot.register_next_step_handler_by_chat_id(call.message.chat.id, handle_question)
    else :
        data = json.loads(call.data)
        bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=None)
        story = data['story']
        user = data['user']
        bot.send_message(call.message.chat.id, "Ok adding story")
        appendRowToSheet(story, user)
        bot.send_message(call.message.chat.id, "Ok story added successfully")


def handle_question(msg):
    # input = msg.json['text']
    user = f"@{msg.from_user.username}"
    input = msg.json['text']

    message = f"""
    The following story will be added:\n\n{input} \n\nDo you confirm ?
    """
    bot.send_message(msg.chat.id, message, reply_markup=genCheckMarkup(input, user))

@server.route('/' + token, methods=["POST"])
def getMessage():
    json_string = request.get_data().decode('utf-8')
    update = telebot.types.Update.de_json(json_string)
    bot.process_new_updates([update])
    return "!", 200


@server.route('/')
def webhook():
    bot.remove_webhook()
    bot.set_webhook(url="https://arts-night-23.herokuapp.com/" + token)
    return "!", 200

# Fetch the sheet

if __name__ == "__main__":
    server.run(host="0.0.0.0", port=int(os.environ.get('PORT', 5000)))
