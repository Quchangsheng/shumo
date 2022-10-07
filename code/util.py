import copy
import numpy as np

total_size = {'length': 2440, 'width': 1220, 's': 2440*1220}
LAMBDA_1 = 2
LAMBDA_2 = 2
BAD_RATE = 0.1
BETA = 1
G1, G2 = 0.8, 0.2


class Item():
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
        self.s = self.item_length * self.item_width

        # 调整长和宽
        if self.item_width > self.item_length:
            self.exchange_len_and_wid()

        # 初始化价值
        if self.item_width > 0.5 * total_size['width']:
            lambda_1 = LAMBDA_1
        else:
            lambda_1 = 1
        if self.item_length > 0.5 * total_size['length']:
            lambda_2 = LAMBDA_2
        else:
            lambda_2 = 1
        self.v = lambda_1 * lambda_2 * self.s
        self.v_for_tree = copy.deepcopy(self.v) / 100

    def reset(self):
        # 调整长和宽
        if self.item_width > self.item_length:
            self.exchange_len_and_wid()
        self.v_for_tree = copy.deepcopy(self.v) / 100
        self.be_used = False

    def update_v(self, using_rate):
        self.v = G1 * self.v + G2 * pow(self.s, BETA) / using_rate

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
        for stripe in self.stripes:
            length += stripe.length
        width = self.stripes[0].width
        self.length = length
        self.width = width
        for stripe in self.stripes:
            s += stripe.s
        self.s = copy.deepcopy(s)
        self.using_rate = self.s / total_size['s']

    @property
    def num_strips(self):
        return len(self.stripes)