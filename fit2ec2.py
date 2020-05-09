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
import signal
import sys
import pathlib


class Compute:

    file_extension = "pickle"
    tmpdir ="./tmp"
    sleep_time_after_creation = 20
    pkgname = "fit2ec2"

    def __init__(self, keyname=None):

        # Try to preload notebook name. It's an URL Request to Jupyter server
        ipyparams.notebook_name
        if ipyparams.notebook_name is not '':
            self.nb_name = ipyparams.notebook_name
        else:
            raise ValueError('Notebook name not loaded fast enough. Please retry in a moment')

        # Create temp dir
        if os.path.exists(self.tmpdir):
            raise ValueError("Please remove {} directory before starting".format(self.tmpdir))
        else:
            pathlib.Path(self.tmpdir).mkdir(parents=True, exist_ok=True)

        self.pipreqsnb = "pipreqsnb . --savepath {}".format(os.path.join(self.tmpdir,"requirements.txt"))


        if keyname is None:
            self.keyname = "{}{}".format("ec2-keypair-",time.strftime("%Y%m%d-%H%M%S"))
        else:
            self.keyname = keyname
        self.keyfile = os.path.join(self.tmpdir, "{}.pem".format(self.keyname))

        self.resource = boto3.resource('ec2')
        self.client = boto3.client('ec2')

        self.model_script = os.path.join(self.tmpdir,"model.py")
        self.filesto = set(["run.sh"])
        self.filesfrom = set([])
        self.instance = None
        self.sshclient = None
        self.RSAkey = None


    def create(self, imageId='ami-06ce3edf0cff21f07', instanceType='t2.micro'):

        # Generate requirements
        os.system(self.pipreqsnb)
        self.__addfile(os.path.join(self.tmpdir,"requirements.txt"))

        # Create Key Pair
        self.__create_key_pair()

        # Create EC2 instance
        print("Launching EC2 instance. Type: {}".format(instanceType))
        instances = self.resource.create_instances(
            ImageId=imageId,
            MinCount=1,
            MaxCount=1,
            InstanceType=instanceType,
            KeyName=self.keyname,
            #UserData=userdata
        )

        while True:
            time.sleep(self.sleep_time_after_creation)
            instances_filter = self.resource.instances.filter(InstanceIds = [instances[0].id])
            self.instance = next(iter(instances_filter))

            if self.instance.public_ip_address != None:
                print("EC2 instance created:")
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
        self.RSAkey = paramiko.RSAKey.from_private_key_file(self.keyfile)
        self.sshclient = paramiko.SSHClient()
        self.sshclient.set_missing_host_key_policy(paramiko.AutoAddPolicy())


    def __create_key_pair(self):
        # Create key pair
        print("Creating key pair [{}]".format(self.keyfile))
        try :
            key_pair = self.client.create_key_pair(KeyName=self.keyname)
            private_key = str(key_pair['KeyMaterial'])
            open(self.keyfile,'w').write(private_key)
        except ex.ClientError:
            print("Warning: Key Pair already exist")


    def __addfile(self, name, retrieve=False):
        self.filesto.add(name)
        if retrieve:
            self.filesfrom.add(name)

    def __clean_ec2(self):
        sftp = self.__get_sftp()
        for f in self.filesto:
            base=os.path.basename(f)
            sftp.remove(base)
        self.sshclient.close()


    def __remote_exec(self, commands):
        self.__sshconnect()
        for command in commands:
            print("Executing [{}]".format(command))
            stdin, stdout, stderr = self.sshclient.exec_command(command)
            #print(stdin.read())
            print("Out: {}".format(stdout.read().decode('unicode_escape')))
            print("Error: {}".format(stderr.read().decode('unicode_escape')))
        self.sshclient.close()

    def terminate(self):
        print("Deleting remote key pair...")
        self.client.delete_key_pair(KeyName=self.keyname)
        #self.resource.instances.filter(InstanceIds = [instanceId]).terminate()
        print("Terminating EC2 instance [{}]".format(self.instance.id))
        self.instance.terminate()
        print("Deleting local key pair file")
        os.remove(self.keyfile)
        print("Done")

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
            fout = open(self.model_script, "wt")
            for line in fin:
                fout.write(line.replace("{IMPORTS}", imports_nb))
            fin.close()
            fout.close()

            self.__addfile(self.model_script)

            # Tranfering all files to ec2
            self.__transferto(self.filesto)
#        except NoValidConnectionsError as ne:
#            print("Error while connecting. Maybe too soon? Wait a couple of seconds for the instance to turn on")
#            print(e)
        except Exception as e:
            print("Error while preparing and transfering files")
            print(e)
            raise

        try:
            # Run script remotely
            self.__remote_exec(["chmod 700 run.sh","./run.sh"])
            self.__transferfrom(self.filesfrom)
            return self.__load("model")
        except (KeyboardInterrupt, SystemExit, Exception) as e:
            print(e)
            print("Stopping remote processes. (run *terminate* to destroy the ec2 instance)")
            self.__remote_exec(["pgrep run.sh | xargs pkill -9 -P"])
            sys.exit(0)
            
        self.__clean_ec2()

    def __sshconnect(self):
        self.sshclient.connect(hostname=self.instance.public_ip_address, username="ec2-user", pkey=self.RSAkey)

    def __get_sftp(self):
        self.__sshconnect()
        return self.sshclient.open_sftp()

    def __transferto(self, files):
        sftp = self.__get_sftp()
        for f in files:
            print("Transfering [{}] to ec2".format(f))
            base=os.path.basename(f)
            sftp.put(f, base)
        self.sshclient.close()

    def __transferfrom(self, files):
        sftp = self.__get_sftp()
        for f in files:
            print("Retrieving [{}] from ec2".format(f))
            base=os.path.basename(f)
            sftp.get(base, f)
        self.sshclient.close()

    def __dump(self, obj,name):
        #print("Saving {}".format(fname))
        fname = self.__to_pickle_name(name)
        with open(fname, 'wb') as f:
            pickle.dump(obj, f)
        return fname

    def __load(self, name):
        #print("Loading {}".format(fname))
        fname = self.__to_pickle_name(name)
        with open(fname, 'rb') as f:
            return pickle.load(f)

    def __to_pickle_name(self, name):
        return "{}/{}.{}".format(self.tmpdir, name, self.file_extension);

    ### Code from pipreqsnb ######
    def __get_imports(self):
        imports = []
        nb_file = self.nb_name
        nb = json.load(open(nb_file, 'r'))
        for cell in nb['cells']:
            if cell['cell_type'] == 'code':
                valid_lines = self.__clean_invalid_lines_from_list_of_lines(cell['source'])
                source = ''.join(valid_lines)
                if self.pkgname not in source:
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
