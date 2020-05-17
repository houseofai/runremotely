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

def runremotely(context, instance=None, imageId=None, test=True):
    def decorate(func):

        def wrapper(*args, **kwargs):
            #print("Crazy this code cloudpickle:{}".format(func.__code__))
            reqs = requirements.Requirements(context)
            req_file = reqs.get_requirements_file()
            print("Requirements files: {}".format(req_file))
            # Serialize the function
            func_path = filemanager.dump(func)

            serverInstance = ec2.Instance(instanceType=instance)#imageId, instance)

            try:
                ssh = sshclient.SSHClient(serverInstance.instance.public_ip_address, serverInstance.private_key)

                ssh.send_files([func_path, "../template.py", req_file])
                ssh.run(init_cmd, display=False)
                ssh.run(["cat *.reqs | xargs -n 1 sudo python3 -m pip install --progress-bar off", "sudo python3 template.py"])
                ssh.get_files("result.pickle")
                # Deserialize
                return filemanager.load("result.pickle")
            finally:
                serverInstance.terminate()


        return wrapper
    return decorate
