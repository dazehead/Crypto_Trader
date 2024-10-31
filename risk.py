class Risk_Handler:
    def __init__(self, client):
        self.client = client
        self.portfolio = None
        self.total_balance = self.client.get_account_balance()
        self.quote_size = '.50'
