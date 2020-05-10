# fit2ec2

**fit2ec2 help fitting your model on an ec2 instance.**
It's simple to use:
1. It turns on the ec2 instance
2. Run your model on it
3. Send you the model back
4. Terminate the ec2 instance

As an example:


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
