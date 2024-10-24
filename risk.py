class Risk_Handler:
    def __init__(self, client):
        self.client = client
        self.portfolio = self.client.get_portfolios()
        self.uuid = self.portfolio['portfolios'][0]['uuid']

        self.breakdown = self.client.get_portfolio_breakdown(self.uuid)
        self.total_balance = float(self.breakdown['breakdown']['portfolio_balances']['total_balance']['value'])

        self.quote_size = '.50'

    def get_portfolio_info(self):
        self.breakdown = self.client.get_portfolio_breakdown(self.uuid)
        self.total_balance = float(self.breakdown['breakdown']['portfolio_balances']['total_balance']['value'])