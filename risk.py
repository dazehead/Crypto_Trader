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
            print(f"Balance to risk: {self.balance_to_risk}")
        self.nonce_counter = 1
        self.last_buy = {}

    def get_nonce(self):
        if self.nonce_counter > 14:
            self.conce_counter = 1
        base_nonce = int(time.time() * 10000)
        nonce = base_nonce + self.nonce_counter
        self.nonce_counter += 1
        return str(nonce)