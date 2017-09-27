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
from UserLocalApi import get_reply
from user_location import get_location
from user_location import save_location

app = Flask(__name__)

channel_access_token = os.getenv('LINE_CHANNEL_ACCESS_TOKEN', None)
channel_secret = os.getenv('LINE_CHANNEL_SECRET', None)
# host_name = 'https://nameless-gorge-55138.herokuapp.com'

if channel_secret is None:
    print('Specify LINE_CHANNEL_SECRET as environment variable.')
    sys.exit(1)
if channel_access_token is None:
    print('Specify LINE_CHANNEL_ACCESS_TOKEN as environment variable.')
    sys.exit(1)

line_bot_api = LineBotApi(channel_access_token)
parser = WebhookParser(channel_secret)

userLocDict = {}
_DEBUG = False
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

    for event in events:
        user_id = event.source.sender_id

        if isinstance(event, PostbackEvent):
            # print(str(event.postback.data))
            if re.search('action=loc', event.postback.data):
                params = event.postback.data.split('&')
                name = params[1].split('=')[1]
                address =params[2].split('=')[1]
                lat = params[3].split('=')[1]
                lng = params[4].split('=')[1]

                # print(address)
                post_location(event.reply_token, title=name, address=address, latitude=lat, longitude=lng)

            if re.search('action=detail', event.postback.data):
                name = event.postback.data.split('&')[1].split('=')[1]
                # print(name)
                post_text(event.reply_token, "https://google.co.jp/search?q=" + name)

        # FollowEvent, JoinEvent の処理はしない
        if not isinstance(event, MessageEvent):
            continue

        if isinstance(event.message, TextMessage):
            receiveText(event)

        if isinstance(event.message, LocationMessage):
            lat = event.message.latitude
            lng = event.message.longitude
            save_location(user_id, lat, lng)
            post_kind(event.reply_token)

    return 'OK'


def receiveText(event):
    user_id = event.source.sender_id
    received_text = event.message.text
    loc_dict = get_location(user_id)

    if re.search('案内', received_text):
        if loc_dict is None:
            post_text(event.reply_token, '+ から位置情報を送ってね')
        else:
            post_kind(event.reply_token)
    elif re.search('観光地', received_text):
        if loc_dict is None:
            post_text(event.reply_token, '+ から位置情報を送ってね')
        else:
            result = get_tourist_spot(loc_dict['lat'], loc_dict['lng'])
            post_spot_carousel('tour', event.reply_token, result)
    elif re.search('ホテル', received_text):
        if loc_dict is None:
            post_text(event.reply_token, '+ から位置情報を送ってね')
        else:
            result = get_hotel(loc_dict['lat'], loc_dict['lng'])
            post_spot_carousel('hotel', event.reply_token, result)
    elif re.search('Wi-Fi', received_text) or re.search('WiFi', received_text):
        if loc_dict is None:
            post_text(event.reply_token, '+ から位置情報を送ってね')
        else:
            result = get_wifi_spot(loc_dict['lat'], loc_dict['lng'])
            post_spot_carousel('wifi', event.reply_token, result)
    elif re.search('ひまつぶし', received_text) or re.search('WiFi', received_text):
        mame = ['''藍染め（あいぞめ）は、徳島の特産物の一つで藍を染料として用いた染物なんよ。
    藍染めは名前のとおり藍色の染色を行うことができて、色が褪(あ)せにくいという優れた特徴を持つんじょ！
    日本では江戸時代には多くの藍染めが行われとって、そん中でも阿波藩での生産は盛んで、今でも徳島県の藍染めは全国的に有名なんよ！！''',
        '''阿波おどりは、徳島県発祥の盆踊りで日本三大盆踊りのひとつで、約400年の歴史がある日本の伝統芸能があるんじょ。
    その中でも徳島市の阿波おどりは、お盆になると人口約26万人の徳島市に全国から延べ135万人の観光客が集まるけん踊り子や観客数において国内最大規模なんじょ！''',
        '''マチ★アソビは、アニメ制作会社ufotableが企画制作するアニメやゲームなどのエンターテインメントが集まるイベントなんじょ。
    「マチをアソビつくす」ことがテーマになっとって、大都市や他の地方都市ではできない徳島の地理や魅力を活用した企画が実施されとんじょ！
    例えば、市街で業界関係者のトークイベントがあったり、眉山ロープウェイでは車内に声優による案内が流れたりするんじょ！''',
        '''眉山（びざん）は、徳島市街に隣接して徳島市の景観を代表する山なんじょ。
    どの方向から眺めても眉に見えるから眉の山で眉山って名前になったらしいんよ''']
        import random
        index = random.randint(0, len(mame)-1)
        print(index)
        reply = mame[index]
        post_text(event.reply_token, reply)
    elif re.search('ヘルプ', received_text) or re.search('WiFi', received_text):
        reply = '''１．まずは、位置情報を送ってね。
        入力フォームの左にある＋を押して「位置情報」をタップしてね\n２．行きたい場所を教えてね。
        徳島県のオープンデータから「観光施設」「ホテル」「とくしま無料Wi-Fiスポット」を教えるよ'''
        post_text(event.reply_token, reply)
    else:
        reply = get_reply(received_text)
        # print(reply)
        post_text(event.reply_token, reply)


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
        original_content_url=image_path,
        preview_image_url=image_path
    )
    line_bot_api.reply_message(
        token,
        image_message
    )


