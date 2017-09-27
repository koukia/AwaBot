# -*- coding: utf-8 -*-

USER_LOC_DATA_PATH = "./tmp/user_data.csv"

def get_location(user_id):
    f = open(USER_LOC_DATA_PATH, 'r')
    loc_dict = None
    '''ファイル内すべて走査して行末に近いデータを取得'''
    for line in f:
        id = line.split(':')[0]
        if(user_id == id):
            loc = line.split(':')[1]
            loc_dict = {'lat': loc.split(',')[0], 'lng': loc.split(',')[1].strip('\n')}
    if loc_dict is None:
        print('get_location()', '位置情報がありません')
    return loc_dict

def save_location(user_id, lat, lng):
    line = str(user_id)+':'+str(lat)+','+str(lng)+'\n'
    with open(USER_LOC_DATA_PATH, 'a') as f:
        f.write(line)
