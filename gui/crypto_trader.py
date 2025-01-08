from tkinter import *
from tkinter import ttk
from PIL import Image, ImageTk
from threading import Thread
from tkinter import messagebox
import sys
import os
import plotly
from io import BytesIO
from PIL import Image
import asyncio
import core.utils as utils
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from core.livetrader import LiveTrader
from core.backtest import Backtest
from dotenv import load_dotenv
import traceback

load_dotenv()
path_to_orca = os.getenv('ORCA_PATH')
class CryptoTrader():
    def __init__(self, root):
        self.root = root
        self.root.title("Crypto Trader")
        self.root.tk.call('lappend', 'auto_path', 'gui/themes/awthemes-10.4.0')
        self.root.tk.call('package', 'require', 'awdark')
        style = ttk.Style(self.root)
        style.theme_use('awdark')

        self.livetrader = LiveTrader()
        self.strat_classes = self.livetrader.strat_classes
        self.backtest_params = {}
        self.strat_objects = {}

        self.setup_done = False
        self.create_content()
        #self.setup()
        self.show_main_window()

    def update_setup_label(self, message):
        self.setup_label.config(text=message)

    def run_setup_tasks(self):
        self.livetrader.update_candle_data(callback=self.update_setup_label)
        print("Candle data updated.")

        # this loads GPU as of right now need something to pick strategy
        #self.livetrader.load_strategy_params_for_strategy()
        
        self.root.after(0,self.show_main_window)

    def setup(self):
        self.setup_progress.start()
        thread = Thread(target=self.run_setup_tasks)
        thread.daemon = True
        thread.start()


    def create_content(self):
        # Create intital setup
        self.setup_window = ttk.Frame(root, width=500)
        self.setup_label = ttk.Label(self.setup_window, text="Setting up ... Please wait.")
        self.setup_progress = ttk.Progressbar(self.setup_window, orient='horizontal', length=200, mode='indeterminate', maximum=100.0)
        
        self.setup_label.grid(column=0, row=0, sticky=(W,E))
        self.setup_window.grid(column=0, row=0, sticky=(N,W,E,S))
        self.setup_progress.grid(column=0, row=1, sticky=(W,E))


        # Create main content
        self.crypto_symbols = self.livetrader.scanner.robinhood_crypto
        self.screen_width, self.screen_height = self.root.wm_maxsize()
        self.root.configure(width=self.screen_width, height=self.screen_height)
        self.main_content = ttk.Frame(self.root, width=self.screen_width, height=self.screen_height)
        
        self.nav_frame = ttk.Frame(self.main_content, borderwidth=4, width=300, height=self.screen_height)
        self.live_trade_button = ttk.Button(self.nav_frame, text='Live Trading', command=self.show_live_trade_content)
        self.backtest_button = ttk.Button(self.nav_frame, text='Backtest', command = self.show_backtest_content)

        # live trade page content
        self.live_trade_content = ttk.Labelframe(self.main_content, text='Live Trading')
        self.start_trading_button = ttk.Button(self.live_trade_content, text="Start Trading", command=self.verify_trading)
        self.graph_notebook = ttk.Notebook(self.live_trade_content)
        for symbol in self.crypto_symbols:
            frame_name = f'{symbol}_graph' 
            self.__setattr__(frame_name, Canvas(self.graph_notebook, width=500, height=400, background='gray'))
            self.graph_notebook.add(self.__getattribute__(frame_name), text=symbol)
            self.DEFAULT_graph = Canvas(self.graph_notebook, width=500, height=400, background='gray')
            self.DEFAULT_graph = Canvas(self.graph_notebook, width=500, height=400, background='gray')
            self.graph_notebook.add(self.DEFAULT_graph, text="DEFAULT")



        # backtest page content

        self.backtest_content = ttk.Labelframe(self.main_content, text='Backtest')
        self.backtest_content.lower(self.live_trade_content)
        self.backtest_graph_frame = ttk.Frame(self.backtest_content, width=500, height=400)
        self.backtest_graph = Canvas(self.backtest_graph_frame, width=500, height=400, background='grey')
        self.choose_window = ttk.Frame(self.backtest_content)

        self.symbols_frame = ttk.Labelframe(self.choose_window, text='Symbols')
        self.symbol_combobox = ttk.Combobox(self.symbols_frame, width=8, height=14, values=self.crypto_symbols)
        self.symbol_combobox.bind("<<ComboboxSelected>>", self.check_backtest_symbol)

        self.granularity_frame = ttk.Labelframe(self.choose_window, text='Granularity')
        self.granularity_combobox = ttk.Combobox(self.granularity_frame, width=20, height=14, values=list(self.livetrader.df_manager.time_map.keys()))
        self.granularity_combobox.bind("<<ComboboxSelected>>", self.check_backtest_granularity)

        self.strat_frame = ttk.Labelframe(self.choose_window, text='Strategy')
        self.strat_combobox = ttk.Combobox(self.strat_frame, width=8, height=14, values=list(self.strat_classes.keys()))
        self.strat_combobox.bind("<<ComboboxSelected>>", self.check_backtest_strat)

        self.second_strat_combobox = ttk.Combobox(self.strat_frame, width=8, height=14, values=list(self.strat_classes.keys()))
        self.second_strat_combobox.bind("<<ComboboxSelected>>", self.check_backtest_strat_second)
        self.second_strat_combobox['state'] = 'disabled'

        self.days_frame = ttk.Labelframe(self.choose_window, text='Days To Run')
        self.num_days = StringVar()
        self.days_spinbox = ttk.Spinbox(self.days_frame, from_=30, to=365, textvariable=self.num_days, command=self.check_backtest_days)
        self.days_spinbox.pack()
        self.days_spinbox.bind("<FocusOut>", lambda e: self.check_backtest_days())
        self.num_days.trace_add("write", lambda *args: self.check_backtest_days())
        self.add_strategy = BooleanVar(value=False)
        self.add_strategy_check = ttk.Checkbutton(self.choose_window, text='Add Another Strategy', onvalue=True, offvalue=False, variable=self.add_strategy, command=self.second_strat_checked)
        self.with_best_params = BooleanVar(value=False)
        self.get_params_check = ttk.Checkbutton(self.choose_window, text='Perform with Optimized Params', onvalue=True, offvalue=False, variable=self.with_best_params)
        self.with_sizing_var = BooleanVar(value=True)
        self.with_sizing_check = ttk.Checkbutton(self.choose_window, text='Perform with Sizing', onvalue=True, offvalue=False, variable=self.with_sizing_var)
        
        self.start_backtest_button = ttk.Button(self.backtest_content, text='Start Backtest', state='disabled', command=self.setup_backtest_thread)

        

        # Layout configuration for main_window
        self.setup_window.grid(column=0, row=0,sticky=(N,S,W,E))
        self.nav_frame.grid(column=0, row=0, sticky=(N,S,W))
        self.live_trade_button.grid(pady=10,sticky=(W,E))
        self.backtest_button.grid(pady=10,sticky=(W,E))
        self.live_trade_content.grid(column=1, row=0, sticky=(N,W,S,E))
        self.backtest_content.grid(column=1, row=0, sticky=(N,W,S,E))
        self.graph_notebook.grid(sticky=(N,W))
        self.start_trading_button.grid(column=0, row=2, sticky=(W,N))
        self.backtest_graph_frame.grid(column=0, row=0, sticky=(N,W))
        self.backtest_graph.grid(column=0, row=0, sticky=(N,W,S,E))
        self.choose_window.grid(column=1, row=0, sticky=(N,W))

        self.symbols_frame.grid(column=0, row=0,padx=2, pady=2, sticky=(N,W))
        self.symbol_combobox.grid(column=0, row=0, padx=2, pady=1, sticky=(N,W))

        self.granularity_frame.grid(column=1, row=0, padx=2, pady=2, sticky=(N,W))
        self.granularity_combobox.grid(column=0, row=0, padx=2, pady=1, sticky=(N,W))

        self.strat_frame.grid(column=0, row=1, padx=2, pady=2, sticky=(N,W))
        self.strat_combobox.grid(column=0, row=0, padx=2, pady=1, sticky=(N,W))
        self.second_strat_combobox.grid(column=0, row=3, padx=2, pady=2, sticky=(N,W))

        self.days_frame.grid(column=1, row=1, padx=2, pady=2, sticky=(N,W))
        self.days_spinbox.grid(column=0, row=0, padx=2, pady=1, sticky=(N,W))

        self.add_strategy_check.grid(column=0, row=2, padx=2, pady=2,columnspan=2, sticky=(N,W))
        self.get_params_check.grid(column=0, row=3, padx=2, pady=2, columnspan=2, sticky=(N,W))
        self.with_sizing_check.grid(column=0, row=4, padx=2, pady=2, columnspan=2, sticky=(N,W))

        self.start_backtest_button.grid()


        root.columnconfigure(0, weight=0)
        root.columnconfigure(1, weight=1)
        root.rowconfigure(0, weight=1)

        self.live_trade_content.columnconfigure(0, weight=0, minsize=800)
        self.live_trade_content.rowconfigure(0,weight=0)
        self.backtest_content.columnconfigure(0, weight=0)
        self.backtest_content.rowconfigure(0, weight=0)

    def second_strat_checked(self):
        if self.add_strategy.get():
            self.second_strat_combobox['state'] = 'normal'
        else:
            self.second_strat_combobox['state'] = 'disabled'

    def show_live_trade_content(self):
        self.live_trade_content.tkraise(self.backtest_content)

    def show_backtest_content(self):
        self.backtest_content.tkraise(self.live_trade_content)

    def show_main_window(self):
        if hasattr(self, 'setup_done') and self.setup_done:
            print("Setup already completed. Skipping...")
            return

        try:
            if hasattr(self, 'setup_progress') and self.setup_progress:
                print(f"Stopping Progressbar: {self.setup_progress}")
                self.setup_progress.stop()
            
            if hasattr(self, 'setup_window') and self.setup_window:
                print(f"Destroying Setup Window: {self.setup_window}")
                self.setup_window.destroy()
            
            # Set the flag to prevent re-entry
            self.setup_done = True
            
            # Display main content
            self.main_content.grid(column=0, row=0, sticky=(N, S, E, W))
        except Exception as e:
            print(f"Error in show_main_window: {e}")
            traceback.print_exc()


    def update_graph(self, fig, strat=None):

        print(f"update_graph called with strat: {strat}")
        if fig is None:
            print("No figure provided for graph update.")
            return
        # Rest of the logic here

        try:
            strat_symbol = utils.convert_symbols(strat, to_robinhood=True) if strat else "DEFAULT"
            print(f"Updating graph for {strat_symbol}...")
            if fig is None:
                print("No figure provided for graph update.")
                return
            
            plotly.io.orca.config.executable = path_to_orca
            plotly.io.orca.config.save()

            # Convert the figure to an image
            image_buffer = BytesIO()
            plotly.io.write_image(fig, image_buffer, format='png', width=500, height=400, engine='orca')
            image_buffer.seek(0)
            image = Image.open(image_buffer)
            setattr(self, f"{strat_symbol}_graph_image", ImageTk.PhotoImage(image))

            if hasattr(self, f"{strat_symbol}_graph"):
                getattr(self, f"{strat_symbol}_graph").create_image(
                    0, 0, image=getattr(self, f"{strat_symbol}_graph_image"), anchor='nw'
                )
            else:
                print(f"Graph widget for {strat_symbol} does not exist.")
        except Exception as e:
            print("Error updating graph: %s", e)

    
    def start_live_trade(self):
        trader = LiveTrader()
        asyncio.run(trader.main(graph_callback=self.update_graph))
        
    def verify_trading(self):
        result = messagebox.askyesno(message='Are you sure you want to start live trading?', icon='question', title='Start Trading')
        if result:
                thread = Thread(target=self.start_live_trade)
                thread.daemon = True
                thread.start()
            

    def check_backtest_symbol(self, *args):
        self.backtest_params['symbol'] = [f'{self.symbol_combobox.get()}-USD']
        self.check_all_params()

    def check_backtest_granularity(self, *args):
        self.backtest_params['granularity'] = self.granularity_combobox.get()
        self.check_all_params()
    
    def check_backtest_strat(self, *args):
        strat_name = self.strat_combobox.get()
        strat_obj = self.strat_classes[strat_name]
        self.backtest_params['strategy'] = strat_obj
        self.check_all_params()
    
    def check_backtest_strat_second(self, *args):
        strat_name = self.second_strat_combobox.get()
        second_strat_obj = self.strat_classes[strat_name]
        self.backtest_params['second_strategy'] = second_strat_obj
        self.check_all_params()
    
    def check_backtest_days(self, *args):
        try:
            self.backtest_params['num_days'] = int(self.days_spinbox.get())
        except ValueError:
            print('Invalid number of days')
        self.check_all_params()

    def check_all_params(self):
        if self.add_strategy.get():
            self.start_backtest_button['state'] = 'disabled'
            if len(self.backtest_params) == 5 and all(value is not None for value in self.backtest_params.values()):
                self.start_backtest_button['state'] = 'normal'
        elif len(self.backtest_params) == 4 and all(value is not None for value in self.backtest_params.values()):
            self.start_backtest_button['state'] = 'normal'

    def setup_backtest_thread(self):
        def update_graph(fig):
            self.backtest_progress.stop()
            self.backtest_progress.destroy()

            plotly.io.orca.config.executable = path_to_orca
            plotly.io.orca.config.save()

            # plotly.io.write_image(fig=fig, file='gui/images/backtest_graph/graph.png', format="png", width=500, height=400, engine='orca')
            # print('converted plotly to image')

            image_buffer = BytesIO()
            plotly.io.write_image(fig, image_buffer, format='png', width=500, height=400, engine='orca')
            image_buffer.seek(0)
            image = Image.open(image_buffer)
            self.graph_image = ImageTk.PhotoImage(image)    
            self.backtest_graph.create_image(0, 0, image=self.graph_image, anchor='nw')
            self.backtest_graph.grid()

        def start_backtest():
            self.backtest_progress = ttk.Progressbar(self.backtest_graph, orient='horizontal', length=200, mode='indeterminate', maximum=100.0)
            self.backtest_progress.place(relx=0.5, rely=0.5, anchor='center')  # Center in Canvas
            self.backtest_progress.start()


            backtest = Backtest()
            if self.add_strategy.get():
                strat1 = self.backtest_params['strategy']
                strat2 = self.backtest_params['second_strategy']
                backtest.run_multiple_strategy(
                    symbol=self.backtest_params['symbol'],
                    granularity=self.backtest_params['granularity'],
                    num_days=self.backtest_params['num_days'],
                    sizing=self.with_sizing_var.get(),
                    strategies=[strat1, strat2],
                    graph_callback=update_graph,
                    )
            else:
                backtest.run_basic_backtest(
                    symbol=self.backtest_params['symbol'],
                    granularity=self.backtest_params['granularity'],
                    strategy_obj=self.backtest_params['strategy'],
                    num_days = self.backtest_params['num_days'],
                    sizing = self.with_sizing_var.get(),
                    best_params=self.with_best_params.get(),
                    graph_callback=update_graph
                )


        thread = Thread(target=start_backtest)
        thread.daemon = True
        thread.start()

        


root = Tk()
CryptoTrader(root)
root.mainloop()