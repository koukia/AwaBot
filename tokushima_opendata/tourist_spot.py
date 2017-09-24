# -*- coding: utf-8 -*-

import numpy as np
import pandas as pd
import matplotlib as mpl
mpl.use('Agg')
import matplotlib.pyplot as plt
import subprocess
import sys
import datetime

file_path = "./tokushima_opendata/kankoshisetsu.csv"
#file_path = "./tokushima_opendata/hotels.csv"

def get_tourist_spot_data(lng, lat):
    '''
    import csv
    f = open('./tokushima_opendata/kankoshisetsu.csv', 'r')
    reader = csv.reader(f)
    header = next(reader)
    for row in reader:
        print(row)
    f.close()
    '''
    data = pd.read_csv(file_path, header=1)#, encoding="SHIFT-JIS")
    #print(data['緯度'][10])
    print('--->1 \n')
    i=0
    placeList = []
    for key,row in data.iterrows():
        if i < 2:
            #print(key)
            print(row)
            #print(type(row[3]))
            #print(row[4])
        diff = compareCoordinate(lng,lat,row[3],row[4])
        if i < 2:
            print(diff)
        json = '{\'diff\':'+str(diff)+',\'name\':'+row[1]+'}'
        placeList.append(json)
        i += 1
    print('--->2 \n')
    print(placeList)
    print('--->3 \n')
    
    for item in placeList:
        js_item = json(item)
        print(item['name'])
        print(item['diff'])
    print('--->4 \n')
    #sorted_data = df.sort_values(by='diff')
    
    return None
    
## 名称                  住所          緯度           経度
    '''
    d = data[data["time"].str.contains(date)]
    d = d[['time', 'air_temperature']]
    d = d.dropna(axis=0)
    d['time'] = pd.to_datetime(d['time'])

    return d    #d = time and air_temperature
    '''
def compareCoordinate(cur_lng, cur_lat, dest_lng, dest_lat):
    try:
        diff_x = float(dest_lat) - float(cur_lat)
        diff_y = float(dest_lng) - float(cur_lng)
        diff = np.log2(diff_x ** 2 + diff_y ** 2)
    except Exception as e:
        print(e)
        return None
    return diff

def get_tourist_spot(lng, lat):
    print('--->get_tourist_spot\n')
    try:
        return get_tourist_spot_data(lng, lat)
    except Exception as e:
        return str(e)

def get_hotel(lng, lat):
    print('get hotel')

def get_tourism_hotel(lng, lat):
    print('get tourism hotel')
    

