import numpy as np


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

        self.be_stacked = False

    @property
    def size(self):
        return [self.item_length, self.item_width]


class Stack():
    def __init__(self):
        self.items = []
        self.length = None
        self.width = None

    def add_item(self, item):
        self.items.append(item)
        item.be_stacked = True
        self.update()

    def update(self):
        length = 0
        for item in self.items:
            length += item.item_length
        width = self.items[0].item_width
        self.length = length
        self.width = width

    def sort(self, len_or_wid='length'):
        assert len_or_wid in ['length', 'width']
        if len_or_wid == 'length':
            self.items.sort(key=lambda item: item.item_length)
        else:
            self.items.sort(key=lambda item: item.item_width)

    @property
    def num_items(self):
        return len(self.items)
