# This is a sample Python script.
import copy
import random
from torch.utils.tensorboard import SummaryWriter
import datetime

from data.data_read import get_all_data
from util import Item, Stack, Stripe, Flat, total_size
from sum_tree import SumTree
import util


def get_items():
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


def get_stripes(items):
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
            try:
                assert not item.be_used, '采样到已经被使用的item，不合理！'
            except:
                pass

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


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    # init log writer
    cur_time = datetime.datetime.now()
    writer = SummaryWriter(f'./log/{cur_time.day}_{cur_time.hour}_{cur_time.minute}')

    # make all data to dict
    all_data_dict = get_all_data('A')

    # 所有毛坯实例化为item，存入items列表
    items = get_items()

    for step in range(1000):
        # 生成sum_tree，并添加item，此时sum_tree的叶子节点以index为顺序
        sum_tree = SumTree(len(items))
        for item in items:
            sum_tree.add(item.v_for_tree, item.index)

        print('==========start making stripes==========')

        # 产生stripes
        stripes = get_stripes(items)

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

        print('total_using_rate:', total_using_rate)
        writer.add_scalar('total_reward/red', total_using_rate, step)

        # 更新价值并重置items，进行下一次迭代
        flats.sort(key=lambda flat: flat.using_rate)
        for bad_flat_index in range(int(len(flats) * util.BAD_RATE)):
            for stripe in flats[bad_flat_index].stripes:
                for stack in stripe.stacks:
                    for item in stack.items:
                        item.update_v(flats[bad_flat_index].using_rate)

        reset(items)