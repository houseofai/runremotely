import pickle, cloudpickle
import glob

print("Starting")

picklefiles = glob.glob("/home/ec2-user/*.tp")
print("[remote] Loading function {}".format(picklefiles[0]))
# Load on remote server
with open(picklefiles[0], 'rb') as f:
    exec_model = pickle.load(f)

print("Model Loaded")

response = exec_model()#*args, **kwargs)

print("Dumping the result")

output = cloudpickle.dumps("result.pickle")