def post_kind(token):
    payload = {
        "replyToken": token,
        "messages": [
            {
                "type": "template",
                "altText": "select destination",
                "template": {
                    "type": "buttons",
                    "text": "どこに行きたいですか？",
                    "actions": [
                        {
                            "type": "message",
                            "label": "観光地",
                            "text": "観光地を教えて"
                        },
                        {
                            "type": "message",
                            "label": "ホテル",
                            "text": "ホテルを教えて"
                        },
                        {
                            "type": "message",
                            "label": "Wi-Fiスポット",
                            "text": "Wi-Fiスポットを教えて"
                        }
                    ]
                }
            }
        ]
    }
    # print(payload)
    REPLY_ENDPOINT = 'https://api.line.me/v2/bot/message/reply'
    HEADER = {
        "Content-Type": "application/json",
        "Authorization": "Bearer " + channel_access_token
    }
    requests.post(REPLY_ENDPOINT, headers=HEADER, data=json.dumps(payload))


def post_spot_carousel(kind, token, place_list):
    columns = None
    if kind is 'tour':
        columns = get_tourist_spot_columns(place_list)
    elif kind is 'hotel':
        columns = get_hotel_columns(place_list)
    elif kind is 'wifi':
        columns = get_wifi_spot_columns(place_list)
    payload = {
        "replyToken": token,
        "messages": [
            {
                "type": "template",
                "altText": "スポットのリスト",
                "template": {
                    "type": "carousel",
                    "columns": columns
                }
            }
        ]
    }
    REPLY_ENDPOINT = 'https://api.line.me/v2/bot/message/reply'
    HEADER = {
        "Content-Type": "application/json",
        "Authorization": "Bearer " + channel_access_token
    }
    requests.post(REPLY_ENDPOINT, headers=HEADER, data=json.dumps(payload))


def get_tourist_spot_columns(places):
    columns = []
    for place in places:
        columns.append({
            "title": place['name'],
            "text": place['address'],
            "actions": [
                {
                    "type": "postback",
                    "label": "位置情報",
                    "data": "action=loc&name=" + place['name'] +
                            "&address=" + place['address'] +
                            "&lat=" + str(place['lat']) +
                            "&lng=" + str(place['lng'])
                },
                {
                    "type": "postback",
                    "label": "詳しく",
                    "data": "action=detail&name=" + place['name'],
                }
            ]
        })
    return columns


def get_hotel_columns(places):
    columns = []
    exist_hp = True
    for place in places:
        if type(place['url']) is float:
            exist_hp = False

    for place in places:
        print(type(place['url'])) #DEBUG
        actions = [
            {
                "type": "postback",
                "label": "位置情報",
                "data": "action=loc&name=" + place['name'] +
                        "&address=" + place['address'] +
                        "&lat=" + str(place['lat']) +
                        "&lng=" + str(place['lng'])
            }, {
                "type": "uri",
                "label": "電話",
                "uri": str("tel:" + place['tel'])
            }

        ]
        if exist_hp:
            actions.append({
                "type": "uri",
                "label": "ホームページ",
                "uri": place['url']
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
            "text": place['detail'],
            "actions": [
                {
                    "type": "postback",
                    "label": "位置情報",
                    "data": "action=loc&name=" + place['name'] +
                        "&address=" + place['address'] +
                        "&lat=" + str(place['lat']) +
                        "&lng=" + str(place['lng'])
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
