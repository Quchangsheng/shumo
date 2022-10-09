# This is a sample Python script.
import copy
import os
import random
from operator import itemgetter
import time

import numpy as np
from torch.utils.tensorboard import SummaryWriter
import datetime
import pandas as pd

from data.data_read import get_all_data
from util import Item, Stack, Stripe, Flat, total_size, Order, Batch
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


def make_orders(items):
    """
    :param items: all items
    :return: orders 是按照订单数子顺序排列的
    """
    orders = []   # orders 是按照订单数子顺序排列的
    material_list = []   # 全部材料种类list
    while True:
        # 判断是否所有item均归到order
        count = 0
        for item in items:
            if item.be_maked_order:
                count += 1
            else:
                break
        if count == len(items):
            break

        # 新建order，不为空添加进orders
        order = Order(len(orders)+1)
        for item in items:
            if not item.be_maked_order and item.item_order == 'order'+str(order.order_num):
                order.add_item(item)

            # 生成全部材料种类list
            if item.item_material not in material_list:
                material_list.append(copy.deepcopy(item.item_material))

        if len(order.items) > 0:
            orders.append(order)

    # 检查order编号是否从1到最大
    count = 0
    for index, order in enumerate(orders):
        if order.order_num == index + 1:
            count += 1
    assert count == len(orders)

    return orders, material_list


def init_batch(orders):
    batchs = []
    for order in orders:
        batch = Batch(order.order_num)
        batch.add_order(order)
        batchs.append(batch)
    return batchs


def calculate_dist_for_batches(batches, material_list):
    """
    计算batch两两之间相似程度，抽象为距离，便于聚类
    :param batches: all batches (each batch has one order)
    :return: 2-dim distance matrix between batches
    """
    dist_matrix = np.zeros((len(batches), len(batches)))
    for index, batch in enumerate(batches):   # 列batch
        for index_, batch_ in enumerate(batches):   # 行batch
            # 遍历材料种类计算相似度
            total_num, same_kind_num = 0, 0
            for material_kind in material_list:
                material_item_num = len(batch.get_items_acc_material(material_kind))
                material_item_num_ = len(batch_.get_items_acc_material(material_kind))
                # total_num += material_item_num + material_item_num_
                if material_item_num > 0 or material_item_num_ > 0:
                    total_num += 1
                if material_item_num > 0 and material_item_num_ > 0:
                    # same_kind_num += material_item_num + material_item_num_
                    same_kind_num += 1
            same_rate = same_kind_num / total_num
            dist_matrix[index, index_] = 1 - same_rate

            # 对角线元素给-1，避免自己和自己合并
            if index == index_:
                dist_matrix[index, index_] = 10

    return dist_matrix


def make_cluster(batches, dist_matrix):
    """
    问题2核心部分
    :param batches:
    :param dist_matrix: 距离矩阵
    :return: batches 单步聚类结果
    """
    min_dist_value = np.min(dist_matrix)
    min_location_tuple = np.where(dist_matrix == min_dist_value)
    location_list = []
    for i in range(len(min_location_tuple[0])):
        location_list.append([min_location_tuple[0][i], min_location_tuple[1][i]])
    selected_batch_list = []  # 要删除的batch

    print('距离聚类')
    for min_location in location_list:
        # 去除对角线
        if min_location[0] == min_location[1]:
            continue
        else:
            selected_batch_0 = batches[min_location[0]]
            selected_batch_1 = batches[min_location[1]]
            # 之前没被选则，且合并后满足要求上限，删除
            if selected_batch_0 not in selected_batch_list and \
                    selected_batch_1 not in selected_batch_list and \
                    selected_batch_0.total_item_num + selected_batch_1.total_item_num <= util.Q2_BATCH_MAX_NUM and \
                    selected_batch_0.total_item_s + selected_batch_1.total_item_s <= util.Q2_BATCH_MAX_S:
                # 要删除的旧batch放进列表
                selected_batch_list.extend([selected_batch_0, selected_batch_1])

    # 考虑最小距离已经不能合并，通过循环的方式按相似度找可以合并的
    if len(selected_batch_list) <= 2:
        print('遍历聚类')
        for index, batch in enumerate(batches):
            batches_copy = copy.deepcopy(batches)
            if batch not in selected_batch_list:
                # 对copy batch用距离排序
                dist_copy = list(copy.deepcopy(dist_matrix[index, :]))
                dist_copy, batches_copy = [list(x) for x in zip(*sorted(zip(dist_copy, batches_copy), key=itemgetter(0)))]
                for batch_copy in batches_copy:
                    batch_copy_in_batches = [batch for batch in batches if batch.batch_num == batch_copy.batch_num]
                    assert len(batch_copy_in_batches) == 1, 'batch_num error!'
                    batch_copy_in_batches = batch_copy_in_batches[0]
                    if batch is not batch_copy_in_batches and \
                            batch_copy_in_batches not in selected_batch_list and \
                            batch.total_item_num + batch_copy_in_batches.total_item_num <= util.Q2_BATCH_MAX_NUM and \
                            batch.total_item_s + batch_copy_in_batches.total_item_s <= util.Q2_BATCH_MAX_S:
                        assert batch is not batch_copy_in_batches, 'get myself error!'
                        # 要删除的旧batch放进列表
                        selected_batch_list.extend([batch, batch_copy_in_batches])
                        break

    # 添加合并后的新batch
    for i in range(int(len(selected_batch_list) / 2)):
        batches_copy = copy.deepcopy(batches)
        batches_copy.sort(key=lambda batch_copy: batch_copy.batch_num)
        max_batch_num = batches_copy[-1].batch_num

        batch_new = Batch(max_batch_num + i + 1)
        batch_new.add_orders(selected_batch_list[i*2].orders + selected_batch_list[i*2 + 1].orders)
        batches.append(batch_new)
    # 删除合并后的batch
    for selected_batch in selected_batch_list:
        batches.remove(selected_batch)

    # check batches num
    # for index, batch in enumerate(batches):
    #     assert batch.batch_num == index + 1, 'merge batch make batch_num error!'

    print('cluster finish')

    return batches


