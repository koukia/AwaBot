# -*- coding: utf-8 -*-

import numpy as np
import pandas as pd
import matplotlib as mpl
mpl.use('Agg')
import matplotlib.pyplot as plt
import subprocess
import sys
import datetime

tourist_file_path       = "./tokushima_opendata/kankoshisetsu.csv"
hotel_file_path         = "./tokushima_opendata/hotels.csv"
tourism_hotel_file_path = "./tokushima_opendata/tebura_kanko_hotel.csv"
wifi_file_path          = "./tokushima_opendata/TokushimaFreeWi-Fiスポット_登録データ一覧_2017年06月30日.csv"

def get_tourist_spot(lng, lat):
    print('現在地:('+str(lng)+'  ,  '+str(lat)+')')
    data = pd.read_csv(tourist_file_path, header=1)#, encoding="SHIFT-JIS")
    placeList = []
    for key,row in data.iterrows():
        diff = compareCoordinate(lng,lat,row[4],row[3])
        place_dict = {'diff':diff, 'name':row[1], 'lng':row[4],'lat':row[3]}
        place_dict['address'] = row[2]
        placeList.append(place_dict)

    return select_spot_list(placeList, 'diff', 5)

def get_hotel(lng, lat):
    data = pd.read_csv(hotel_file_path , header=1, encoding="SHIFT-JIS")
    placeList = []
    #i=0
    for key, row in data.iterrows():
        '''
        if i<3:
            for i, v in enumerate(row):
                print(i,v)
            i+=1
        '''
        diff = compareCoordinate(lng, lat, row[6], row[5])
        place_dict = {'diff': diff, 'name': row[1], 'lng': row[6], 'lat': row[5]}
        place_dict['address'] = row[4]
        place_dict['tel'] = row[7]
        place_dict['url'] = row[8]
        placeList.append(place_dict)

    return select_spot_list(placeList, 'diff', 5)

def get_wifi_spot(lng, lat):
    data = pd.read_csv(wifi_file_path, header=0, encoding="SHIFT-JIS")
    placeList = []
    for key, row in data.iterrows():
        diff = compareCoordinate(lng, lat, row[4], row[3])
        place_dict = {'diff': diff, 'name': row[1]+' '+row[17], 'lng': row[4], 'lat': row[3]}
        place_dict['town'] = row[0]
        place_dict['address'] = row[2]
        placeList.append(place_dict)

    return select_spot_list(placeList, 'diff', 5)


def select_spot_list(place_list, key , max):
    try:
        sorted_list = sorted(place_list, key=lambda x: x[key])
        selected_list = []
        i = 0
        for place in sorted_list:
            selected_list.append(place)
            i += 1
            if i >= max:
                break
        return selected_list
    except Exception as e:
        print(e)
        return None

def compareCoordinate(cur_lng, cur_lat, dest_lng, dest_lat):
    try:
        diff_x = float(dest_lat) - float(cur_lat)
        diff_y = float(dest_lng) - float(cur_lng)
        #print('x: '+str(diff_x)+' y:'+str(diff_y)+' ->'+ str(diff_x ** 2 + diff_y ** 2))
        diff = np.sqrt(diff_x ** 2 + diff_y ** 2)
    except Exception as e:
        print(e)
        return None
    return diff


    

