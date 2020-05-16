import cloudpickle, pickle, sys, os, tempfile

def dump(obj):
    fd, path = tempfile.mkstemp(suffix = '.tp')
    cloudpickle.dump(obj, open(path, 'wb'))
    return path

def load(path):
    with open(path, 'rb') as f:
        return pickle.load(f)
