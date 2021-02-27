from flask import Flask, request, abort

from linebot import (
    LineBotApi, WebhookHandler
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import *

import os
from datetime import datetime
from models import *
import random
from os import environ

app = Flask(__name__)

static_tmp_path = os.path.join(os.path.dirname(__file__), 'static', 'tmp')

# Channel Access Token
line_bot_api = LineBotApi(environ.get('LINE_BOT_CHANNEL_ACCESS_TOKEN'))

# Channel Secret
handler = WebhookHandler(environ.get('LINE_BOT_CHANNEL_SECRET'))

database_url = environ.get('CLEARDB_DATABASE_URL')

MORNING_REPORT_NUMBER = 1
NIGHT_REPORT_NUMBER = 2
MORNING_BODY_TEMPERATURE_NUMBER = 3
NOON_BODY_TEMPERATURE_NUMBER = 4
NIGHT_BODY_TEMPERATURE_NUMBER = 5

REPORT_CONTENT_ERROR = '回報內容不符合現在回報的格式，請重新回報'
WRONG_REPORT_TIME = '現在不是回報時間\n 上午回報時間:1000-1300\n下午回報時間:1800-2100'
WRONG_USER_NAME = "回報時請將三碼學號打在名字前面，再做回報\n範例：001-王大明"
SERVER_EXCEPTION_PLZ_TRY_AGAIN = '伺服器剛剛恍神，重新回報看看'


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
    soldier_id = display_soldier_name[0:3]
    if is_user_name_format_correct(display_soldier_name):
        message_split_parts = msg.split('\n')

        if is_body_temperature_report_format_correct(message_split_parts[0]):
            handle_body_temperature_report(event, msg, display_soldier_name)
            soldier = get_soldier_by_soldier_id(soldier_id)
            body_temperature_report_type = get_body_temperature_report_type_of_current_time()
            all_report_text = get_text_report_of_body_temperature(body_temperature_report_type, soldier)
            bot_reply_message(event, all_report_text)
        elif is_normal_report_format_correct(message_split_parts[0]):
            if is_morning_report():
                if is_morning_report_content_empty(message_split_parts):
                    handle_morning_report(event, msg, display_soldier_name)
                    soldier = get_soldier_by_soldier_id(soldier_id)
                    all_report_text = get_text_report_of_morning(MORNING_REPORT_NUMBER, soldier)
                    bot_reply_message(event, all_report_text)
                else:
                    bot_reply_message(event, REPORT_CONTENT_ERROR)
            elif is_night_report():
                if is_night_report_content_empty(message_split_parts):
                    handle_night_report(event, msg, display_soldier_name)
                    soldier = get_soldier_by_soldier_id(soldier_id)
                    all_report_text = get_text_report_of_night(NIGHT_REPORT_NUMBER, soldier)
                    bot_reply_message(event, all_report_text)
                else:
                    bot_reply_message(event, REPORT_CONTENT_ERROR)
            else:
                bot_reply_message(event, WRONG_REPORT_TIME)
    else:
        bot_reply_message(event, WRONG_USER_NAME)


def is_morning_report_content_empty(message_split_parts):
    return len(message_split_parts) == 2


def is_night_report_content_empty(message_split_parts):
    return len(message_split_parts) == 3


def is_user_name_format_correct(display_soldier_name):
    soldier_id = display_soldier_name[0:3]
    return soldier_id.isnumeric()


def handle_morning_report(event, msg, display_soldier_name):
    message_split_parts = msg.split('\n')
    soldier_id = display_soldier_name[0:3]
    location = message_split_parts[1]
    body_temperature = ''
    symptom = '無'

    if len(message_split_parts) == 2:
        location = message_split_parts[1]
        body_temperature = generate_random_normal_body_temperature()

    elif len(message_split_parts) == 3:
        if is_text_body_temperature(message_split_parts[2]):
            location = message_split_parts[1]
            body_temperature = message_split_parts[2]
        else:
            location = message_split_parts[1]
            body_temperature = generate_random_normal_body_temperature()
            symptom = message_split_parts[2]
    elif len(message_split_parts) == 4:
        body_temperature = message_split_parts[2]
        symptom = message_split_parts[3]
    start_report(event, MORNING_REPORT_NUMBER, soldier_id, location, None, str(body_temperature), str(symptom))


def handle_body_temperature_report(event, msg, display_soldier_name):
    message_split_parts = msg.split('\n')
    soldier_id = display_soldier_name[0:3]
    body_temperature = ''
    symptom = '無'

    if len(message_split_parts) == 3:
        body_temperature = message_split_parts[1]
        symptom = message_split_parts[2]
    if len(message_split_parts) == 2:
        if is_text_body_temperature(message_split_parts[1]):
            body_temperature = message_split_parts[1]
        else:
            body_temperature = generate_random_normal_body_temperature()
            symptom = message_split_parts[1]
    if len(message_split_parts) == 1:
        body_temperature = generate_random_normal_body_temperature()

    body_temperature_report_type = get_body_temperature_report_type_of_current_time()
    start_report(event, body_temperature_report_type, soldier_id, None, None, str(body_temperature), str(symptom))


def is_text_body_temperature(text):
    try:
        float(text)
        return True
    except ValueError:
        return False


def get_body_temperature_report_type_of_current_time():
    now = datetime.datetime.now()
    now_time = int(now.strftime("%H%M%S"))
    body_temperature_report_type = MORNING_BODY_TEMPERATURE_NUMBER
    if 80000 < now_time < 120000:
        body_temperature_report_type = MORNING_BODY_TEMPERATURE_NUMBER
    elif 120000 <= now_time < 160000:
        body_temperature_report_type = NOON_BODY_TEMPERATURE_NUMBER
    elif 160000 <= now_time < 240000:
        body_temperature_report_type = NIGHT_BODY_TEMPERATURE_NUMBER
    return body_temperature_report_type


def handle_night_report(event, msg, display_soldier_name):
    message_split_parts = msg.split('\n')
    soldier_id = display_soldier_name[0:3]
    location = message_split_parts[1]
    after_ten_location = message_split_parts[2]
    body_temperature = ''
    symptom = '無'

    if len(message_split_parts) == 3:
        body_temperature = generate_random_normal_body_temperature()
    elif len(message_split_parts) == 4:
        if is_text_body_temperature(message_split_parts[3]):
            body_temperature = message_split_parts[3]
        else:
            body_temperature = generate_random_normal_body_temperature()
            symptom = message_split_parts[3]
    elif len(message_split_parts) == 5:
        body_temperature = message_split_parts[3]
        symptom = message_split_parts[4]
    start_report(event, NIGHT_REPORT_NUMBER, soldier_id, location, after_ten_location, str(body_temperature),
                 str(symptom))


def start_report(event, report_type, soldier_id, location, after_ten_location, body_temperature, symptom):
    report_result = report(report_type, soldier_id, location, after_ten_location, str(body_temperature), str(symptom))
    if report_result == REPORT_FAILURE_BY_LOSS_CONNECTION:
        bot_reply_message(event, SERVER_EXCEPTION_PLZ_TRY_AGAIN)


def generate_random_normal_body_temperature():
    body_temperature_text = random.randrange(350, 369, 3)
    return round(int(body_temperature_text) / 10, 2)


def is_normal_report_format_correct(message_first_part):
    return message_first_part == '回報：' or message_first_part == '回報:' or message_first_part == '回報'


def is_body_temperature_report_format_correct(message_first_part):
    return message_first_part == '體溫回報'


def bot_reply_message(event, msg):
    message = TextSendMessage(text=str(msg))
    line_bot_api.reply_message(event.reply_token, message)


def get_profile(event):
    user_id = event.source.user_id
    print(event.source.user_id)
    return line_bot_api.get_profile(user_id)


def is_morning_report():
    now = datetime.datetime.now()
    now_time = int(now.strftime("%H%M%S"))
    return 100000 < now_time < 130000


def is_night_report():
    now = datetime.datetime.now()
    now_time = int(now.strftime("%H%M%S"))
    return 180000 < now_time < 210000


def get_text_report_of_morning(report_type_id, soldier):
    today = datetime.date.today()
    reports_history = get_report_history_by_date_and_report_type_and_class_number(today, report_type_id,
                                                                                  soldier.class_number)
    report_type = get_report_type_by_id(report_type_id)
    report_title = '{report_time_period}{type_name}\n\n'.format(report_time_period=report_type.report_time_period,
                                                                type_name=report_type.type_name)
    all_report_text = ''
    for report in reports_history:
        personal_report_text = "姓名：{name}\n" \
                               "學號：{soldier_id}\n" \
                               "手機：{phone}\n" \
                               "地點：{location}\n\n".format(name=report.soldier.name,
                                                          soldier_id=report.soldier.soldier_id,
                                                          phone=report.soldier.phone,
                                                          location=report.location)
        all_report_text += personal_report_text
    return report_title + all_report_text


def get_text_report_of_night(report_type_id, soldier):
    today = datetime.date.today()
    reports_history = get_report_history_by_date_and_report_type_and_class_number(today, report_type_id,
                                                                                  soldier.class_number)
    report_type = get_report_type_by_id(report_type_id)
    report_title = '{report_time_period}{type_name}\n\n'.format(report_time_period=report_type.report_time_period,
                                                                type_name=report_type.type_name)
    all_report_text = ''
    for report in reports_history:
        personal_report_text = "姓名：{name}\n" \
                               "學號：{soldier_id}\n" \
                               "手機：{phone}\n" \
                               "地點：{location}\n" \
                               "2200後地點：{location_after_ten}\n\n".format(name=report.soldier.name,
                                                                         soldier_id=report.soldier.soldier_id,
                                                                         phone=report.soldier.phone,
                                                                         location=report.location,
                                                                         location_after_ten=report.location_after_ten)
        all_report_text += personal_report_text
    return report_title + all_report_text


def get_text_report_of_general_and_body_temperature(report_type_id, soldier):
    today = datetime.date.today()
    reports_history = get_report_history_by_date_and_report_type_and_class_number(today, report_type_id,
                                                                                  soldier.class_number)
    report_type = get_report_type_by_id(report_type_id)
    report_title = '{report_time_period}{type_name}\n\n'.format(report_time_period=report_type.report_time_period,
                                                                type_name=report_type.type_name)
    all_report_text = ''
    for report in reports_history:
        personal_report_text = "姓名：{name}\n" \
                               "學號：{soldier_id}\n" \
                               "手機：{phone}\n" \
                               "地點：{location}\n" \
                               "體溫：{body_temperature}\n" \
                               "症狀：{symptom}\n\n".format(name=report.soldier.name,
                                                         soldier_id=report.soldier.soldier_id,
                                                         phone=report.soldier.phone,
                                                         location=report.location,
                                                         body_temperature=report.body_temperature,
                                                         symptom=report.symptom)
        all_report_text += personal_report_text
    return report_title + all_report_text


def get_text_report_of_body_temperature(report_type_id, soldier):
    today = datetime.date.today()
    reports_history = get_report_history_by_date_and_report_type_and_class_number(today, report_type_id,
                                                                                  soldier.class_number)
    report_type = get_report_type_by_id(report_type_id)
    report_title = '{date}\t{report_time_period}\t{type_name}\n\n'.format(date=today.strftime('%m/%d'),
                                                                          report_time_period=report_type.report_time_period,
                                                                          type_name=report_type.type_name)
    all_report_text = ''
    for report in reports_history:
        simple_soldier_id = report.soldier.soldier_id[2:5]
        personal_report_text = "{soldier_id}{name}\n" \
                               "體溫：{body_temperature}\n" \
                               "症狀：{symptom}\n\n".format(soldier_id=simple_soldier_id,
                                                         name=report.soldier.name,
                                                         body_temperature=report.body_temperature,
                                                         symptom=report.symptom)
        all_report_text += personal_report_text
    return report_title + all_report_text


def log_for_heroku(message):
    print(message)


@app.route("/")
def test():
    return "Report bot!"


if __name__ == "__main__":
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
