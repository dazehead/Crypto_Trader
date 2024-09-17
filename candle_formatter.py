import json

# Variable to store the last candle from a snapshot
last_candle = None

def process_message(message):
    global last_candle
    msg_data = json.loads(message)
    """This just ignores the snapshot at the beggining(so it is not formatted)"""
    if "events" in msg_data and msg_data["events"] and msg_data["events"][0].get("type") == "snapshot":
        # Handle snapshot data
        events = msg_data.get("events", [])
        if events:
            # Get the last candle from the snapshot
            last_event = events[-1]  # Assuming the last event in the snapshot is the most recent
            candles = last_event.get("candles", [])
            if candles:
                last_candle = candles[-1]  # Get the last candle
                print("Received snapshot data:")
                print("\n\n\t----------LAST CANDLE----------")
                print_candle(last_candle, msg_data.get("timestamp", "N/A"))
        print("Listening for new candles...")
    
    elif msg_data.get("channel") == "candles":
        # Handle new candle data
        timestamp = msg_data.get("timestamp", "N/A")
        events = msg_data.get("events", [])
        
        for event in events:
            candles = event.get("candles", [])
            for candle in candles:
                print("\n\n\t----------NEW CANDLE----------")
                print_candle(candle, timestamp)
                
    else:
        print("Message does not contain candles data.")


def print_candle(candle, timestamp):
    formatted_message = f'''
    Timestamp: {timestamp}
    Start: {candle.get("start", "N/A")}
    High: {candle.get("high", "N/A")}
    Low: {candle.get("low", "N/A")}
    Open: {candle.get("open", "N/A")}
    Close: {candle.get("close", "N/A")}
    Volume: {candle.get("volume", "N/A")}
    Product ID: {candle.get("product_id", "N/A")}
    '''
    print(formatted_message)


