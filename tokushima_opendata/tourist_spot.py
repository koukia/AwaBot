# -*- coding: utf-8 -*-

import numpy as np
import pandas as pd
import matplotlib as mpl

mpl.use('Agg')
import matplotlib.pyplot as plt
import subprocess
import sys
import datetime

tourist_file_path = "./tokushima_opendata/kankoshisetsu.csv"
hotel_file_path = "./tokushima_opendata/hotels.csv"
tourism_hotel_file_path = "./tokushima_opendata/tebura_kanko_hotel.csv"
wifi_file_path = "./tokushima_opendata/TokushimaFreeWi-Fiスポット_登録データ一覧_2017年06月30日.csv"


def get_tourist_spot(lat, lng):
    print('get_tourist_spot()', lat, ',', lng)
    data = pd.read_csv(tourist_file_path, header=1)  # , encoding="SHIFT-JIS")
    placeList = []
    for key, row in data.iterrows():
        diff = compareCoordinate(lat, lng, row[3], row[4])
        place_dict = {'diff': diff, 'name': row[1], 'address': row[2], 'lat': row[3], 'lng': row[4]}
        placeList.append(place_dict)

    return select_spot_list(placeList, 'diff', 5)


def get_hotel(lat, lng):
    print('get_hotel()', lat, ',', lng)
    data = pd.read_csv(hotel_file_path, header=1, encoding="SHIFT-JIS")
    placeList = []
    for key, row in data.iterrows():
        diff = compareCoordinate(lat, lng, row[5], row[6])
        place_dict = {'diff': diff, 'name': row[1], 'address': row[4],
                      'lat': row[5], 'lng': row[6], 'tel': row[7],'url': row[8]}
        placeList.append(place_dict)

    return select_spot_list(placeList, 'diff', 5)


def get_wifi_spot(lat, lng):
    print('get_wifi_spot()', lat, ',', lng)
    data = pd.read_csv(wifi_file_path, header=0, encoding="SHIFT-JIS")
    placeList = []
    for key, row in data.iterrows():
        diff = compareCoordinate(lat, lng, row[3], row[4])
        place_dict = {'diff': diff, 'town': row[0], 'name': row[1],
                      'detail': row[17], 'address': row[2], 'lat': row[3], 'lng': row[4]}
        placeList.append(place_dict)
    return select_spot_list(placeList, 'diff', 5)


def select_spot_list(place_list, key, max):
    try:
        sorted_list = sorted(place_list, key=lambda x: x[key])
        selected_list = []
        for i in range(max):
            selected_list.append(sorted_list[i])
            #print(i,sorted_list[i])

        return selected_list
    except Exception as e:
        print(e)
        return None


def compareCoordinate(cur_lat, cur_lng, target_lat, target_lng):
    try:
        diff_x = float(target_lat) - float(cur_lat)
        diff_y = float(target_lng) - float(cur_lng)
        # print('x: '+str(diff_x)+' y:'+str(diff_y)+' ->'+ str(diff_x ** 2 + diff_y ** 2))
        diff = np.sqrt(diff_x ** 2 + diff_y ** 2)
    except Exception as e:
        print(e)
        return None
    return diff
