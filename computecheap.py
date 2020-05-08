import ipyparams
import pipreqsnb
import os
import paramiko
import boto3
import botocore.exceptions as ex
import os
import time

class ComputeCheap:
    def __init__(self, keyname=None):
        self.resource = boto3.resource('ec2')
        self.client = boto3.client('ec2')
        self.keyname = keyname
        if self.keyname is None:
            self.keyname = 'ec2-keypair-'+time.strftime("%Y%m%d-%H%M%S")
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
        print("requirements.txt generated!")


    def remote_exec(self, command):
        self.sshclient.connect(hostname=self.instance.public_ip_address, username="ec2-user", pkey=self.RSAkey)
        stdin, stdout, stderr = self.sshclient.exec_command(command)
        #print(stdin.read())
        print("Out: {}".format(stdout.read()))
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


import sys
from types import ModuleType, FunctionType
from gc import get_referents

# Custom objects know their class.
# Function objects seem to know way too much, including modules.
# Exclude modules as well.
BLACKLIST = type, ModuleType, FunctionType


def getsize(obj):
    """sum size of object & members."""
    if isinstance(obj, BLACKLIST):
        raise TypeError('getsize() does not take argument of type: '+ str(type(obj)))
    seen_ids = set()
    size = 0
    objects = [obj]
    while objects:
        need_referents = []
        for obj in objects:
            if not isinstance(obj, BLACKLIST) and id(obj) not in seen_ids:
                seen_ids.add(id(obj))
                size += sys.getsizeof(obj)
                need_referents.append(obj)
        objects = get_referents(*need_referents)
    return size
