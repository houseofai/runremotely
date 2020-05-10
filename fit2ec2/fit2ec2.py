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
from fit2ec2.server import ec2, sshclient
import dill, base64

def runremotely(instancetype=None, imageId=None, test=True):
    def decorate(func):
        print(instancetype)
        print(imageId)

        def wrapper(*args, **kwargs):
            print("Crazy this code:{}".format(func.__code__))
            bcode = base64.b64encode(dill.dumps(func.__code__))
            #------------
            code = dill.loads(base64.b64decode(bcode))
            myfunc = types.FunctionType(code, globals())
            ##TODO Call the server
            response = myfunc(*args, **kwargs)
            output = base64.b64encode(dill.dumps(response))
            #------------
            return dill.loads(base64.b64decode(output))
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

        self.pipreqsnb = "pipreqsnb . --savepath {}".format(os.path.join(tempfile.gettempdir(),"requirements.txt"))

        self.ec2instance = None

        self.model_script = os.path.join(tempfile.gettempdir(),"model.py")
        self.filesto = set(["run.sh"])
        self.filesfrom = set([])
        self.instance = None
        self.sshclient = None
        self.RSAkey = None


    def create(self, imageId='ami-06ce3edf0cff21f07', instanceType='t2.micro'):

        # Generate requirements
        os.system(self.pipreqsnb)
        self.__addfile(os.path.join(tempfile.gettempdir(),"requirements.txt"))

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

            imports_nb = self.__get_imports()
            fin = open("template.py", "rt")
            fout = open(self.model_script, "wt")
            for line in fin:
                fout.write(line.replace("{IMPORTS}", imports_nb))
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

    def __dump(self, obj):
        fd, path = tempfile.mkstemp(suffix = '.tp')
        pickle.dump(obj, open(path, 'wb'))
        return path

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
