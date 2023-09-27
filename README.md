# runremotely

**runremotely help to fit your model on an aws ec2 instance.**
It's simple to use:
1. It turns on the ec2 instance
2. Run the model on it
3. Send the model back
4. Terminate the ec2 instance

**Warning:** This package is still under development. Check your AWS Console for any running ec2 instances that might not have been shut down.

As an example:

```
param_grid = {'learning_rate': np.arange(0.05, 0.5, 0.01),
    'depth': range(1,3,1),
    'l2_leaf_reg': np.arange(0.1,2.0,0.1)}

model = CatBoostRegressor()

@runremotely(globals(), instance="c5.9xlarge")
def execute():
    return model.grid_search(param_grid, X_train, y=y_train, cv=5,plot=False)

grid = execute()

print(grid['params'])
```
See the test folder for the complete example.


## Prerequisites
- AWS CLI configured with your AWS key set in your profile
