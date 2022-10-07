from data.data_read import get_all_data
from util import Item, Stack


def get_1d_stack(all_data_dict):
    # 所有item实例化成类
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

    # 对item进行第一阶段拼接 -> 1D
    stacks = []
    while True:
        stack = Stack()
        for item in items:
            # 如果该item还未被拼接
            if not item.be_used:
                # 如果stack还未添加item，添加第一个item确定宽度
                if stack.num_items == 0:
                    stack.add_item(item)
            # 具有相同宽度添加到stack
            if stack.width == item.item_width and (not item.be_used):
                stack.add_item(item)

        if stack.num_items > 0:
            stacks.append(stack)
        else:
            # 如果没有为拼接的，则结束
            break

    return stacks