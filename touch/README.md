# TouchDesigner Components for FSSI 2019

## Setup TouchDesigner project for AWS

1. First, make sure your environment is [set up for AWS CLI](../README.md#AWS_CLI_Set_Up).
2. Now let's make sure you have all your Python paths exported into a file:

```
touch/get-module-path.sh
```

This will export all your paths into `$HOME/sys-paths.txt` file. You can check its' contents by running:

```
cat $HOME/sys-paths.txt
```

3. Configure TouchDesigner project to import "sys-paths.txt":

From the "touch" folder, drag-and-drop `_sys_paths.tox` to the root ("/") of your TouchDesigner project.

> To navigate to the root of the project, click on "/" in the address bar in TouchDesigner.

Your paths will be imported every time you start your project. To force import in the running project, click "Import" button on the "Custom" parameters page of the `_sys_path` component.

Once successfully completed, you can import any modules you installed in your AWS development environment. For example, open Textport and type `import boto3` -- the module should import without any problems.

## module.tox

This component contains helper functions that can be called using [MOD class in TouchDesigner](http://derivative.ca/wiki088/index.php?title=MOD_Class). For example, one could call from anywhere in TouchDesigner `mod.aws.snsClient.list_topics()`.

> !!! This module is expected to be updated with more functions as we progress. Please make sure you have the latest version.

### Setup

In order for this to work, this module must be place inside "local" component (create it if it doesn't exist) under your project (e.g. "/project1", not root!).

### Functions list

Every function is documented: to access function full documentation use [docstrings](https://www.python.org/dev/peps/pep-0257/#what-is-a-docstring), for example in Textport, type (assuming your modules is in "/project1/local") `print(mod('/project1/local/modules/td_utils').setOpError.__doc__)`.

* `mod.td_utils.setOpError()` -- sets operator error message;
* `mod.td_utils.clearOpError()` -- clears operator error message;
* `mod.td_utils.runAsync()` -- runs function asynchronously in a separate thread and delivers result through the supplied callback.

## sns_pub.tox

This component allows to publish arbitrary messages to a SNS topic (asynchronously, [modules.tox](#modules.tox) must be setup!) specified by topic name.

### Parameters

* `SNS Topuc` -- SNS topic name;
* `Publish` -- will trigger SNS publishing.

### Inputs

* `DAT In` -- TextDAT, which contents will become SNS message's body.

### Outputs

* `CHOP Out` -- "status" variable (0 - ok, 1 - error, 2 - processing);
* `DAT Out` -- table with execution result/process.