def store_batches(batches):
    dict = {}
    for i in range(len(batches)):
        dict[i+1] = []
        for l in range(1000):
            try:
                dict[i+1].append(batches[i].orders[l].order_num)
            except:
                dict[i+1].append(-1)

    # 存储
    pd_dict = pd.DataFrame(dict)
    store_path = './result/' + '数据集' + util.word + str(util.num)
    pd_dict.to_csv(store_path + '/batch.csv')


def read_batches(orders):
    read_path = './result/' + '数据集' + util.word + str(util.num) + '/batch.csv'
    data = pd.read_csv(read_path)
    data_dict = data.to_dict('list')

    batches = []
    for i, key in enumerate(data_dict.keys()):
        if i == 0:
            continue
        batch = Batch(key)
        for order_num in data_dict[key]:
            if order_num < 0:
                break
            for order in orders:
                if order.order_num == order_num:
                    batch.add_order(order)
                    break
        if len(batch.orders) > 0:
            batches.append(batch)

    # check
    be_added_num = 0
    for order in orders:
        if order.be_added:
            be_added_num += 1
    assert be_added_num == len(orders)

    return batches


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

    total_using_rate = train(items, util.max_step, params)

    return total_using_rate


def train(items, train_max_step, params):
    # reset items index
    for i in range(len(items)):
        items[i].index = i

    assert train_max_step > 0, 'train step 应大于 0！'
    # assign value to params
    for item in items:
        item.lambda_1 = params['lambda_1']
        item.lambda_2 = params['lambda_2']
        item.beta = params['beta']
        item.g1 = params['g1']
        item.g2 = params['g2']

    total_using_rate_steps = np.zeros(util.max_step)
    last_using_rate = 0
    for step in range(train_max_step):
        # 生成sum_tree，并添加item，此时sum_tree的叶子节点以index为顺序
        sum_tree = SumTree(len(items))
        for item in items:
            sum_tree.add(item.v_for_tree, item.index)

        # print('==========start making stripes==========')

        # 产生stripes
        stripes = get_stripes(items, sum_tree)

        # print('=============finish stripes=============')
        # print('===========start making flats===========')

        # 由stripes组成flat
        # 将stripe按长度排序（面积不太合理）
        stripes.sort(key=lambda stripe: stripe.length)
        stripes.reverse()
        flats = get_flats(stripes)

        # print('==============finish flats==============')

        total_using_rate = 0
        for flat in flats:
            total_using_rate += flat.using_rate
        total_using_rate = total_using_rate / int(len(flats))
        total_using_rate_steps[step] = total_using_rate

        # 记录最高利用率的step信息
        if total_using_rate > last_using_rate:
            last_using_rate = total_using_rate
            flats_for_store = flats

        # print('total_using_rate:', total_using_rate)
        writer.add_scalar('total_reward/red', total_using_rate, step)
        # check(flats)

        # 更新价值并重置items，进行下一次迭代
        flats.sort(key=lambda flat: flat.using_rate)
        for bad_flat_index in range(int(len(flats) * params['bad_rate'])):
            for stripe in flats[bad_flat_index].stripes:
                for stack in stripe.stacks:
                    for item in stack.items:
                        item.update_v(flats[bad_flat_index].using_rate)

        reset(items)

    return total_using_rate, total_using_rate_steps, flats_for_store, len(flats_for_store)


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


