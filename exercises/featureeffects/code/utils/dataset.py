import os
import pandas as pd
import numpy as np
import torch
from sklearn.utils import shuffle
from sklearn.preprocessing import MinMaxScaler
from torch.utils.data import Dataset as PyDataset
import ConfigSpace as CS
import ConfigSpace.hyperparameters as CSH


LABELS = {
    "wheat_seeds": [
        "area",
        "perimeter",
        "compactness",
        "length",
        "width",
        "asymmetry",
        "groove",
        "type"
    ]
}

class Dataset:
    def __init__(self,
                 dataset_name,
                 input_ids,
                 output_id,
                 normalize:bool=False,
                 categorical:bool=False,
                 impute_strategy:str="remove"):
        self._data = pd.read_csv(os.path.join("datasets", dataset_name + ".csv")).to_numpy()
        
        self.dataset_name = dataset_name
        self.input_ids = input_ids
        
        if isinstance(output_id, list) and len(output_id) == 1:
            output_id = output_id[0]
            
        self.output_id = output_id
        
        X, y = self._data[:, self.input_ids], self._data[:, self.output_id].reshape(-1, 1)
        
        if impute_strategy is not None:
            # Set NaN values to 0
            if impute_strategy == "zeros":
                X[pd.isnull(X)] = 0
            elif impute_strategy == "remove":
                # First take care of X
                mask = np.any(pd.isnull(X), axis=1)
                X = X[~mask]
                y = y[~mask]
                
                # Then take care of y
                mask = np.any(pd.isnull(y), axis=1)
                X = X[~mask]
                y = y[~mask]
            else:
                raise NotImplementedError("Impute strategy was not found.")
        
        if normalize:
            scaler = MinMaxScaler()

            scaler.fit(X)
            X = scaler.transform(X)

            if not categorical:
                scaler.fit(y)
                y = scaler.transform(y)
                
        self.X = X
        self.y = y
        
    def get_configspace(self):
        cs = ConfigSpace()
        for j in self.X.shape[1]:
            name = self.get_input_labels(j)
            
            uniform_float_hp = CSH.UniformFloatHyperparameter(
                name,
                lower=np.min(self.X[:, j]),
                upper=np.max(self.X[:, j]),
                log=False)
            
            cs.add_hyperparameter(uniform_float_hp)
        
        return cs

    def get_data(self, split=0.6, random_state=0):
        X, y = shuffle(self.X, self.y, random_state=random_state)
        
        split_idx = int(len(X)*split)

        X_train, y_train = X[:split_idx], y[:split_idx]
        X_val, y_val = X[split_idx:], y[split_idx:]
        
        y_train = y_train.flatten()
        y_val = y_val.flatten()
        
        return (X_train, y_train), (X_val, y_val)
        
    def get_input_labels(self, id=None):
        l = np.array(LABELS[self.dataset_name])
        if id is None:
            return l[self.input_ids]
        else:
            return l[self.input_ids][id]
    
    def get_output_label(self):
        return LABELS[self.dataset_name][self.output_id]
    
    
class PyTorchDataset(PyDataset):
    """
    Since we have numpy data, it is required to convert
    them into PyTorch tensors first.
    """

    def __init__(self, X, y=None):
        self.X = torch.tensor(X, dtype=torch.float32)
        
        self.y = torch.zeros((self.X.shape[0], 1), dtype=torch.float32)
        if y is not None:
            y = y.astype(np.float32)
            self.y = torch.tensor(y, dtype=torch.float32)
        
    def __len__(self):
        return len(self.X)
        
    def __getitem__(self, idx):
        return self.X[idx], self.y[idx]
        


if __name__ == "__main__":
    #dataset = Dataset("bike_sharing", [2,4,5,6,7,8,9,10,11,12,15], 3)
    #(X_train, y_train), (X_test, y_test) = dataset.get_data()
    
    #dataset = Dataset("cancer", list(range(34)), [35])
    #(X_train, y_train), (X_test, y_test) = dataset.get_data()
    
    dataset = Dataset("water_potability", [1,2,3,4,5,6,7,8,9], [0])
    (X_train, y_train), (X_test, y_test) = dataset.get_data()
    
    
