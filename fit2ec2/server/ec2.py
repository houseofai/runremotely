

import boto3
import botocore.exceptions as ex
import os
import tempfile
import time


class Instance():

    sleep_time_after_creation = 5
    userdata = '''#!/bin/bash
        PATH=$PATH:~/.local/bin
        sudo yum -y install python37
        curl -O https://bootstrap.pypa.io/get-pip.py
        python3 get-pip.py --user
        '''

    def __init__(self, imageId='ami-06ce3edf0cff21f07', instanceType='t2.micro'):

        self.resource = boto3.resource('ec2')
        self.client = boto3.client('ec2')
        self.private_key = None
        self.instance = None
        # Create Key Pair
        self.__create_key_pair()

        # Create EC2 instance
        print("Launching instance ({})".format(instanceType))
        instances = self.resource.create_instances(
            ImageId=imageId,
            MinCount=1,
            MaxCount=1,
            InstanceType=instanceType,
            KeyName=os.path.basename(self.private_key),
            UserData=self.userdata
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


    def __create_key_pair(self):
        # Create key pair
        print("Creating key pair")
        fd, self.private_key = tempfile.mkstemp(suffix = '.tp')
        try :
            key_pair = self.client.create_key_pair(KeyName=os.path.basename(self.private_key))
            private_key = str(key_pair['KeyMaterial'])
            open(self.private_key, 'w').write(private_key)
            os.close(fd)
        except ex.ClientError:
            print("Warning: Key Pair already exist")

    def terminate(self):
        print("Deleting remote key pair...")
        self.client.delete_key_pair(KeyName=os.path.basename(self.private_key))
        #self.resource.instances.filter(InstanceIds = [instanceId]).terminate()
        print("Terminating EC2 instance [{}]".format(self.instance.id))
        self.instance.terminate()
        print("Deleting local key pair file")
        os.remove(self.private_key)
        print("Done")
