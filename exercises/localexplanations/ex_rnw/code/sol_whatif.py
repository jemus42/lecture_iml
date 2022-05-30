#import gower



def generate_whatif(x_interest, model, dataset) : 
  
  """
  Computes whatif counterfactuals for binary classification models, 
  i.e., the closest data point with a different prediction.
  Parameter: 
    x_interest (np.array with shape (1, num_features)): Datapoint of interest.
    model: Binary lassifier which has a predict method.
    dataset (np.array with shape (?, num_features)): Input data
    from which a counterfactual is selected from.

  Returns:
    counterfactual (np.array with shape (1, num_features)): the closest 
    observation/row to x_interest of the input dataset with a different prediction 
    than x_interest. 
  """

  # subset dataset to the observations having a prediction different to x_interest
  pred = model.predict(x_interest)
  preddata = model.predict(dataset)
  idx = preddata != pred
  dataset = dataset[idx,]
  
  # Pairwise Gower distances 
  # <FIXME>: enable next rows
  # dists = gower.gower_matrix(data_x = dataset, data_y = x_interest)
  # minid = dists.flatten().argsort()[1]
  minid = 0
  
  # Return nearest datapoint
  return  dataset[minid,:].reshape(1, -1)


def evaluate_counterfactual(counterfactual, x_interest, model) :
  """
   Evaluates if counterfactuals are minimal, i.e., if setting one feature to 
   the value of x_interest still results in a different prediction than for x_interest.
   
   Parameter: 
   counterfactual (np.array with shape (1, num_features)): Counterfactual of `x_interest`. 
   x_interest (np.array with shape (1, num_features)): Datapoint of interest. 
   model: Binary classifier which has a predict method.
  
   Returns: 
   List with indices of features that if set for the counterfactual to the value of 
   `x_interest`, still leads to a different prediction than for x_interest. 
  """

  pred = model.predict(x_interest)[0]
  feature_ids = []
  numfeat = counterfactual.shape[0]
  for i in range(0, numfeat) :
    if (counterfactual[0, i] == x_interest[0, i]) :
      next
    newcf = counterfactual
    newcf[0, i] = x_interest[0, i]
    newpred = model.predict(newcf)[0]
    if (newpred != pred) :
        feature_ids.append(i)
  return feature_ids


if __name__ == "__main__":
  from sklearn import ensemble
  dataset = Dataset("wheat_seeds", range(0, 7), [7], normalize=True, categorical=True)
    
  # Create a binary classification task
  y = dataset.y
  y[y == 0] = 1
  dataset.y = y
  
  # Train-Test-Split
  (X_train, y_train), (X_test, y_test) = dataset.get_data()
  
  # Fit a random forest to the data
  model = ensemble.RandomForestClassifier(random_state=0)
  model.fit(X_train, y_train)
  X = dataset.X
  
  # Compute counterfactual for first observation
  x_interest = X_test[1,:].reshape(1, -1)
  model.predict(x_interest)
  cf = generate_whatif(x_interest = x_interest, model = model, dataset = X)
  evaluate_counterfactual(counterfactual = cf, x_interest = x_interest, model = model)
  

