import asyncio
from core.livetrader import LiveTrader

trader = LiveTrader()
asyncio.run(trader.main())