# This is a sample Python script.
import copy
import os
import random

import numpy as np
from torch.utils.tensorboard import SummaryWriter
import datetime
import pandas as pd

from data.data_read import get_all_data
from util import Item, Stack, Stripe, Flat, total_size
from sum_tree import SumTree
import util
from plot import plot


def get_items(all_data_dict):
    '''
    :return: items 以宽降序排列，同宽下长度降序排列
    '''
    items = []
    for i in range(len(all_data_dict['item_id'])):
        items.append(Item(
            index=all_data_dict['index'][i],
            item_id=all_data_dict['item_id'][i],
            item_material=all_data_dict['item_material'][i],
            item_num=all_data_dict['item_num'][i],
            item_length=all_data_dict['item_length'][i],
            item_width=all_data_dict['item_width'][i],
            item_order=all_data_dict['item_order'][i],
        ))
    items.sort(key=lambda item: item.item_length)
    # items.reverse()
    items.sort(key=lambda item: item.item_width)
    items.reverse()
    for i in range(len(items)):
        items[i].index = copy.deepcopy(i)
    return items


def get_stripes(items, sum_tree):
    stripes = []
    while True:  # 直到所有stack(item)都被使用
        # 是否所有item均被使用
        be_used_count = 0
        for item in items:
            if item.be_used:
                be_used_count += 1
        if be_used_count == len(items):
            break

        # 还有没用的item，则初始化一个stripe
        stripe = Stripe()
        while True:
            # 是否所有item均被使用
            be_used_count = 0
            for item in items:
                if item.be_used:
                    be_used_count += 1
            if be_used_count == len(items):
                break

            # 采样一个item
            _, _, item_index = sum_tree.get_leaf(random.random() * sum_tree.total_p)
            item = items[item_index]
            assert not item.be_used, '采样到已经被使用的item，不合理！'

            # 判断产生stack（能向上添加则产生stack）
            if item.item_width + stripe.width <= total_size['width'] and \
                    (stripe.length == 0 or item.item_length <= stripe.length):
                stack = Stack()
                stack.add_item(item, sum_tree)  # debug: items中item被使用，item被使用，正确

                # # stack添加进stripe
                # stripe.add_stack(stack)   # debug: stack被使用，正确
            # 不能则循环找item向上塞
            else:
                # 搜索可以向上塞入的item（按宽度有大到小搜索）
                # 防止原始items顺序被打乱
                items_copy = copy.deepcopy(items)
                items_copy.sort(key=lambda item_copy: item_copy.item_width)
                items_copy.reverse()  # debug: copy_items顺序改变，items没变，正确

                # 可向上塞入的item_index
                item_index = 1e6
                for item_copy in items_copy:
                    if item_copy.item_width + stripe.width <= total_size['width'] and \
                            item_copy.item_length <= stripe.length and not item_copy.be_used:
                        item_index = copy.deepcopy(item_copy.index)
                        break
                # 找到了
                if item_index <= len(items):
                    item = [item for item in items if item.index == item_index]
                    assert len(item) == 1, '原始items的index出现重复 or item_index超出范围！'
                    stack = Stack()
                    stack.add_item(item[0], sum_tree)
                else:
                    break

            # 把只有一个item的stack加入stripe
            stripe.add_stack(stack)

            # 向右填充stack
            for item in items:
                if not item.be_used:
                    if item.item_width == stack.width and \
                            item.item_length + stack.length <= stripe.length:
                        stack.add_item(item, sum_tree)
                        assert len(stripe.stacks[-1].items) > 1, 'stack 横向添加错误！'
                    elif item.item_length == stack.width and \
                            item.item_width + stack.length <= stripe.length:
                        # 交换长和宽
                        item.exchange_len_and_wid()
                        stack.add_item(item, sum_tree)
                        assert len(stripe.stacks[-1].items) > 1, 'stack 横向添加错误！'

        if len(stripe.stacks) > 0:
            stripes.append(stripe)

    # 检查strips
    # for stripe in stripes:
    #     for i in range(len(stripe.stacks)):
    #         if stripe.stacks[0].length < stripe.stacks[i].length:
    #             pass
    #         if stripe.width > total_size['width']:
    #             pass

    return stripes


def get_flats(stripes):
    flats = []
    while True:
        # 如果所有stripe都被使用
        stripe_be_used_count = 0
        for stripe in stripes:
            if stripe.be_used:
                stripe_be_used_count += 1
        if stripe_be_used_count == len(stripes):
            break

        flat = Flat()
        # 面积从大到小找stripe填入flat
        for stripe in stripes:
            if not stripe.be_used and stripe.length + flat.length <= total_size['length']:
                flat.add_stack(stripe)

        if len(flat.stripes) > 0:
            flats.append(flat)

    return flats


def reset(items):
    for item in items:
        item.reset()
    items.sort(key=lambda item: item.item_length)
    # items.reverse()
    items.sort(key=lambda item: item.item_width)
    items.reverse()
    for i in range(len(items)):
        items[i].index = copy.deepcopy(i)


def bayesian_optimization(**params):
    # init params
    params = {
        'lambda_1': params['lambda_1'],
        'lambda_2': params['lambda_2'],
        'bad_rate': params['bad_rate'],
        'beta': params['beta'],
        'g1': params['g1'],
        'g2': params['g2'],
    }

    # make all data to dict
    all_data_dict = get_all_data(util.word, util.num)

    # 所有毛坯实例化为item，存入items列表
    items = get_items(all_data_dict)

    total_using_rate, total_using_rate_steps = train(items, util.max_step, params)

    return np.max(total_using_rate_steps)


