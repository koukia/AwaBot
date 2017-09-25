# -*- coding: utf-8 -*-

from __future__ import unicode_literals

import os
import sys
from argparse import ArgumentParser

from flask import Flask, request, abort, send_from_directory
from linebot import (
    LineBotApi, WebhookParser
)
from linebot.exceptions import (
    InvalidSignatureError
)
from linebot.models import (
    MessageEvent, TextMessage, TextSendMessage,
    ImageSendMessage, LocationSendMessage, LocationMessage,
    SourceUser, PostbackEvent, 
)

import re
from datetime import datetime
from datetime import timedelta
import time
import requests
import json

from tokushima_opendata.tourist_spot import get_tourist_spot
from tokushima_opendata.tourist_spot import get_hotel
from tokushima_opendata.tourist_spot import get_wifi_spot

app = Flask(__name__)

channel_access_token = os.getenv('LINE_CHANNEL_ACCESS_TOKEN', None)
channel_secret = os.getenv('LINE_CHANNEL_SECRET', None)

host_name = 'https://nameless-gorge-55138.herokuapp.com'
host_name = 'https://162c3259.ngrok.io'

if channel_secret is None:
    print('Specify LINE_CHANNEL_SECRET as environment variable.')
    sys.exit(1)
if channel_access_token is None:
    print('Specify LINE_CHANNEL_ACCESS_TOKEN as environment variable.')
    sys.exit(1)

line_bot_api = LineBotApi(channel_access_token)
parser = WebhookParser(channel_secret)

userLocDict = {}
_DEBUG = True
_DUMMY_POS = '134.398391,34.122109'

@app.route('/img-sam/<path:filename>')
def image(filename):
    return send_from_directory('img', filename)


@app.route('/tmp/<path:filename>')
def csv(filename):  
    return send_from_directory('tmp', filename)


@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)
    
    try:
        events = parser.parse(body, signature)
    except InvalidSignatureError:
        abort(400)

    #print(events)
    for event in events:
        user_id = event.source.sender_id

        if isinstance(event, PostbackEvent):
            #print(str(event.postback.data))
            if re.search('action=loc', event.postback.data):
                name = event.postback.data.split('&')[1].split('=')[1]
                address = event.postback.data.split('&')[2].split('=')[1]
                lng = event.postback.data.split('&')[3].split('=')[1]
                lat = event.postback.data.split('&')[4].split('=')[1]
                #print(address)
                post_location(event.reply_token, title=name, address=address, latitude=lat,longitude=lng)

            if re.search('action=detail', event.postback.data):
                name = event.postback.data.split('&')[1].split('=')[1]
                #print(name)
                post_text(event.reply_token, "https://google.co.jp/search?q="+name)

        # FollowEvent, JoinEvent の処理はしない
        if not isinstance(event, MessageEvent):
            continue
        
        if isinstance(event.message, TextMessage):
            receiveText(event)
        
        if isinstance(event.message, LocationMessage):
            lng = event.message.longitude
            lat = event.message.latitude
            pos = str(lng)+','+str(lat)
            #print(pos)
            userLocDict[str(user_id)] = pos
            #print(userLocDict)
            post_kind(event.reply_token)

    return 'OK'

def receiveText(event):
    user_id = event.source.sender_id
    received_text = event.message.text
    if user_id not in userLocDict and _DEBUG:
        userLocDict[user_id] = _DUMMY_POS

    if user_id in userLocDict:
        pos = userLocDict[str(user_id)].split(',')
        lng = pos[0]
        lat = pos[1]
    else:
        print("位置情報がありません")

    if re.search('案内', received_text):
        if user_id not in userLocDict:
            post_text(event.reply_token, '+ から位置情報を送ってね')
            return 'no location data'
        post_kind(event.reply_token)

    elif re.search('観光地', received_text):
        if user_id not in userLocDict:
            post_text(event.reply_token, '+ から位置情報を送ってね')
            return 'no location data'
        try:
            result = get_tourist_spot(lng, lat)
            post_spot_carousel('tour', event.reply_token, result)
        except Exception as e:
            print(e)
    elif re.search('ホテル', received_text):
        try:
            result = get_hotel(lng, lat)
            print(result)
            post_spot_carousel('hotel', event.reply_token, result)
        except Exception as e:
            print(e)
    elif re.search('Wi-Fi', received_text) or re.search('WiFi', received_text):
        result = get_wifi_spot(lng, lat)
        print(result)
        post_spot_carousel('wifi',event.reply_token, result)

    else:
        post_text(event.reply_token, received_text)

def post_text(token, text):
    line_bot_api.reply_message(
        token,
        TextSendMessage(text=text)
    )

