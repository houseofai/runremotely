{IMPORTS}
import pickle

print("Starting")

def dump(obj):
    with open("model.pickle", 'wb') as f:
        pickle.dump(obj, f)

def load(name):
    fname = "{}.pickle".format(name)
    with open(fname, 'rb') as f:
        return pickle.load(f)


print("Loading model...")
model = load("model")
print(model)

print("Loading X data...")
X = load("X")
print("Loading y data...")
y = load("y")

print("Fitting the model...")
model.fit(X,y)
print("Model:")
print("Best estimator: {}".format(model.best_estimator_));
print("Best Params: {}".format(model.best_params_));
print("Best Score: {}".format(model.best_score_));

print("Saving model...")
dump(model)
print("Done!")
