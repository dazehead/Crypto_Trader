"""This class will have all logic for executing trades"""
class Trade():

    def __init__(self, signals):
        self.signals = signals

        if self.signals[-1] == 1:
            self.buy()

        elif self.signals[-1] == -1:
            self.sell()
            
        else:
            self.monitor_trade()


    def buy(self):
        pass

    def sell(self):
        pass

    def monitor_trade(self):
        pass
