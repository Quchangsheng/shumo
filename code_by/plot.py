#!/usr/bin/env python3
import numpy as np
import cv2
import pandas as pd
import os
import matplotlib.pyplot as plt
import matplotlib

import util


def read_csv(word, num, step):
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

    path = os.getcwd()   # E:\比赛\数学建模\shumo\code
    path = path + '/result/' + '数据集' + word + str(num) + '/step' + str(step) + '/data.csv'
    print('读取文件路径为: ', path)
    data = pd.read_csv(path)
    return data


def get_patterns(word, num, step):
    dict = {
        'Unnamed: 0': [],
        'item_material': [],
        'flat_index': [],
        'item_id': [],
        'x': [],
        'y': [],
        'x_length': [],
        'y_length': []
    }
    data = read_csv(word, num, step)
    data_dict = data.to_dict('list')
    for key in data_dict.keys():
        dict[key].extend(data_dict[key])
    return dict


def plot(word, num):
    path = os.getcwd()   # E:\比赛\数学建模\shumo\code
    path1 = path + '/result/' + '数据集' + word + str(num)
    for step in range(util.max_step):
        path = path1 + '/step' + str(step) + '/view'
        dict = get_patterns(word, num, step)
        num_patterns = dict['flat_index'][-1] + 1
        colors = ['b', 'g', 'r', 'y', 'm', 'k']
        for j in range(num_patterns):
            fig,ax = plt.subplots()
            ax.set_xlim(0, 2440)
            ax.set_ylim(0, 1220)
            current_axis = fig.gca()
            for i in range(len(dict['y'])):
                if dict['flat_index'][i] == j:
                    rect = matplotlib.patches.Rectangle((dict['x'][i],dict['y'][i]),dict['x_length'][i],dict['y_length'][i], facecolor=colors[i % 6])
                    rectangles = {str(dict['item_id'][i]):rect}
                    ax.add_artist(rectangles[str(dict['item_id'][i])])
                    rx, ry = rectangles[str(dict['item_id'][i])].get_xy()
                    cx = rx + rectangles[str(dict['item_id'][i])].get_width() / 2.0
                    cy = ry + rectangles[str(dict['item_id'][i])].get_height() / 2.0
                    ax.annotate(str(dict['item_id'][i]), (cx, cy), color='w', weight='bold',
                                fontsize=12, ha='center', va='center')
                    # current_axis.add_patch(rect)
            plt.savefig(path + str(j) + '.jpg')
            # plt.show()


if __name__ == '__main__':
    plot('A',1)

