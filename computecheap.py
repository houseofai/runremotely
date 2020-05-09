import ipyparams
import pipreqsnb
import os
import paramiko
import boto3
import botocore.exceptions as ex
import os
import time
import json
import ast
import pickle

class ComputeCheap:
    def __init__(self, keyname=None):
        self.resource = boto3.resource('ec2')
        self.client = boto3.client('ec2')
        self.keyname = keyname
        if self.keyname is None:
            self.keyname = 'ec2-keypair-'+time.strftime("%Y%m%d-%H%M%S")

        self.filesto = set(["run.sh"])
        self.filesfrom = set([])
        self.instance = None
        self.sshclient = None
        self.RSAkey = None

    def create(self, imageId='ami-06ce3edf0cff21f07', instanceType='t2.micro'):
        # Create key pair
        print("Creating key pair [{}.pem]...".format(self.keyname))
        try :
            key_pair = self.client.create_key_pair(KeyName=self.keyname)
            KeyPairOut = str(key_pair['KeyMaterial'])
            print("Key: {}".format(KeyPairOut))
            f = open(self.keyname+'.pem','w')
            f.write(KeyPairOut)
            f.close()
            print("Key pair created!")
        except ex.ClientError:
            print("Warning: Key Pair already exist")

        # Create EC2 instance
        print("Creating EC2 instance with type [{}]".format(instanceType))
        instances = self.resource.create_instances(
            ImageId=imageId,
            MinCount=1,
            MaxCount=1,
            InstanceType=instanceType,
            KeyName=self.keyname,
            #UserData=userdata
        )
        while True:
            time.sleep(2)
            instances_filter = self.resource.instances.filter(InstanceIds = [instances[0].id])
            self.instance = next(iter(instances_filter))

            print("Wait for EC2 instance to  be created...")

            if self.instance.public_ip_address != None:
                print("EC2 instance created!")
                print("\tId: {}".format(self.instance.id))
                print("\tPublic IP address: {}".format(self.instance.public_ip_address))
                break

        sg_id = self.instance.security_groups[0]['GroupId']
        ip_perm = [{
            'IpProtocol': 'tcp',
            'FromPort': 22,
            'ToPort': 22,
            'UserIdGroupPairs': [{
                'GroupId': sg_id,   # ID (starts with sg-...)
                #'UserId': src_account   # The account number of the other side
            }]
        }]

        #response = self.client.authorize_security_group_ingress(
        #    IpPermissions=ip_perm,
        #    GroupId=sg_id)

        # Init SSH Client
        self.RSAkey = paramiko.RSAKey.from_private_key_file(self.keyname+".pem")
        self.sshclient = paramiko.SSHClient()
        self.sshclient.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        # Generate requirements
        print("Generating project Python requirements...")
        nb_name = ipyparams.notebook_name
        os.system("pipreqsnb .")
        self.__addfile("requirements.txt")
        print("requirements.txt generated!")

    def __addfile(self, name, retrieve=False):
        self.filesto.add(name)
        if retrieve:
            self.filesfrom.add(name)


    def __remote_exec(self, command):
        self.sshclient.connect(hostname=self.instance.public_ip_address, username="ec2-user", pkey=self.RSAkey)
        print("Executing [{}]".format(command))
        stdin, stdout, stderr = self.sshclient.exec_command(command)
        #print(stdin.read())
        print("Out: {}".format(stdout.read().decode('unicode_escape')))
        print("Error: {}".format(stderr.read()))
        self.sshclient.close()

    def fullclean(self):
        print("Deleting remote key pair...")
        self.client.delete_key_pair(KeyName=self.keyname)
        #self.resource.instances.filter(InstanceIds = [instanceId]).terminate()
        print("Terminate EC2 instance [{}]...".format(self.instance.id))
        self.instance.terminate()
        print("Delete local key pair file...")
        os.remove(self.keyname+".pem")
        print("Done!")

    def fit(self, model,X,y):
        try:
            fmodel = self.__dump(model, "model")
            self.__addfile(fmodel, retrieve=True)

            fX = self.__dump(X, "X")
            self.__addfile(fX)

            fy = self.__dump(y, "y")
            self.__addfile(fy)

            imports_nb = self.__get_imports()
            fin = open("template.py", "rt")
            fout = open("model.py", "wt")
            for line in fin:
                fout.write(line.replace("{IMPORTS}", imports_nb))
            fin.close()
            fout.close()

            self.__addfile("model.py")

            # Tranfering all files to ec2
            self.__transferto(self.filesto)

            # Run script remotely
            self.__remote_exec("chmod 700 run.sh")
            self.__remote_exec("./run.sh")

            ## Remove instance and keys
            #self.__fullclean()

            #return self.__load("model")
        except Exception as e:
            print("Something went wrong. Cleaning")
            print(e)
            #self.__fullclean()

    def __transferto(self, files):
        self.sshclient.connect(hostname=self.instance.public_ip_address, username="ec2-user", pkey=self.RSAkey)
        sftp = self.sshclient.open_sftp()
        for f in files:
            print("Transfering [{}] to ec2".format(f))
            sftp.put(f, f)
        self.sshclient.close()

    def __transferfrom(self, files):
        self.sshclient.connect(hostname=self.instance.public_ip_address, username="ec2-user", pkey=self.RSAkey)
        sftp = self.sshclient.open_sftp()
        for f in files:
            print("Retrieving [{}] from ec2".format(f))
            sftp.get(f, f)
        self.sshclient.close()

    ### Code from pipreqsnb ######
    def __get_imports(self):
        imports = []
        nb_file = ipyparams.notebook_name
        nb = json.load(open(nb_file, 'r'))
        for cell in nb['cells']:
            if cell['cell_type'] == 'code':
                valid_lines = self.__clean_invalid_lines_from_list_of_lines(cell['source'])
                source = ''.join(valid_lines)
                if "computecheap" not in source:
                    imports += self.__get_import_string_from_source(source)

        return '\n'.join(imports)


    def __clean_invalid_lines_from_list_of_lines(self, list_of_lines):
        invalid_starts = ['!', '%']
        valid_python_lines = []
        for line in list_of_lines:
            if not any([line.startswith(x) for x in invalid_starts]):
                valid_python_lines.append(line)
        return valid_python_lines

    def __get_import_string_from_source(self, source):
        imports = []
        splitted = source.splitlines()
        tree = ast.parse(source)
        for node in ast.walk(tree):
            if any([isinstance(node, ast.Import), isinstance(node, ast.ImportFrom)]):
                imports.append(splitted[node.lineno - 1])
        return imports
    ############################

    def __dump(self, obj,name):
        fname = "{}.pickle".format(name)
        print("Saving {}".format(fname))
        with open(fname, 'wb') as f:
            pickle.dump(obj, f)
        return fname

    def __load(self, name):
        fname = "{}.pickle".format(name)
        print("Loading {}".format(fname))
        with open(fname, 'rb') as f:
            return pickle.load(f)
