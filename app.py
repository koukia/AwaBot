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
    ImageSendMessage, LocationMessage,
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
            try:
                pos = userLocDict[str(user_id)].split(',')
                lng = pos[0]
                lat = pos[1]
            except KeyError:
                #post_text(event.reply_token, '+ から位置情報を送ってね')
                #break
                lng = 134.398391
                lat = 34.122109

            if re.search('.*=0',event.postback.data):
                result = get_tourist_spot(lng, lat)
                post_tourist_spot_carousel(event.reply_token, result)
            elif re.search('.*=1',event.postback.data):
                result = get_hotel(lng, lat)
                #print(result)
            elif re.search('.*=2',event.postback.data):
                result = get_wifi_spot(lng, lat)
                #result = get_wifi_spot(lng, lat)
                #print(result)

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
    if user_id not in userLocDict:
        post_text(event.reply_token, '+ から位置情報を送ってね')
        return None
    else:
        post_kind(event.reply_token)

    received_text = event.message.text
    if re.search('観光地', received_text):
        try:
            result = get_tourist_spot()
            post_tourist_spot_carousel(event.reply_token, result)
        except Exception as e:
            print(e)
    elif re.search('ホテル', received_text):
        try:
            post_carousel(event.reply_token)
        except Exception as e:
            print(e)
    elif re.search('Wi-Fi', received_text):
        post_text(event.reply_token, 'Wi-Fi')
    #elif re.search('タクシー', received_text):
    #    post_text(event.reply_token, 'taxi')

    else:
        post_text(event.reply_token, received_text)

def post_text(token, text):
    line_bot_api.reply_message(
        token,
        TextSendMessage(text=text)
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
                            "type" :"postback",
                            "label":"観光地",
                            "data" :"action=0"
                        },
                        {
                            "type" : "postback",
                            "label": "ホテル",
                            "data" : "action=1"
                        },
                        {
                            "type" : "postback",
                            "label": "Wi-Fiスポット",
                            "data"  : "action=2"
                        }
                    ]
                }
            }
        ]
    }
    print(payload)
    REPLY_ENDPOINT = 'https://api.line.me/v2/bot/message/reply'
    HEADER = {
        "Content-Type": "application/json",
        "Authorization": "Bearer "+channel_access_token
    }
    requests.post(REPLY_ENDPOINT, headers=HEADER, data=json.dumps(payload))

def get_tourist_spot_columns(places):
    columns = []
    for place in places:
        print("https://maps.google.co.jp/maps?q="+str(place['lat'])+","+str(place['lng']))
        print("http://google.com/search?q="+str(place['name']))
        columns.append({
                "title": place['name'],
                "text" : place['address'],
                "actions": [
                    {
                        "type": "uri",
                        "label": "マップ",
                        "uri": "https://maps.google.co.jp/maps?q="+str(place['lat'])+","+str(place['lng'])
                    },
                    {
                        "type": "uri",
                        "label": "詳しく",
                        "uri": "http://google.com/search?q="+str(place['name'])
                    }
                ]
            })
    return columns

def post_tourist_spot_carousel(token, place_list):
    payload = {
        "replyToken":token,
        "messages":[
            {
                "type" :"template",
                "altText" :"tourist spots",
                "template" :{
                    "type" :"carousel",
                    "columns" :get_tourist_spot_columns(place_list)
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

def post_carousel(token):
    payload = {
        "replyToken":token,
        "messages":[
            {
                "type"    :"template",
                "altText" :"this is template",
                "template":{
                    "type"   :"carousel",
                    "columns":[
                        {
                           # "thumbnailImageUrl": host_name+"/img-sam/01.jpg",
                            "title":"徳島グランドホテル偕楽園",
                            "text" :"徳島市伊賀町1丁目8",
                            "actions":[
                                {
                                    "type" :"postback",
                                    "label":"電話",
                                    "data" :"action=add&itemid=1"
                                },
                                {
                                    "type" : "postback",
                                    "label": "マップ",
                                    "data" : "action=add&itemid=111"
                                },
                                {
                                    "type" : "uri",
                                    "label": "詳しく",
                                    "uri"  : "http://google.com/search?q="+"徳島グランドホテル偕楽園"
                                }
                            ]
                        },
                        {
                           # "thumbnailImageUrl": host_name+"/img-sam/02.jpg",
                            "title":"this is menu",
                            "text" :"description",
                            "actions":[
                                {
                                    "type" :"postback",
                                    "label":"buy",
                                    "data" :"action=add&itemid=1"
                                },
                                {
                                    "type" : "postback",
                                    "label": "Add to cart",
                                    "data" : "action=add&itemid=111"
                                },
                                {
                                    "type" : "uri",
                                    "label": "View detail",
                                    "uri"  : "http://google.com"
                                }
                            ]
                        }
                    ]
                }
            }
        ]
    }
    '''
    payload = {
        "replyToken":token,
            "messages":[
                {
                    "type":"text",
                    "text": 'abc'
                }
            ]    
    }'''
    print('-----\n')
    print(payload)
    print('-----\n')
    REPLY_ENDPOINT = 'https://api.line.me/v2/bot/message/reply'
    HEADER = {
        "Content-Type": "application/json",
        "Authorization": "Bearer " +channel_access_token
    }
    requests.post(REPLY_ENDPOINT, headers=HEADER,data=json.dumps(payload)) # LINEにデータを送信   

if __name__ == "__main__":
    arg_parser = ArgumentParser(
        usage='Usage: python ' + __file__ + ' [--port <port>] [--help]'
    )
    arg_parser.add_argument('-p', '--port', default=8000, help='port')
    arg_parser.add_argument('-d', '--debug', default=False, help='debug')
    options = arg_parser.parse_args()

    app.run(debug=options.debug, port=options.port)
