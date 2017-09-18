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

def get_data():
    '''
    import csv
    f = open('./tokushima_opendata/kankoshisetsu.csv', 'r')
    reader = csv.reader(f)
    header = next(reader)
    for row in reader:
        print(row)
    f.close()
    '''
    data = pd.read_csv(file_path)#, encoding="SHIFT-JIS")
    print(data)
    print('\n-----\n')

    '''
    d = data[data["time"].str.contains(date)]
    d = d[['time', 'air_temperature']]
    d = d.dropna(axis=0)
    d['time'] = pd.to_datetime(d['time'])

    return d    #d = time and air_temperature
    '''
def get_tourist_spot():
    try:
        get_data()
    except Exception as e:
        print(e.args)

