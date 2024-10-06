import sqlite3
import utils
class Node:
    """A class representing a single node in the linked list."""
    def __init__(self, value, next_node=None):
        self.value = value 
        self.next_node = next_node

    def get_value(self):
        return self.value

    def get_next_node(self):
        return self.next_node

    def set_next_node(self, next_node):
        self.next_node = next_node


class LinkedList:
    """A class representing a generic linked list."""
    def __init__(self, value=None):
        self.head_node = Node(value) if value is not None else None

    def get_head_node(self):
        return self.head_node

    def insert_beginning(self, new_value):
        new_node = Node(new_value)
        new_node.set_next_node(self.head_node)
        self.head_node = new_node

    def insert_end(self, new_value):
        new_node = Node(new_value)
        if not self.head_node:
            self.head_node = new_node
            return
        current_node = self.head_node
        while current_node.get_next_node():
            current_node = current_node.get_next_node()
        current_node.set_next_node(new_node)

    def remove_node(self, value_to_remove):
        current_node = self.get_head_node()
        if not current_node:
            return
        if current_node.get_value() == value_to_remove:
            self.head_node = current_node.get_next_node()
        else:
            while current_node:
                next_node = current_node.get_next_node()
                if next_node and next_node.get_value() == value_to_remove:
                    current_node.set_next_node(next_node.get_next_node())
                    return
                current_node = next_node

    def stringify_list(self):
        """Returns a string representation of all values in the list."""
        string_list = ""
        current_node = self.get_head_node()
        while current_node:
            string_list += str(current_node.get_value()) + "\n"
            current_node = current_node.get_next_node()
        return string_list
    
    def export_multiple_to_db(self, granularity):
        """not finished"""
        current_node = self.get_head_node()
        while current_node:
            strat = current_node.get_value()
            # this is where we are going to call the util function for exporting
            output_dict = {}
            table_name = ''
            for strategy in strat.strategies:
                table_name += strategy.__class__.__name__ + '_'
                output_dict.update(utils.get_params_from_strategy(strategy))
            table_name = table_name.rstrip('_')

            df = utils.get_metrics_from_backtest(strat,
                                                 multiple=True,
                                                 multiple_dict=output_dict)
            
            utils.export_backtest_to_db(df,
                                        granularity=granularity,
                                        multiple_table_name=table_name)

            current_node = current_node.get_next_node()
