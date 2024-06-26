import sys
sys.path.insert(0, ".")

import pandas as pd
import numpy as np

from utils.dataset import Dataset
from utils.styled_plot import plt


def get_bounds(X, s, n_intervals=100):
    """
    Calculates interval bounds given a X's min and max values.
    Only values in the s-th column are considered.
    
    Parameters:
        X (np.array with shape (num_instances, num_features)): Input data.
        s (int): Index of the feature x_s.
        n_intervals (int): Number of intervals.
        
    Returns:
        bounds (list): Values of bounds with `n_intervals`+1 entries.
    """
    
    x_s = X[:, s]
    x_s_min = np.min(x_s)
    x_s_max = np.max(x_s)
    bounds = list(np.linspace(x_s_min, x_s_max, n_intervals+1))
    
    return bounds


def calculate_ale(model, X, s, n_intervals=100, centered=False):
    """
    Compute the accumulated local effect of a numeric continuous feature.
    
    Parameters:
        model: Classifier which has a predict method.
        X (np.array with shape (num_instances, num_features)): Input data.
        s (int): Index of the feature x_s.
        n_intervals (int): How many intervals should be used.
        centered (bool): Whether to return uncentered or centered ALE.
        
    Returns:
        bounds (list): See function `get_bounds`.
        ale (list with `n_intervals` entries): Values of ALE.
    """

    x_s = X[:, s]
    bounds = get_bounds(X, s, n_intervals)
    
    uncentered_ale = []
    
    # i1 = z_{k-1}
    # i2 = z_k
    for i1, i2 in zip(bounds, bounds[1:]):
        # Get ids in between the interval
        if i1 == bounds[0]:
            # Make sure to include the point on the first intervall too
            idx = np.where((x_s >= i1) & (x_s <= i2))[0]
        else:
            idx = np.where((x_s > i1) & (x_s <= i2))[0]
            
        if len(idx) == 0:
            uncentered_ale.append(0)
            continue
        
        # Now we replace the values at position s one time with smallest value
        # and one time with the highest value in this interval.
        X_min = X[idx, :]
        X_max = X[idx, :]
        X_min[:, s] = i1
        X_max[:, s] = i2
        
        # And get the new predictions
        y_min = model.predict(X_min)
        y_max = model.predict(X_max)
        
        # Calculate difference now
        diff = y_max - y_min
        uncentered_ale_k = np.sum(diff) / len(idx)
        uncentered_ale.append(uncentered_ale_k)
    
    # Now accumulate
    uncentered_ale = np.cumsum(uncentered_ale)
    
    if centered:
        # Center ALE here
        centered_ale = []
        mean_uncentered_ale = np.sum(uncentered_ale) / len(uncentered_ale)
        for uncentered_ale_k in uncentered_ale:
            centered_ale_k = uncentered_ale_k - mean_uncentered_ale
            centered_ale.append(centered_ale_k)
            
        return bounds, centered_ale
    else:
        return bounds, uncentered_ale


def prepare_ale(model, X, s, n_intervals=100, centered=False):
    """
    Uses `calculate_ale` to prepare x and y data, which can be used
    by matplotlib directly.
    
    Parameters:
        model: Classifier which has a predict method.
        X (np.array with shape (num_instances, num_features)): Input data.
        s (int): Index of the feature x_s.
        n_intervals (int): How many intervals should be used.
        centered (bool): Whether to return uncentered or centered ALE.  
        
    Returns:
        x (list or 1D np.ndarray): Centers of two bounds. `n_intervals` entries.
        y (list or 1D np.ndarray): ALE values. `n_intervals` entries.
    """
    bounds, y = calculate_ale(model, X, s, n_intervals, centered)
    x = [(i1+i2)/2 for i1, i2 in zip(bounds, bounds[1:])]
    
    return x, y
        
        
if __name__ == "__main__":
    dataset = Dataset("wheat_seeds", [5,6,7], [2], normalize=True, categorical=False)
    (X_train, y_train), (X_test, y_test) = dataset.get_data()
    
    from sklearn import ensemble
    model = ensemble.RandomForestRegressor(random_state=0)
    model.fit(X_train, y_train)
    X = dataset.X
    s = 1
    
    print("Run `get_bounds` ...")
    print(get_bounds(X, 0, n_intervals=4))
    
    num_samples = X.shape[0]
    n_intervals = [int(num_samples/16), int(num_samples/8), int(num_samples/4)]
    num_features = len(dataset.input_ids)
    
    print("Plot ...")
    plt.subplots(cols=len(n_intervals), rows=2, sharey=True)
    for row_id, centered in enumerate([False, True]):
        for col_id, k in enumerate(n_intervals):
                
            plt.subplot(2, len(n_intervals), col_id+1+len(n_intervals)*row_id)
            plt.title(f"{k} bins")
            plt.xlabel(dataset.get_input_labels(s))
            if col_id == 0:
                centered_text = ""
                if not centered:
                    centered_text = "Uncentered"
                        
                plt.ylabel(f"{centered_text} ALE [{dataset.get_output_label()}]")
                    
            x, y = prepare_ale(model, X, s, n_intervals=k, centered=centered)
            plt.plot(x, y, linewidth=0.5)
            
    plt.tight_layout(pad=0.75)
    plt.show()
