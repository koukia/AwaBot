# -*- coding: utf-8 -*-
from urllib.request import urlopen
from urllib.error import HTTPError
from urllib.error import URLError
import urllib.request
import json
import os
from urllib.parse import urlencode
from urllib.parse import quote

USER_LOCAL_API_KEY = os.getenv('USER_LOCAL_API_KEY', None)


def get_reply(message):
    #print(type(message))
    enc_message = quote(str(message))
    url = 'https://chatbot-api.userlocal.jp/api/chat?message={mess}&key={key}'.format(mess=enc_message,key=USER_LOCAL_API_KEY)
    #print(str(url))
    with urllib.request.urlopen(url) as res:
        html = res.read().decode("utf-8")
    #print(html)
    dict_response = json.loads(html)

    if dict_response['status'] == 'success':
        return str(dict_response['result'])
    else:
        return None

if __name__ == '__main__':
    try:
        get_reply('hello')
    except Exception as e:
        print(e)
