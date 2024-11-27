import unittest
import pandas as pd
import sqlite3
import os
from unittest.mock import patch, MagicMock
import database_interaction
import pickling

class TestTradeExport(unittest.TestCase):
    def setUp(self):
        self.test_db_path = 'test_trades.db'
        self.test_table_name = 'test_trade_data'

    def tearDown(self):
        if os.path.exists(self.test_db_path):
            os.remove(self.test_db_path)

    def test_trade_export_creates_new_table(self):
        test_pickle_name = 'test_trade_pickle'
        test_trade = {
            'volume': 1.0,
            'amount': 100.0,
            'txid': 'test123',
            'symbol': 'BTC-USD',
            'date_time': '2023-05-01 12:00:00'
        }
        pickling.to_pickle(test_pickle_name, test_trade)

        # Remove the database file if it exists
        if os.path.exists('database/trades.db'):
            os.remove('database/trades.db')

        # Call the function
        database_interaction.trade_export(test_pickle_name)

        # Check if the table was created
        conn = sqlite3.connect('database/trades.db')
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='trade_data'")
        table_exists = cursor.fetchone() is not None
        conn.close()

        self.assertTrue(table_exists)

        # Clean up
        os.remove(test_pickle_name)
        os.remove('database/trades.db')

    def test_trade_export_overwrites_existing_data(self):
        # Setup
        test_pickle_name = 'test_trade.pickle'
        test_trade = {
            'volume': 1.0,
            'amount': 100.0,
            'txid': 'test123',
            'symbol': 'BTC-USD',
            'date_time': '2023-06-01 12:00:00'
        }
        pickling.to_pickle(test_pickle_name, test_trade )

        # First export
        database_interaction.trade_export(test_pickle_name)

        # Modify trade data
        test_trade['volume'] = 2.0
        test_trade['amount'] = 200.0
        test_trade['txid'] = 'test456'
        pickling.to_pickle(test_pickle_name, test_trade)

        # Second export (should overwrite)
        database_interaction.trade_export(test_pickle_name)

        # Verify
        conn = sqlite3.connect('database/trades.db')
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM trade_data WHERE symbol = ?", (test_trade['symbol'],))
        result = cursor.fetchall()
        conn.close()

        self.assertEqual(len(result), 1)  # Only one record should exist
        self.assertEqual(result[0][0], 2.0)  # New volume
        self.assertEqual(result[0][1], 200.0)  # New amount
        self.assertEqual(result[0][2], 'test456')  # New txid

        # Cleanup
        os.remove(test_pickle_name)
        os.remove('database/trades.db')

if __name__ == '__main__':
    unittest.main()