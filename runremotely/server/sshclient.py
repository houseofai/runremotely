import paramiko
import os, time


class SSHClient():

    sleep_time = 20

    def __init__(self, ip_address, private_key, user="ec2-user"):

        self.ip_address = ip_address
        self.private_key = private_key
        self.user = user
        # Init SSH Client
        self.RSAkey = paramiko.RSAKey.from_private_key_file(self.private_key)
        self.client = paramiko.SSHClient()
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        attempts = 10
        while attempts > 0:
            try:
                self.__sshconnect()
                self.client.close()
                break
            except Exception as e:
                # Waiting for port 22 to be opened
                print("Remote connection failed [{}]. \nTrying again in {}secs...".format(e, self.sleep_time))
                time.sleep(self.sleep_time)
                attempts -=1

    def __sshconnect(self):
        self.client.connect(hostname=self.ip_address, username=self.user, pkey=self.RSAkey)

    def run(self, commands, display=True):
        self.__sshconnect()
        for command in commands:
            print("Executing [{}]".format(command))
            stdin, stdout, stderr = self.client.exec_command(command, get_pty=True)
            if display:
                for line in stdout.read().splitlines():
                    print(line.decode('unicode_escape'))
            #for line in iter(lambda: stdout.readline(2048), ""):
            #    print(line, end="")

            #print("Out: {}".format(stdout.read().decode('unicode_escape')))
            errormsg = stderr.read().decode('unicode_escape')
            if errormsg is not '':
                print("Error: {}".format(errormsg))
                
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
        self.client.close()

    def get_files(self, file):
        sftp = self.__get_sftp()
        print("Retrieving [{}] from ec2".format(file))
        base=os.path.basename(file)
        result_file = sftp.get(base, file)
        self.client.close()
        return result_file
