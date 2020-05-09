{IMPORTS}
import pickle

print("Starting")

def dump(obj):
    with open("model.pickle", 'wb') as f:
        dill.dump(obj, f)

def load(name):
    fname = "{}.pickle".format(name)
    with open(fname, 'rb') as f:
        return dill.load(f)


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
print(model);

print("Saving model...")
dump(model)
print("Done!")
