class Risk_Handler:
    def __init__(self, client=None):
        self.client = client
        self.percent_to_size = self.kelly_criterion()
        self.balance = self.get_portoflio_balance()
        self.amount_to_purchase = self.balance * self.percent_to_size

    def kelly_criterion(self):
        #calculate percent_to_size
        return .02

    def get_portoflio_balance(self):
        #get balance from client
        return 100