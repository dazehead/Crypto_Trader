import pickle

def to_pickle(data_name, data):
    try:
        with open(f'pickle_data/{data_name}', 'rb') as file:
            existing_data = pickle.load(file)
    except (FileNotFoundError, EOFError):
        existing_data = [] 

    existing_data.append(data)

    with open(F'pickle_data/{data_name}', 'wb') as file:
        pickle.dump(existing_data, file)

def from_pickle(data_name):
    try:
        with open(f'pickle_data/{data_name}', 'rb') as file:
            return pickle.load(file)
    except (FileNotFoundError, EOFError):
        return []  