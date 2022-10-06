#!/usr/bin/env python3
import pandas as pd
import os
import numpy as np
import copy

def read_data_from_excel(word, num):
    '''
    :param word: 'A' or 'B'
    :param num: 1, 2, 3, 4, 5
    :return: path = E:\比赛\数学建模\shumo\code\data\子问题1-数据集A\dataA1.csv
    '''
    assert word in ['A', 'B'], 'word error!'
    assert num in [1, 2, 3, 4, 5], 'num error!'
    if word == 'A':
        question = 1
    else:
        question = 2

    path = os.getcwd()   # E:\比赛\数学建模\shumo\code\data
    path = path + '\\data\\子问题' + str(question) + '-数据集' + word + '\\data' + word + str(num) + '.csv'
    print('读取文件路径为: ', path)

    data = pd.read_csv(path)
    return data


def get_all_data(word):
    dict = {
        'index': [],
        'item_id': [],
        'item_material': [],
        'item_num': [],
        'item_length': [],
        'item_width': [],
        'item_order': [],
    }
    for i in range(4):
        data = read_data_from_excel(word, i+1)
        data_dict = data.to_dict('list')
        for key in data_dict.keys():
            dict[key].extend(data_dict[key])
    for index in range(len(dict['item_id'])):
        dict['index'].append(index)

    return dict


# dict = get_all_data('A')
# data_for_storage = pd.DataFrame(dict)
# data_for_storage.to_excel('data_all.xlsx')
