import copy
import math
import numpy as np

total_size = {'length': 2440, 'width': 1220, 's': 2440*1220}
Q2_BATCH_MAX_NUM = 1000
Q2_BATCH_MAX_S = 250 * 1e6
LAMBDA_1 = 4.26
LAMBDA_2 = 8.58
BAD_RATE = 0.4
BETA = 1.06
G1, G2 = 0.38, 0.49   # 0.8, 0.2

num = 4
word = 'B'
max_step = 50


class Item():
    """
    length: x_length
    width: y_length
    初始化及重置时长边x(length)，短边y(width)
    填充时可能旋转，此时交换x，y即可
    """
    def __init__(self, index, item_id, item_material, item_num,
                 item_length, item_width, item_order):
        self.index = index
        self.item_id = item_id
        self.item_material = item_material
        self.item_num = item_num
        self.item_length = item_length
        self.item_width = item_width
        self.item_order = item_order

        self.be_used = False
        self.be_maked_order = False
        self.s = self.item_length * self.item_width
        self.x = 0
        self.y = 0
        self.flat_index = None

        # 调整长和宽
        if self.item_width > self.item_length:
            self.exchange_len_and_wid()

        # init params
        self.lambda_1 = None
        self.lambda_2 = None
        self.beta = BETA
        self.g1 = G1
        self.g2 = G2

        # 初始化价值
        if self.item_width > 0.5 * total_size['width']:
            self.lambda_1 = LAMBDA_1
        else:
            self.lambda_1 = 1
        # self.lambda_2 = math.exp(self.item_length / 1000)
        if self.item_length > 0.5 * total_size['length']:
            self.lambda_2 = LAMBDA_2
        else:
            self.lambda_2 = 1

        self.v = self.lambda_1 * self.lambda_2 * self.s
        self.v_for_tree = copy.deepcopy(self.v) / 10000

    def reset(self):
        # 调整长和宽
        if self.item_width > self.item_length:
            self.exchange_len_and_wid()
        self.v_for_tree = copy.deepcopy(self.v) / 10000
        self.be_used = False
        self.x = 0
        self.y = 0

    def update_v(self, using_rate):
        self.v = self.g1 * self.v + self.g2 * pow(self.s, self.beta) / using_rate

    @property
    def size(self):
        return [self.item_length, self.item_width]

    def exchange_len_and_wid(self):
        '''
        交换长和宽
        '''
        temp = copy.deepcopy(self.item_width)
        self.item_width = copy.deepcopy(self.item_length)
        self.item_length = copy.deepcopy(temp)


class Stack():
    def __init__(self):
        self.items = []
        self.length = 0
        self.width = 0
        self.s = 0

        self.be_used = False

    def add_item(self, item, sum_tree):
        self.items.append(item)
        item.be_used = True

        item.v_for_tree = 0
        tree_index = item.index + sum_tree.capacity - 1
        sum_tree.update(tree_index, item.v_for_tree)
        self.update()

    def update(self):
        length = 0
        s = 0
        for item in self.items:
            length += item.item_length
        width = self.items[0].item_width
        self.length = length
        self.width = width
        for item in self.items:
            s += item.s
        self.s = copy.deepcopy(s)

    def sort(self, len_or_wid='length'):
        assert len_or_wid in ['length', 'width']
        if len_or_wid == 'length':
            self.items.sort(key=lambda item: item.item_length)
        else:
            self.items.sort(key=lambda item: item.item_width)

    @property
    def num_items(self):
        return len(self.items)


class Stripe():
    def __init__(self):
        self.stacks = []
        self.length = 0
        self.width = 0
        self.s = self.length * self.width

        self.be_used = False

    def add_stack(self, stack):
        self.stacks.append(stack)
        stack.be_used = True
        self.update()

        # check length
        for stack_check in self.stacks:
            assert stack_check.length <= self.length, 'exist one stack longer than stripe[0] length!'

    def update(self):
        width = 0
        s = 0
        for stack in self.stacks:
            width += stack.width
        length = self.stacks[0].length
        self.length = length
        self.width = width
        for stack in self.stacks:
            s += stack.s
        self.s = copy.deepcopy(s)

        if self.length > 0.9 * total_size['length']:
            self.length = total_size['length']

    @property
    def num_stacks(self):
        return len(self.stacks)


class Flat():
    def __init__(self):
        self.stripes = []
        self.length = 0
        self.width = 0
        self.s = 0
        self.using_rate = 0

        self.be_used = False

    def add_stack(self, stripe):
        self.stripes.append(stripe)
        stripe.be_used = True
        self.update()

    def update(self):
        length = 0
        s = 0
        width = 0
        for stripe in self.stripes:
            length += stripe.length
            if stripe.width > width:
                width = stripe.width
        self.length = length
        self.width = width
        for stripe in self.stripes:
            s += stripe.s
        self.s = copy.deepcopy(s)
        self.using_rate = self.s / total_size['s']

    @property
    def num_strips(self):
        return len(self.stripes)


class Order():
    def __init__(self, order_num):
        self.items = []
        self.order_num = order_num   # 从1开始
        self.material_dict = {}
        self.total_item_s = 0
        self.total_item_num = 0

        self.be_added = False

    def add_item(self, item):
        self.items.append(item)
        try:
            self.material_dict[item.item_material].append(item)
            item.be_maked_order = True
        except:
            self.material_dict[item.item_material] = []
            self.material_dict[item.item_material].append(item)
            item.be_maked_order = True

        self.update()

    def update(self):
        s = 0
        for item in self.items:
            s += item.s
        self.total_item_s = s
        self.total_item_num = len(self.items)

    def get_items_acc_material(self, item_material):
        try:
            return self.material_dict[item_material]
        except:
            return []


class Batch():
    def __init__(self, batch_num):
        self.orders = []
        self.batch_num = batch_num
        self.total_item_s = 0
        self.total_item_num = 0

    def add_order(self, order):   # 输入类实例
        self.orders.append(order)
        self.update()

    def add_orders(self, orders):  # 输入类实例list
        self.orders.extend(orders)
        self.update()

    def update(self):
        s, num = 0, 0
        for order in self.orders:
            s += order.total_item_s
            num += order.total_item_num
            order.be_added = True
        self.total_item_s = s
        self.total_item_num = num

    def get_items_acc_material(self, item_material):
        items_material = []
        for order in self.orders:
            items_material.extend(order.get_items_acc_material(item_material))
        return items_material




