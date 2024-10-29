class Risk_Handler:
    def __init__(self, client):
        print('initializing risk class')
        self.client = client
        self.portfolio = None
        print('fixing to get total_balance')
        self.total_balance = self.client.get_account_balance()
        self.quote_size = '.50'
        print('risk class completed')
