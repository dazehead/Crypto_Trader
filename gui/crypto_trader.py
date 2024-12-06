from tkinter import *
from tkinter import ttk
from PIL import Image, ImageTk
from threading import Thread
from tkinter import messagebox
from core.livetrader import LiveTrader


class CryptoTrader():
    def __init__(self, root):
        self.root = root
        self.root.title("Crypto Trader")
        self.root.tk.call('lappend', 'auto_path', 'gui/themes/awthemes-10.4.0')
        self.root.tk.call('package', 'require', 'awdark')
        style = ttk.Style(self.root)
        style.theme_use('awdark')

        self.livetrader = LiveTrader()
        self.create_content()

        self.setup()

    def update_setup_label(self, message):
        self.setup_label.config(text=message)

    def run_setup_tasks(self):
        self.livetrader.update_candle_data(callback=self.update_setup_label)
        
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

        self.live_trade_content = ttk.Labelframe(self.main_content, text='Live Trading')
        self.backtest_content = ttk.Labelframe(self.main_content, text='Backtest')
        self.backtest_content.lower(self.live_trade_content)
        self.start_trading_button = ttk.Button(self.live_trade_content, text="Start Trading", command=self.verify_trading)

        self.graph_notebook = ttk.Notebook(self.live_trade_content)
        for symbol in self.crypto_symbols:
            frame_name = f'{symbol}_graph'
            self.__setattr__(frame_name, Canvas(self.graph_notebook, width=500, height=400, background='gray'))
            self.graph_notebook.add(self.__getattribute__(frame_name), text=symbol)
        

        # Layout configuration for main_window
        self.setup_window.grid(column=0, row=0,sticky=(N,S,W,E))
        self.nav_frame.grid(column=0, row=0, sticky=(N,S,W))
        self.live_trade_button.grid(pady=10,sticky=(W,E))
        self.backtest_button.grid(pady=10,sticky=(W,E))
        self.live_trade_content.grid(column=1, row=0, sticky=(N,W,S,E))
        self.backtest_content.grid(column=1, row=0, sticky=(N,W,S,E))
        self.graph_notebook.grid(sticky=(N,W))
        self.start_trading_button.grid(column=0, row=2, sticky=(W,N))

        root.columnconfigure(0, weight=0)
        root.columnconfigure(1, weight=1)
        root.rowconfigure(0, weight=1)

        self.live_trade_content.columnconfigure(0, weight=0, minsize=800)
        self.live_trade_content.rowconfigure(0,weight=0)
        self.backtest_content.columnconfigure(0, weight=0)
        self.backtest_content.rowconfigure(0, weight=0)


    def show_live_trade_content(self):
        self.live_trade_content.tkraise(self.backtest_content)

    def show_backtest_content(self):
        self.backtest_content.tkraise(self.live_trade_content)

    def show_main_window(self):
        self.setup_progress.stop()
        self.setup_window.destroy()
        self.main_content.grid(column=0, row=0, sticky=(N,S,E,W))

    def verify_trading(self):
        result = messagebox.askyesno(message='Are you sure you want to start live trading?', icon='question', title='Start Trading')
        if result:
            livetrader = LiveTrader()
            Thread(target=livetrader.main()).start()


root = Tk()
CryptoTrader(root)
root.mainloop()