# -*- coding: utf-8 -*-

#  Licensed under the Apache License, Version 2.0 (the "License"); you may
#  not use this file except in compliance with the License. You may obtain
#  a copy of the License at
#
#       https://www.apache.org/licenses/LICENSE-2.0
#
#  Unless required by applicable law or agreed to in writing, software
#  distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#  WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#  License for the specific language governing permissions and limitations
#  under the License.

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
    ImageSendMessage
)
#added
import re
from datetime import datetime
from datetime import timedelta
import time

import image
from io import StringIO

import requests
import json

app = Flask(__name__)

# get channel_secret and channel_access_token from your environment variable
channel_secret = os.getenv('LINE_CHANNEL_SECRET', None)
channel_access_token = os.getenv('LINE_CHANNEL_ACCESS_TOKEN', None)
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


@app.route('/img-sam/<path:filename>')
def image(filename):
    return send_from_directory('img', filename)


@app.route('/tmp/<path:filename>')
def csv(filename):  
    return send_from_directory('tmp', filename)


@app.route("/callback", methods=['POST'])
def callback():
    signature = request.headers['X-Line-Signature']

    # get request body as text
    body = request.get_data(as_text=True)
    app.logger.info("Request body: " + body)

    # parse webhook body
    try:
        events = parser.parse(body, signature)
    except InvalidSignatureError:
        abort(400)

    # if event is MessageEvent and message is TextMessage, then echo text
    #print(events)
    for event in events:
        if not isinstance(event, MessageEvent):
            continue
        if not isinstance(event.message, TextMessage):
            continue
        
        received_text = event.message.text

        if re.search('観光', received_text):
            from tokushima_opendata.tourist_spot import get_tourist_spot
            get_tourist_spot()
            post_text(event.reply_token, 'kankou')

        elif re.search('ホテル', received_text):
            try:
                post_carousel(event.reply_token)
            except Exception as e:
                print(e)
        elif re.search('タクシー', received_text):
            post_text(event.reply_token, 'taxi')
        
        elif re.search('Wi-Fi', received_text):
            post_text(event.reply_token, 'Wi-Fi')
        
        else:
            post_text(event.reply_token, received_text)
    
    return 'OK'

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
