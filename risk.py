class Risk_Handler:
    def __init__(self):
        self.percent_to_size = self.kelly_criterion()
        self.balance = self.get_portoflio_balance()

    def kelly_criterion(self):
        #calculate percent_to_size
        return .02

    def get_portoflio_balance(self):
        #get balance from exchange
        return 100