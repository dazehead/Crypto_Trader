from llist import dllist

class Longbook:
    def __init__(self, data=None, max=None, fast_window=None, slow_window=None):
        self.data = data
        self.max = max
        self.fast_window = fast_window
        self.slow_window = slow_window

        print(self.data)
        print(type(self.data))

    def into_llist(self):
        linked_list = dllist(self.data)
        for node in linked_list:
            print(node)

    def bests_into_llist(self):
        linked_bests = dllist([self.max, self.fast_window, self.slow_window]) 
        for node in linked_bests:
            print(node)
