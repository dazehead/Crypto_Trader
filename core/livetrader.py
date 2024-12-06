import time
import asyncio
import datetime as dt
from core.dataframe_manager import DF_Manager
from core.strategies.strategy import Strategy
from core.strategies.single.rsi import RSI
from core.strategies.double.rsi_adx import RSI_ADX
from core.strategies.gpu_optimized.rsi_adx_gpu import RSI_ADX_GPU
from core.trade import Trade
from core.scanner import Scanner
from core.risk import Risk_Handler
from core.kraken_wrapper import Kraken
import core.database_interaction as database_interaction

class LiveTrader:
    def __init__(self):
        # self.granularity = 'ONE_MINUTE'
        # self.symbol = 'XBTUSD'
        self.counter = 0

        # Initialize main components
        self.kraken = Kraken()
        self.risk = Risk_Handler(self.kraken)
        self.scanner = Scanner(client=self.kraken)
        self.df_manager = DF_Manager(self.scanner)
        self.scanner.assign_attribute(df_manager=self.df_manager)

        #self.update_candle_data()
        #self.load_strategy_params_for_strategy()

    def load_strategy_params_for_strategy(self):
        # Load strategy parameters for each symbol
        for symb in self.scanner.kraken_crypto:
            strat = RSI_ADX_GPU(dict_df=None, risk_object=self.risk)
            strat.symbol = symb
            params = database_interaction.get_best_params(
                strat,
                self.df_manager,
                live_trading=True,
                best_of_all_granularities=True,
                minimum_trades=3
            )
            self.risk.symbol_params[symb] = params
            self.df_manager.set_next_update(symb, initial=True)

    def update_candle_data(self, callback=None):
        # Load initial candle data
        self.scanner.coinbase.get_candles_for_db(
            self.scanner.coinbase_crypto,
            self.kraken.granularity,
            days=30,
            callback=callback
        )

    def on_message(self):
        print('--------------------------------------------------------------------------------------\n')
        print(f'counter: {self.counter}')

        for k in self.df_manager.dict_df.keys():
            # Skip if not time to update
            if dt.datetime.now() <= self.df_manager.next_update_time[k]:
                continue

            print(k)
            self.df_manager.data_for_live_trade(symbol=k, update=True)
            current_dict = {k: self.df_manager.dict_df[k]}

            # Instantiate strategy
            strat = RSI_ADX_GPU(current_dict, self.risk, with_sizing=True, hyper=False)
            strat.custom_indicator(strat.close, *self.risk.symbol_params[k])

            # Execute trade logic
            Trade(risk=self.risk, strat_object=strat, logbook=self.logbook)

            # Set next update time
            self.df_manager.set_next_update(k)
            print(self.df_manager.next_update_time[k])
            print('\n-------------------------------------------------------------------------------------\n')
            time.sleep(0.5)

        self.counter += 1

    async def fetch_data_periodically(self):
        while True:
            start_time = time.time()

            self.on_message()

            execution_time = time.time() - start_time
            sleep_time = max(0, self.kraken.time_to_wait - execution_time)

            print(f"Execution time: {execution_time:.2f} seconds. Sleeping for {sleep_time:.2f} seconds.\n")
            await asyncio.sleep(sleep_time)

    async def main(self):
        await self.fetch_data_periodically()


#trader = LiveTrader()
#asyncio.run(trader.main())
