from flask import Flask, request, abort
import os
from os import environ
from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import *


app = Flask(__name__)

line_bot_api = LineBotApi(environ.get('LINE_BOT_CHANNEL_ACCESS_TOKEN'))

handler = WebhookHandler(environ.get('LINE_BOT_CHANNEL_SECRET'))


WRONG_USER_NAME = "回報時請將三碼學號打在名字前面，再做回報\n範例：001-王大明"


@app.route("/callback", methods=['POST'])
def callback():
    # get X-Line-Signature header value
    signature = request.headers['X-Line-Signature']
    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)
    # handle webhook body
    try:
        handler.handle(body, signature)
    except InvalidSignatureError:
        abort(400)
    return 'OK'


# 處理訊息
@handler.add(MessageEvent, message=TextMessage)
def handle_message(event):
    msg = event.message.text
    profile = get_profile(event)
    display_soldier_name = profile.display_name

    if is_user_name_format_correct(display_soldier_name):
        message_split_parts = msg.split('\n')
        print(message_split_parts)
    else:
        bot_reply_message(event, WRONG_USER_NAME)


def get_profile(event):
    return line_bot_api.get_profile(event.source.user_id)


def bot_reply_message(event, msg):
    message = TextSendMessage(text=str(msg))
    line_bot_api.reply_message(event.reply_token, message)


def is_user_name_format_correct(display_soldier_name):
    soldier_id = display_soldier_name[0:3]
    return soldier_id.isnumeric()


@app.route("/")
def test():
    return "Report bot!"


if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)