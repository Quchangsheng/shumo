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

    path = './result/' + '数据集' + word + str(num) + '/step3_0.7074696757604041' + '/data.csv'
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
    path1 = './result/' + '数据集' + word + str(num)
    for step in range(1):
        path = path1 + '/step' + '3_0.7074696757604041' + '/view'
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

def plot_b(word, num):
    path1 = './result/' + '数据集' + word + str(num)

    path = path1 + '/data_0.6997202136555108.csv'

    dict = {
        'Unnamed: 0': [],
        'batch_index': [],
        'item_material': [],
        'flat_index': [],
        'item_id': [],
        'x': [],
        'y': [],
        'x_length': [],
        'y_length': []
    }
    assert word in ['A', 'B'], 'word error!'
    assert num in [1, 2, 3, 4, 5], 'num error!'
    if word == 'A':
        question = 1
    else:
        question = 2

    print('读取文件路径为: ', path)
    data = pd.read_csv(path)
    data_dict = data.to_dict('list')
    for key in data_dict.keys():
        dict[key].extend(data_dict[key])
    for b in range(dict['batch_index'][-1]+1):
        index = []
        for i in range(len(dict['y'])):
            if dict['batch_index'][i]==b:
                index.append(i)
        num_patterns = dict['flat_index'][index[-1]] + 1
        print(num_patterns)
        colors = ['b', 'g', 'r', 'y', 'm', 'k']
        for j in range(num_patterns):
            fig, ax = plt.subplots()
            ax.set_title(dict['item_material'][index[0]])
            ax.set_xlim(0, 2440)
            ax.set_ylim(0, 1220)
            current_axis = fig.gca()
            for item in index:
                if dict['flat_index'][item]==j:
                    rect = matplotlib.patches.Rectangle((dict['x'][item], dict['y'][item]), dict['x_length'][item],
                                                        dict['y_length'][item], facecolor=colors[item % 6])
                    rectangles = {str(dict['item_id'][item]): rect}
                    ax.add_artist(rectangles[str(dict['item_id'][item])])
                    rx, ry = rectangles[str(dict['item_id'][item])].get_xy()
                    cx = rx + rectangles[str(dict['item_id'][item])].get_width() / 2.0
                    cy = ry + rectangles[str(dict['item_id'][item])].get_height() / 2.0
                    ax.annotate(str(dict['item_id'][item]), (cx, cy), color='w', weight='bold',
                                fontsize=12, ha='center', va='center')
            plt.savefig(path1 + '/batch' + str(b) + 'flat' + str(j) + '.jpg')
            # plt.show()



    # num_patterns = dict['flat_index'][-1] + 1
    # colors = ['b', 'g', 'r', 'y', 'm', 'k']
    # for j in range(num_patterns):
    #     fig, ax = plt.subplots()
    #     ax.set_xlim(0, 2440)
    #     ax.set_ylim(0, 1220)
    #     current_axis = fig.gca()
    #     for i in range(len(dict['y'])):
    #         if dict['flat_index'][i] == j and:
    #             rect = matplotlib.patches.Rectangle((dict['x'][i], dict['y'][i]), dict['x_length'][i],
    #                                                 dict['y_length'][i], facecolor=colors[i % 6])
    #             rectangles = {str(dict['item_id'][i]): rect}
    #             ax.add_artist(rectangles[str(dict['item_id'][i])])
    #             rx, ry = rectangles[str(dict['item_id'][i])].get_xy()
    #             cx = rx + rectangles[str(dict['item_id'][i])].get_width() / 2.0
    #             cy = ry + rectangles[str(dict['item_id'][i])].get_height() / 2.0
    #             ax.annotate(str(dict['item_id'][i]), (cx, cy), color='w', weight='bold',
    #                         fontsize=12, ha='center', va='center')
    #             # current_axis.add_patch(rect)
    #     plt.savefig(path + str(j) + '.jpg')
    #     # plt.show()

if __name__ == '__main__':
    plot_b('B', 5)

