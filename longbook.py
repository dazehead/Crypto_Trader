from llist import dllist

class Longbook:
    def __init__(self, **kwargs):
        self.data = kwargs.get('data')

    def into_llist(self):
        linked_list = dllist(self.data)
        linked_list.append(4)
        linked_list.appendleft(0)
        for node in linked_list:
            print(node)