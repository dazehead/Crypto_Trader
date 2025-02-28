import time

class Risk_Handler:
    def __init__(self, client=None):
        self.client = client
        self.percent_to_size = .02
        self.total_balance = 1000
        if client is not None:
            self.total_balance = self.client.get_account_balance()
            self.balance_to_risk = None
            print(f"Balance: {self.total_balance}") 
        print("Risk Handler Initialized")
        print(f"client: {self.client.__class__.__name__}")  
        self.symbol_params = {}

