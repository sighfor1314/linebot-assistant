from __future__ import unicode_literals
import os
import parser
from hashlib import sha1
import hmac
from wsgiref.handlers import format_date_time
from datetime import datetime
import time
import base64
import requests
import json
from flask import Flask, request, abort
from linebot import LineBotApi, WebhookHandler
from linebot.exceptions import InvalidSignatureError, LineBotApiError
from linebot.models import MessageEvent, TextMessage, TextSendMessage, UnfollowEvent, FollowEvent, ImageMessage, \
    LocationMessage, ImageSendMessage, TemplateSendMessage, ButtonsTemplate, MessageImagemapAction, ImagemapArea, \
    MessageTemplateAction, URITemplateAction, ConfirmTemplate, CarouselTemplate, CarouselColumn, URIAction
from pathlib import Path
import configparser

app = Flask(__name__)

# LINE 聊天機器人的基本資料
config = configparser.ConfigParser()
config.read('config.ini')

line_bot_api = LineBotApi(config.get('line-bot', 'channel_access_token'))
handler = WebhookHandler(config.get('line-bot', 'channel_secret'))
app_id = config.get('Transportation', 'app_id')
app_key = config.get('Transportation', 'app_key')


class Auth():

    def __init__(self, app_id, app_key):
        self.app_id = app_id
        self.app_key = app_key

    def get_auth_header(self):
        xdate = format_date_time(time.mktime(datetime.now().timetuple()))
        hashed = hmac.new(self.app_key.encode('utf8'), ('x-date: ' + xdate).encode('utf8'), sha1)
        signature = base64.b64encode(hashed.digest()).decode()

        authorization = 'hmac username="' + self.app_id + '", ' + \
                        'algorithm="hmac-sha1", ' + \
                        'headers="x-date", ' + \
                        'signature="' + signature + '"'
        return {
            'Authorization': authorization,
            'x-date': format_date_time(time.mktime(datetime.now().timetuple())),
            'Accept - Encoding': 'gzip'
        }


# 接收 LINE 的資訊
@app.route("/api/line", methods=['POST'])
def callback():
    # 驗證token是不是line
    signature = request.headers['X-Line-Signature']

    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    try:
        print(body, signature)
        handler.handle(body, signature)

    except InvalidSignatureError:
        abort(400)

    return 'OK'


def get_answer(message_text):
    url = config.get('QnAMaker', 'url')
    # 發送request到QnAMaker Endpoint要答案
    response = requests.post(
        url,
        json.dumps({'question': message_text}),
        headers={
            'Content-Type': 'application/json',
            'Authorization': config.get('QnAMaker', 'authorization')
        }
    )

    data = response.json()
    try:
        # 我們使用免費service可能會超過限制（一秒可以發的request數）
        if "error" in data:
            return data["error"]["message"]
        # 這裡我們預設取第一個答案
        answer = data['answers'][0]['answer']
        return answer
    except Exception:
        return "Error occurs when finding answer"


