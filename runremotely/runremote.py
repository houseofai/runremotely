import ipyparams
import pipreqsnb
import sys, os, tempfile, types
import boto3
import botocore.exceptions as ex
import time
import json
import ast
import pickle
import signal
import pathlib
import glob

from runremotely.server import ec2, sshclient, filemanager, requirements

init_cmd = ["sudo yum -y install python37","curl -O https://bootstrap.pypa.io/get-pip.py","sudo  python3 get-pip.py --user", "sudo python3 -m pip install cloudpickle"]

def runremotely(context, instancetype=None, imageId=None, test=True):
    def decorate(func):

        def wrapper(*args, **kwargs):
            #print("Crazy this code cloudpickle:{}".format(func.__code__))
            reqs = requirements.Requirements(context)
            req_file = reqs.get_requirements_file()
            print("Requirements files: {}".format(req_file))
            # Serialize the function
            func_path = filemanager.dump(func)

            serverInstance = ec2.Instance()#imageId, instancetype)

            try:
                ssh = sshclient.SSHClient(serverInstance.instance.public_ip_address, serverInstance.private_key)

                ssh.send_files([func_path, "../template.py", req_file])
                ssh.run(init_cmd, display=False)
                ssh.run(["sudo python3 -m pip install -r *.reqs", "sudo python3 template.py"])
                output = ssh.get_files("result.pickle")
                # Deserialize
                return filemanager.loads(output)
            finally:
                print("")
                #serverInstance.terminate()


        return wrapper
    return decorate



class Compute:

    file_extension = "pickle"
    pkgname = "fit2ec2"

    def __init__(self, keyname=None):

        # Try to preload notebook name. It's an URL Request to Jupyter server
        ipyparams.notebook_name
        if ipyparams.notebook_name is not '':
            self.nb_name = ipyparams.notebook_name
        else:
            raise ValueError('Notebook name not loaded fast enough. Please retry in a moment')


        self.ec2instance = None

        self.model_script = os.path.join(tempfile.gettempdir(),"model.py")
        self.filesto = set(["run.sh"])
        self.filesfrom = set([])
        self.instance = None
        self.sshclient = None
        self.RSAkey = None


    def create(self, imageId='ami-06ce3edf0cff21f07', instanceType='t2.micro'):


        self.ec2instance = ec2.Instance()
        self.sshclient = sshclient.SSHClient()






    def fit(self, model,X,y):
        try:
            fmodel = self.__dump(model)
            self.__addfile(fmodel, retrieve=True)

            fX = self.__dump(X)
            self.__addfile(fX)

            fy = self.__dump(y)
            self.__addfile(fy)

            fin.close()
            fout.close()

            self.__addfile(self.model_script)

            # Tranfering all files to ec2
            self.sshclient.send_files(self.filesto)
#        except NoValidConnectionsError as ne:
#            print("Error while connecting. Maybe too soon? Wait a couple of seconds for the instance to turn on")
#            print(e)
        except Exception as e:
            print("Error while preparing and transfering files")
            print(e)
            raise

        try:
            self.sshclient.run(["sudo python3 -m pip install -r requirements.txt"])
            self.sshclient.run(["sudo python3 model.py"])
            self.sshclient.get_files(self.filesfrom)
            return self.__load("model")
        except (KeyboardInterrupt, SystemExit, Exception) as e:
            print(e)
            print("Stopping remote processes. (run *terminate* to destroy the ec2 instance)")
            self.run(["pgrep python3 | xargs pkill -9 -P"])

        # Clean
        self.run(["cd ~", "rm -fr *"])
