#!/usr/bin/env python3
import pandas as pd
import os

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
    path = path + '\\子问题' + str(question) + '-数据集' + word + '\\data' + word + str(num) + '.csv'
    print('读取文件路径为: ', path)

    data = pd.read_csv(path)

    # print(data.iloc[:3, 1])


read_data_from_excel('A', 1)