@handler.add(MessageEvent, message=TextMessage)
def search＿result(event):
    msg = event.message.text
    if msg == '@使用說明':
        line_bot_api.reply_message(event.reply_token, TextSendMessage("查詢格式為: 天氣 <縣  市>\n" +
                                                                      "範例: 天氣 桃園市\n" +
                                                                      "========================\n" +
                                                                      "查詢格式為: 火車 <日期> <起站> <迄站> <起始時間> <截止時間>\n" +
                                                                      "範例: 火車 3/7 台北 中壢 08:00 21:00"))

    elif msg == '哈囉':
        line_bot_api.reply_message(event.reply_token, TextSendMessage(msg + '小白測試中'))

    elif msg == '小白':
        im = ImageSendMessage(
            original_content_url="https://via.placeholder.com/300.png/09f/fff",
            preview_image_url="https://via.placeholder.com/300/09f/fff.png"
        )

        line_bot_api.reply_message(event.reply_token, im)

    elif msg[:2] == '天氣':

        cities = ['基隆市', '嘉義市', '臺北市', '嘉義縣', '新北市', '臺南市', '桃園市', '高雄市', '新竹市', '屏東縣', '新竹縣', '臺東縣', '苗栗縣', '花蓮縣',
                  '臺中市', '宜蘭縣', '彰化縣', '澎湖縣', '南投縣', '金門縣', '雲林縣', '連江縣']

        city = msg[3:]
        city = city.replace('台', '臺')
        if city in cities:
            url = 'https://opendata.cwb.gov.tw/api/v1/rest/datastore/F-C0032-001'
            params = {
                "Authorization": config.get('Weather', 'authorization'),
                "locationName": city,
            }
            Data = requests.get(url, params=params)
            Data = json.loads(Data.text)
            weather_elements = Data["records"]["location"][0]["weatherElement"]

            line_bot_api.reply_message(event.reply_token, TextSendMessage(text= \
                                                                              '縣市：' + Data["records"]["location"][0][
                                                                                  "locationName"] + '\n' +
                                                                              '開始時間：' + weather_elements[0]["time"][0][
                                                                                  "startTime"] + '\n' +
                                                                              '結束時間：' + weather_elements[0]["time"][0][
                                                                                  "endTime"] + '\n' +
                                                                              '天氣：' + weather_elements[0]["time"][0][
                                                                                  "parameter"]["parameterName"] + '\n' +
                                                                              '降雨機率：' + weather_elements[1]["time"][0][
                                                                                  "parameter"]["parameterName"] + '\n' +
                                                                              '最低溫度：' + weather_elements[2]["time"][0][
                                                                                  "parameter"]["parameterName"] + '\n' +
                                                                              '最高溫度：' + weather_elements[4]["time"][0][
                                                                                  "parameter"]["parameterName"] + '\n' +
                                                                              '舒適度：' + weather_elements[3]["time"][0][
                                                                                  "parameter"]["parameterName"] + '\n'
                                                                          ))
        else:
            line_bot_api.reply_message(event.reply_token, TextSendMessage(text="查詢格式為: 天氣 縣市"))


    elif msg[:2] == '火車':

        a = Auth(app_id, app_key)
        with open('trainTable.json') as f:
            data = json.load(f)
        station = data['Stations']
        station_ID = {}
        for i in range(len(station)):
            station_ID[station[i]['StationName']['Zh_tw']] = station[i]['StationID']
        parameter = msg.split(' ')

        if len(parameter) == 4:
            parameter.append('00:00')
            parameter.append('23:59')

        # nowTime = int(time.time())  # 取得現在時間   #有問題
        # struct_time = time.localtime(nowTime)  # 轉換成時間元組 #有問題
        # timeString = time.strftime("%Y ", struct_time)  # 將時間元組轉換成想要的字串 ＃有問題

        parameter[1] = '2022' + '/' + parameter[1]
        date = str(datetime.strptime(parameter[1], "%Y/%m/%d"))[:-9]
        parameter[2] = parameter[2].replace('台', '臺')
        parameter[3] = parameter[3].replace('台', '臺')

        start_station = station_ID[parameter[2]]
        destination_station = station_ID[parameter[3]]

        response = requests.get(
            'https://ptx.transportdata.tw/MOTC/v2/Rail/TRA/DailyTimetable/OD/' + start_station + '/to/' + destination_station + '/' + date + '?%24format=JSON',
            headers=a.get_auth_header())
        data = json.loads(response.text)

        start_time = datetime.strptime(parameter[4], "%M:%S")
        end_time = datetime.strptime(parameter[5], "%M:%S")

        result = parameter[2] + ' 到 ' + parameter[3] + '\n'

        for i in range(len(data)):
            origin_stopTime = data[i]['OriginStopTime']['DepartureTime']
            destination_stopTime = data[i]['DestinationStopTime']['ArrivalTime']
            car_name = data[i]['DailyTrainInfo']['TrainTypeName']['Zh_tw']

            if start_time <= datetime.strptime(origin_stopTime, "%M:%S") and datetime.strptime(origin_stopTime,
                                                                                               "%M:%S") <= end_time:
                diff_time = str(
                    datetime.strptime(destination_stopTime, "%M:%S") - datetime.strptime(origin_stopTime, "%M:%S"))
                if '(' in car_name:
                    car_name = car_name[:2]

                s = car_name + '  ' + origin_stopTime + '  ' + destination_stopTime + '  ' + diff_time[2:]
                result += '\n' + s
        line_bot_api.reply_message(event.reply_token, TextSendMessage(text=result))

    else:
        answer = get_answer(event.message.text)
        line_bot_api.reply_message(event.event.reply_token, TextSendMessage(text=answer))


@handler.add(event=FollowEvent)
def followEvent(event):
    print(event)
    profile = line_bot_api.get_profile(event.source.user_id)
    print(profile.user_id)
    print(profile.display_name)
    line_bot_api.reply_message(event.reply_token,
                               TextSendMessage('哈齁，' + profile.display_name)
                               )


@handler.add(event=UnfollowEvent)
def unfollowEvent(event):
    print(event.source.user_id)


@handler.add(event=MessageEvent, message=ImageMessage)
def pretty(event):
    msg_id = event.message.id
    msg_content = line_bot_api.get_message_content(msg_id)
    with open(Path(f"images/{msg_id}.jpg" or "images/{msg_id}.pgn").absolute(), "wb") as f:
        for chunk in msg_content.iter_content():
            f.write(chunk)
    line_bot_api.reply_message(event.reply_token, TextSendMessage('傳圖片呢'))


@handler.add(event=MessageEvent, message=LocationMessage)
def location(event):
    print(event)
    print(event.message.latitude)
    print(event.message.longitude)
    line_bot_api.reply_message(event.reply_token, TextSendMessage('傳位址呢'))


if __name__ == "__main__":
    app.run()