def train(items, train_max_step, params):
    assert train_max_step > 0, 'train step 应大于 0！'
    # assign value to params
    for item in items:
        item.lambda_1 = params['lambda_1']
        item.lambda_2 = params['lambda_2']
        item.beta = params['beta']
        item.g1 = params['g1']
        item.g2 = params['g2']

    total_using_rate_steps = np.zeros(util.max_step)
    for step in range(train_max_step):
        # 生成sum_tree，并添加item，此时sum_tree的叶子节点以index为顺序
        sum_tree = SumTree(len(items))
        for item in items:
            sum_tree.add(item.v_for_tree, item.index)

        print('==========start making stripes==========')

        # 产生stripes
        stripes = get_stripes(items, sum_tree)

        print('=============finish stripes=============')
        print('===========start making flats===========')

        # 由stripes组成flat
        # 将stripe按长度排序（面积不太合理）
        stripes.sort(key=lambda stripe: stripe.length)
        stripes.reverse()
        flats = get_flats(stripes)

        print('==============finish flats==============')

        total_using_rate = 0
        for flat in flats:
            total_using_rate += flat.using_rate
        total_using_rate = total_using_rate / int(len(flats))
        total_using_rate_steps[step] = total_using_rate

        print('total_using_rate:', total_using_rate)
        writer.add_scalar('total_reward/red', total_using_rate, step)
        # check(flats)

        # calculate coordinate for items
        final_dict = get_items_coordinate_and_make_final_dict(flats)
        # store .csv file as requested
        final_df = pd.DataFrame(final_dict)
        store_path = './result/' + '数据集' + util.word + str(util.num) + '/step' + str(step) + '_' + str(total_using_rate)
        if not os.path.exists(store_path):
            os.mkdir(store_path)
        final_df.to_csv(store_path + '/data.csv')

        # 更新价值并重置items，进行下一次迭代
        flats.sort(key=lambda flat: flat.using_rate)
        for bad_flat_index in range(int(len(flats) * params['bad_rate'])):
            for stripe in flats[bad_flat_index].stripes:
                for stack in stripe.stacks:
                    for item in stack.items:
                        item.update_v(flats[bad_flat_index].using_rate)

        reset(items)

    return total_using_rate, total_using_rate_steps


def check(flats):
    for flat_index, flat in enumerate(flats):
        if flat.length > total_size['length']:
            print('')
        if flat.width > total_size['width']:
            print('')
        length = 0
        for stripe in flat.stripes:
            length += stripe.length
            if stripe.width > flat.width:
                print('')
        if length != flat.length:
            print('')
        for stripe_index, stripe in enumerate(flat.stripes):
            if stripe.length > total_size['length']:
                print('')
            if stripe.width > total_size['width']:
                print('')
            if stripe.length != stripe.stacks[0].length:
                print('')
            width = 0
            for stack in stripe.stacks:
                width += stack.width
            if stripe.width != width:
                print('')
            for stack in stripe.stacks:
                if stripe.length < stack.length:
                    print('')

            for stack in stripe.stacks:
                if stack.length > total_size['length']:
                    print('')
                if stack.width > total_size['width']:
                    print('')
                length = 0
                for item in stack.items:
                    if stack.width != item.item_width:
                        print('')
                    length += item.item_length
                if stack.length != length:
                    print('')


def get_items_coordinate_and_make_final_dict(flats):
    '''
    :param flats: all flats -> list
    give x & y to all items, including flat index
    '''
    final_dict = {
        'item_material': [],
        'flat_index': [],
        'item_id': [],
        'x': [],
        'y': [],
        'x_length': [],
        'y_length': []
    }

    for flat_index, flat in enumerate(flats):
        x_stripe = 0
        for stripe_index, stripe in enumerate(flat.stripes):
            y = 0
            x_stripe += flat.stripes[stripe_index - 1].length if stripe_index >= 1 else 0
            for stack_index, stack in enumerate(stripe.stacks):
                y += stripe.stacks[stack_index - 1].width if stack_index >= 1 else 0
                x_stack = 0
                for item_index, item in enumerate(stack.items):
                    x_stack += stack.items[item_index - 1].item_length if item_index >= 1 else 0

                    item.x = copy.deepcopy(x_stripe + x_stack)
                    item.y = copy.deepcopy(y)
                    item.flat_index = copy.deepcopy(flat_index)

                    # make final dict
                    final_dict['item_material'].append(item.item_material)
                    final_dict['flat_index'].append(item.flat_index)
                    final_dict['item_id'].append(item.item_id)
                    final_dict['x'].append(item.x)
                    final_dict['y'].append(item.y)
                    final_dict['x_length'].append(item.item_length)
                    final_dict['y_length'].append(item.item_width)

    return final_dict


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    # init log writer
    cur_time = datetime.datetime.now()
    writer = SummaryWriter(f'./log/{cur_time.day}_{cur_time.hour}_{cur_time.minute}')

    # make all data to dict
    all_data_dict = get_all_data(util.word, util.num)

    # 所有毛坯实例化为item，存入items列表
    items = get_items(all_data_dict)

    params = {
        'lambda_1': util.LAMBDA_1,
        'lambda_2': util.LAMBDA_2,
        'bad_rate': util.BAD_RATE,
        'beta': util.BETA,
        'g1': util.G1,
        'g2': util.G2,
    }

    total_using_rate, total_using_rate_steps = train(items, util.max_step, params)

    print('最高材料利用率的step: ', np.argmax(total_using_rate_steps))
    print('最高材料利用率的step: ', np.max(total_using_rate_steps))

    # plot(util.word, util.num)