def post_location(token, title=None, address=None, latitude=None, longitude=None):
    location_message = LocationSendMessage(
        title=title,
        address=address,
        latitude=latitude,
        longitude=longitude,
    )
    line_bot_api.reply_message(
        token,
        location_message
    )

def post_image(token, image_path):
    image_message = ImageSendMessage(
        original_content_url = image_path,
        preview_image_url = image_path
    )
    line_bot_api.reply_message(
        token,
        image_message
    )

def post_kind(token):
    payload = {
        "replyToken":token,
        "messages":[
            {
                "type"    :"template",
                "altText" :"select destination",
                "template":{
                    "type"   :"buttons",
                    "text"  :"どこに行きたいですか？",
                    #"title"   :"行先を選択してください",
                    "actions":[
                        {
                            "type" :"message",
                            "label":"観光地",
                            "text" :"観光地を教えて"
                        },
                        {
                            "type" : "message",
                            "label": "ホテル",
                            "text" : "ホテルを教えて"
                        },
                        {
                            "type" : "message",
                            "label": "Wi-Fiスポット",
                            "text"  : "Wi-Fiスポットを教えて"
                        }
                    ]
                }
            }
        ]
    }
    #print(payload)
    REPLY_ENDPOINT = 'https://api.line.me/v2/bot/message/reply'
    HEADER = {
        "Content-Type": "application/json",
        "Authorization": "Bearer "+channel_access_token
    }
    requests.post(REPLY_ENDPOINT, headers=HEADER, data=json.dumps(payload))

def post_spot_carousel(kind, token, place_list):
    if kind is 'tour':
        columns = get_tourist_spot_columns(place_list)
    elif kind is 'hotel':
        columns = get_hotel_columns(place_list)
    elif kind is 'wifi':
        columns = get_wifi_spot_columns(place_list)

    payload = {
        "replyToken":token,
        "messages":[
            {
                "type" :"template",
                "altText" :"this is template",
                "template" :{
                    "type" :"carousel",
                    "columns" :columns
                }
            }
        ]
    }

    REPLY_ENDPOINT = 'https://api.line.me/v2/bot/message/reply'
    HEADER = {
        "Content-Type": "application/json",
        "Authorization": "Bearer " +channel_access_token
    }
    requests.post(REPLY_ENDPOINT, headers=HEADER,data=json.dumps(payload))

def get_tourist_spot_columns(places):
    columns = []
    for place in places:
        #print("https://maps.google.co.jp/maps?q="+str(place['lat'])+","+str(place['lng']))
        #print("http://google.com/search?q="+str(place['name']))
        columns.append({
                "title": place['name'],
                "text" : place['address'],
                "actions": [
                    {
                        "type" : "postback",
                        "label": "位置情報",
                        "data" : "action=loc&name="+place['name']+"&address="+place['address']+"&lng="+str(place['lng'])+"&lat="+str(place['lat']),
                    },
                    {
                        "type" : "postback",
                        #"type": "uri",
                        "label": "詳しく",
                        #"uri":"https://google.co.jp/search?q="+place['name']
                        "data" : "action=detail&name="+place['name'],
                    }
                ]
            })
    return columns

def get_hotel_columns(places):
    columns = []
    exitst_hp = True
    for place in places:
        if str(place['url']) is 'nan':
            exitst_hp = False
            break

    for place in places:
        print(str(place['url']))
        actions = [
            {
                "type": "postback",
                "label": "位置情報",
                "data": "action=loc&name=" + place['name'] + "&address=" + place['address'] + "&lng=" + str(
                    place['lng']) + "&lat=" + str(place['lat']),
            },{
                "type": "uri",
                "label": "電話",
                "uri":str("tel:"+place['tel'])
            }
        ]
        if exitst_hp:
            actions.append({
                "type": "uri",
                "label": "ホームページ",
                "uri": str(place['url'])
            })

        columns.append({
            "title": place['name'],
            "text": place['address'],
            "actions": actions
        })
    return columns

def get_wifi_spot_columns(places):
    columns = []
    for place in places:
        columns.append({
            "title": place['name'],
            "text": place['address'],
            "actions": [
                {
                    "type": "postback",
                    "label": "位置情報",
                    "data": "action=loc&name=" + place['name'] + "&address=" + place['address'] + "&lng=" + str(
                        place['lng']) + "&lat=" + str(place['lat']),
                }
            ]
        })
    return columns

if __name__ == "__main__":
    arg_parser = ArgumentParser(
        usage='Usage: python ' + __file__ + ' [--port <port>] [--help]'
    )
    arg_parser.add_argument('-p', '--port', default=8000, help='port')
    arg_parser.add_argument('-d', '--debug', default=False, help='debug')
    options = arg_parser.parse_args()
    app.run(debug=options.debug, port=options.port)
