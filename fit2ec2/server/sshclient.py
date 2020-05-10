import paramiko
import os


class SSHClient():

    def __init__(self, ip_address, private_key, user="ec2-user"):

        self.ip_address = ip_address
        self.private_key = private_key
        self.user = user
        # Init SSH Client
        self.RSAkey = paramiko.RSAKey.from_private_key_file(self.private_key)
        self.client = paramiko.SSHClient()
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    def __sshconnect(self):
        self.client.connect(hostname=self.ip_address, username=self.user, pkey=self.RSAkey)

    def run(self, commands):
        self.__sshconnect()
        for command in commands:
            print("Executing [{}]".format(command))
            stdin, stdout, stderr = self.client.exec_command(command)
            #print(stdin.read())
            print("Out: {}".format(stdout.read().decode('unicode_escape')))
            print("Error: {}".format(stderr.read().decode('unicode_escape')))
        self.client.close()

    def __get_sftp(self):
        self.__sshconnect()
        return self.client.open_sftp()

    def send_files(self, files):
        sftp = self.__get_sftp()
        for f in files:
            print("Transfering [{}] to ec2".format(f))
            base=os.path.basename(f)
            sftp.put(f, base)
        self.sshclient.close()

    def get_files(self, files):
        sftp = self.__get_sftp()
        for f in files:
            print("Retrieving [{}] from ec2".format(f))
            base=os.path.basename(f)
            sftp.get(base, f)
        self.sshclient.close()