def check_clusters(batches, orders):
    order_num = 0
    for batch in batches:
        assert batch.total_item_s <= util.Q2_BATCH_MAX_S
        assert batch.total_item_num <= util.Q2_BATCH_MAX_NUM
        order_num += len(batch.orders)
    assert order_num == len(orders)

def get_items_coordinate_and_make_final_dict(flats_batches):
    '''
    :param flats: all flats -> list
    give x & y to all items, including flat index
    '''
    final_dict = {
        'batch_index': [],
        'item_material': [],
        'flat_index': [],
        'item_id': [],
        'x': [],
        'y': [],
        'x_length': [],
        'y_length': []
    }
    for batch_index, flats_batch in enumerate(flats_batches):
        for flat_index, flat in enumerate(flats_batch):
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
                        final_dict['batch_index'].append(item.batch_index)
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

    start_init_data_time = time.time()
    # make all data to dict
    all_data_dict = get_all_data(util.word, util.num)

    # 所有毛坯实例化为item，存入items列表
    items = get_items(all_data_dict)
    total_item_num_q2 = copy.deepcopy(len(items))

    # 依据订单编号将item存入相应order
    orders, material_list = make_orders(items)   # debug: items全部编入order且编号没问题

    # init batches and matrix
    try:
        batches = read_batches(orders)     # 如果存储过聚类结果，直接读取
        print('read data')
    except:
        batches = init_batch(orders)     # 未存过聚类结果，初始化
        print('init data')
    param_matrix = np.ones((len(batches), len(batches)))

    finish_init_data_time = time.time()
    print('init_data:', finish_init_data_time - start_init_data_time)

    # 开始迭代训练
    for i in range(1):
        # 计算距离矩阵，并和迭代后的系数矩阵相点乘
        dist_matrix = calculate_dist_for_batches(batches, material_list)
        dist_matrix = param_matrix * dist_matrix   # 材料种类完重合，距离为0，完全不同距离为1

        # 聚类
        print('start clustering')
        start_cluster_time = time.time()
        count, add_num = 0, 0
        while True:
            batches_len = copy.deepcopy(len(batches))

            # 聚类
            batches = make_cluster(batches, dist_matrix)
            dist_matrix = calculate_dist_for_batches(batches, material_list)
            count += 1
            cluster_time = time.time()

            # 存储聚类结果并打印信息
            store_batches(batches)
            print('cluster次数：', count, '  time:', cluster_time - start_cluster_time, '  batch数量：', len(batches))
            # 如果不再聚类，跳出循环
            if len(batches) == batches_len:
                break
        check_clusters(batches, orders)
        print('=========check correct=========')

        params = {
            'lambda_1': util.LAMBDA_1,
            'lambda_2': util.LAMBDA_2,
            'bad_rate': util.BAD_RATE,
            'beta': util.BETA,
            'g1': util.G1,
            'g2': util.G2,
        }

        batches_inf = {}
        flats_batches = []
        for batch_index, batch in enumerate(batches):
            flats_batch = []
            for material in material_list:
                items_batch_material = batch.get_items_acc_material(material)
                if len(items_batch_material) > 0:
                    total_using_rate, total_using_rate_steps, flats_batch_material, flats_num = \
                        train(items_batch_material, util.max_step, params)
                    flats_batch.extend(flats_batch_material)
                    print(material, ': ', np.max(total_using_rate_steps), '  flat num:', flats_num)

            flats_batches.append(flats_batch)
            # batch using rate
            s = 0
            for flat in flats_batch:
                s += flat.s
            batch_using_rate = s / (len(flats_batch) * total_size['s'])
            print('batch_', batch_index, ': ', batch_using_rate)

        # all batches using rate
        s = 0
        for flats_batch in flats_batches:
            for flat in flats_batch:
                s += flat.s
        batches_using_rate = s / (len(flats_batches) * total_size['s'])
        print('all batches', ': ', batches_using_rate)

        # 检查item数量，给item添加批次属性
        item_num_check = 0
        for batch_index, flats_batch in enumerate(flats_batches):
            for flat in flats_batch:
                for stripe in flat.stripes:
                    for stack in stripe.stacks:
                        item_num_check += len(stack.items)
                        for item in stack.items:
                            item.batch_index = batch_index
                            # assert item.be_used, '有item未被使用'
                            pass
        assert item_num_check == total_item_num_q2, 'item数量错误'

        # 保存数据
        # calculate coordinate for items
        final_dict = get_items_coordinate_and_make_final_dict(flats_batches)
        # store .csv file as requested
        final_df = pd.DataFrame(final_dict)
        store_path = './result/' + '数据集' + util.word + str(util.num)
        if not os.path.exists(store_path):
            os.mkdir(store_path)
        final_df.to_csv(store_path + '/data_' + str(batches_using_rate) + '.csv')


    # plot(util.word, util.num)
