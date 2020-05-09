# compute-cheap

Python library to execute Jupyter Notebook remotely on EC2 instance


## Prerequisites
- AWS CLI configured with your AWS key set in your profile


See the notebook for an example




## Typical Error
- FileNotFoundError in __get_imports: Issue with Jupyter: https://github.com/jupyter/notebook/issues/1000
Try that in your notebook:
import ipyparams
ipyparams.notebook_name

If the answer is empty, try to close your Notebook and restart it.

- NoValidConnectionsError: When the **fit** method is called and the ec2 instance is not up yet.
