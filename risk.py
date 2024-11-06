class Risk_Handler:
    def __init__(self, client=None):
        self.client = client
        self.percent_to_size = .02
        self.balance = self.client.get_trade_balance()
        self.balance_to_risk = self.kelly_criterion()
        print(f"Balance: {self.balance}")
        print(f"Balance to risk: {self.balance_to_risk}")

    def kelly_criterion(self):
        """Calculates balance to risk based off of backtests"""
        return self.balance * .10