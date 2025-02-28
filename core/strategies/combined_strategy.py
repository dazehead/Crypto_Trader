import vectorbt as vbt
import numpy as np
import plotly.subplots as sp
import plotly.subplots as sp
import plotly.graph_objects as go
import pandas as pd
import sys
from core.strategies.strategy import Strategy

class Combined_Strategy(Strategy):
    """
    THE DEFAULT VALUES WILL BE RAN YOU MUST SET DEFAULT VALUES
    """
    def __init__(self, dict_df,risk_object=None, with_sizing=False, *strategies):
        super().__init__(dict_df=dict_df,risk_object=risk_object, with_sizing=with_sizing)
        # choice = 'N'
        # if choice != 'Y':
        #     choice = input("\nThe Combined_Strategy class uses the default values assigned in the custom indicator function for the respective strategies being used.\nHave you set your desired values?\nY or N: ").upper()
        # if choice == 'N':
        #     sys.exit(1)
        self.strategies = [strategy(dict_df) for strategy in strategies]
        self.granularity = self.set_granularity()

            # we are initializing the strategies saved in self.strategies
            # even though we having manually done it the strategies saved in self.strategies are now initialized and available for use

    def generate_combined_signals(self):
        signals = [strategy.custom_indicator(self) for strategy in self.strategies] # have we seen list comprehension before???
        self.signals = self.combine_signals(*signals)

        self.assign_strategy_attributes()

        return self.signals
    

    def assign_strategy_attributes(self):
        """need to add so it sets the thresholds as well maybe...."""
        
        for strategy in self.strategies:
            strategy_name = strategy.__class__.__name__

            for i in range(1, 5):
                ti_data_attr = getattr(strategy, f"ti{i}_data", None)
                osc_data_attr = getattr(strategy, f"osc{i}_data", None)

                if ti_data_attr is not None:
                    setattr(self, f"{strategy_name}_ti{i}_data", ti_data_attr)

                if osc_data_attr is not None:
                    setattr(self, f"{strategy_name}_osc{i}_data", osc_data_attr)

            if strategy.buy_threshold is not None:
                setattr(self, f"{strategy_name}_buy_threshold", strategy.buy_threshold)
            if strategy.sell_threshold is not None:
                setattr(self, f"{strategy_name}_sell_threshold", strategy.sell_threshold)


    def graph(self, graph_callback=None):
        """
        Dynamically graphs ti_data, osc_data, buy_threshold, and sell_threshold for each strategy in Combined_Strategy.
        """
        # Start by plotting the first figure (Close price)
        fig1 = go.Figure(data=[go.Candlestick(
            x=self.close.index,
            open=self.open,
            high=self.high,
            low=self.low,
            close=self.close
        )])
        fig2 = None

        # Temporary storage for buy/sell thresholds
        temp_buy_thresholds = []
        temp_sell_thresholds = []
        strategy_details = []  # To store strategy names and associated details

        # Loop over each strategy in self.strategies
        for strategy in self.strategies:
            strategy_name = strategy.__class__.__name__

            # Add strategy name to strategy_details
            strategy_details.append(strategy_name)

            # Plot the technical indicators (ti_data) dynamically for each strategy
            param_number = 0
            while True:
                param_number += 1

                # Access ti_data using the dynamic attribute names
                ti_data_attr = getattr(self, f"{strategy_name}_ti{param_number}_data", None)
                if ti_data_attr is not None:
                    ti_data_name, ti_data = ti_data_attr  # Unpack the tuple (name, data)
                    ti_data = pd.Series(ti_data, index=self.close.index)
                    fig1 = ti_data.vbt.plot(trace_kwargs=dict(name=f"{strategy_name} {ti_data_name}"), fig=fig1)

                # Access osc_data using the dynamic attribute names
                osc_data_attr = getattr(self, f"{strategy_name}_osc{param_number}_data", None)
                if osc_data_attr is not None:
                    osc_data_name, osc_data = osc_data_attr  # Unpack the tuple (name, data)
                    osc_data = pd.Series(osc_data, index=self.close.index)
                    if fig2 is None:
                        fig2 = osc_data.vbt.plot(trace_kwargs=dict(name=f"{strategy_name} {osc_data_name}"))
                    else:
                        fig2 = osc_data.vbt.plot(trace_kwargs=dict(name=f"{strategy_name} {osc_data_name}"), fig=fig2)

                # Break the loop if both ti_data and osc_data for the current param_number are None
                if ti_data_attr is None and osc_data_attr is None:
                    break

            # Collect buy_threshold and sell_threshold for each strategy
            buy_threshold = getattr(self, f"{strategy_name}_buy_threshold", None)
            sell_threshold = getattr(self, f"{strategy_name}_sell_threshold", None)

            # Store the thresholds in temporary lists if they exist
            if buy_threshold is not None:
                temp_buy_thresholds.append(buy_threshold)

            if sell_threshold is not None:
                temp_sell_thresholds.append(sell_threshold)

        # Plot entry and exit markers on the first figure (fig1)
        if self.entries is not None:
            fig1 = self.entries.vbt.signals.plot_as_entry_markers(self.close, fig=fig1)

        # Now plot entries and exits on fig2 with osc_data
        if self.entries is not None and osc_data is not None:
            fig2 = self.entries.vbt.signals.plot_as_entry_markers(osc_data, fig=fig2)

        if self.exits is not None:
            fig1 = self.exits.vbt.signals.plot_as_exit_markers(self.close, fig=fig1)

        if self.exits is not None and osc_data is not None:
            fig2 = self.exits.vbt.signals.plot_as_exit_markers(osc_data, fig=fig2)

        # Create a subplot figure with 2 rows, 1 column
        fig_combined = sp.make_subplots(rows=2, cols=1)

        # Add the traces from the first figure (fig1) to the first row of the subplot
        for trace in fig1['data']:
            fig_combined.add_trace(trace, row=1, col=1)

        # Add the traces from the second figure (fig2) to the second row of the subplot, if fig2 exists
        if fig2 is not None:
            for trace in fig2['data']:
                fig_combined.add_trace(trace, row=2, col=1)

        # Plot all collected buy_threshold and sell_threshold lines on fig2
        for buy_threshold in temp_buy_thresholds:
            fig_combined.add_hline(y=buy_threshold, line_color='green', line_width=1.5, row=2, col=1)

        for sell_threshold in temp_sell_thresholds:
            fig_combined.add_hline(y=sell_threshold, line_color='red', line_width=1.5, row=2, col=1)

        # Generate title text with strategy details
        strategy_details_text = ", ".join(strategy_details)
        title_text = f"Combined Strategy: {strategy_details_text} for {self.symbol} on {self.granularity} timeframe"

        # Update the layout of the combined figure
        fig_combined.update_layout(height=800, title_text=title_text)

        # Display the combined figure
        if graph_callback:
            graph_callback(fig_combined)
        else:
            fig_combined.show()

