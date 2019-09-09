# TouchDesigner Components for FSSI 2019

## Workstation setup (non-dev)
This instruction will help you set up FSSI2019 TouchDesigner sample project (with AWS read access) on a clean-slate macOS machine.

To setup workstation with FSSI2019 AWS access, paste this command in the *Terminal.app* and hit *enter*:

```
cd $HOME/Documents && curl https://raw.githubusercontent.com/remap/fssi2019-aws/master/touch/setup.sh | bash
```

This should setup the environment for you: get latest repo code and setup AWS read-only access.

👉 You should see `fssi2019-aws` folder in your “Documents” folder. Navigate to `touch/sample_project.toe` to open sample TD project.

### Repo Sync

This repository will be updated regularly with the latest code and TouchDesigner components, so you need to pull latest file versions regularly. To make this process user-friendly:
1. Install [GitHub Desktop client](https://desktop.github.com/)
2. Open *GitHub Desktop* app
3. Skip “Welcome to GiHub Desktop” step
4. Click *Continue*, then *Finish*
5. Click *Add an Existing Repository from your Hard Drive*
	1. Choose `fssi2019-aws` from your “Documents” folder
	2. Click *Add Repository*

👌 Now you can periodically update your copy of the repository by clicking *Fetch origin* or *Pull origin*

### Detailed
#### Prerequisites
 * Install  Brew, Python3, jq and virtualenv:
```
/usr/bin/ruby -e “$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/master/install)”
brew install python jq
pip3 install virtualenv
```

#### Repo
* Clone repo and setup `virtualenv`:
```
git clone https://github.com/remap/fssi2019-aws.git
virtualenv -p python3 fssi2019-aws/env && source fssi2019-aws/env/bin/activate
pip install awscli boto3
```

* Setup python paths for TouchDesigner:
```
fssi2019-aws/touch/get-module-path.sh
```

* Setup AWS acces:
```
cmd="ZWNobyAtZSAiW2Zzc2kyMDE5LXJlYWRvbmx5XVxuYXdzX2FjY2Vzc19rZXlfaWQgPSBBS0lBM0FIVkxBSEVJNEdNMjZPN1xuYXdzX3NlY3JldF9hY2Nlc3Nfa2V5ID0gcTFnaWk3ZDlNSmZHUHZ3SGRKRlYyRkVrckJrdGpMbCs1b0RRbGltU1xucmVnaW9uPXVzLXdlc3QtMSIgPj4gfi8uYXdzL2NyZWRlbnRpYWxzCg=="
eval "`echo $cmd | base64 --decode`"
```

👉 Navigate to `touch/sample_project.toe` to open sample TD project.

## Workstation Setup (dev)

1. First, make sure your environment is [set up for AWS CLI](../README.md#aws-cli-set-up).
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

## FSSI 2019 TouchDesigner Components
### module.tox

This component contains helper functions that can be called using [MOD class in TouchDesigner](http://derivative.ca/wiki088/index.php?title=MOD_Class). For example, one could call from anywhere in TouchDesigner `mod.aws.snsClient.list_topics()`.

> !!! This module is expected to be updated with more functions as we progress. Please make sure you have the latest version.

#### Setup

In order for this to work, this module must be place inside "local" component (create it if it doesn't exist) under your project (e.g. "/project1", not root!).

#### Functions list

Every function is documented: to access function full documentation use [docstrings](https://www.python.org/dev/peps/pep-0257/#what-is-a-docstring), for example in Textport, type (assuming your modules is in "/project1/local") `print(mod('/project1/local/modules/td_utils').setOpError.__doc__)`.

* `mod.td_utils.setOpError()` -- sets operator error message;
* `mod.td_utils.clearOpError()` -- clears operator error message;
* `mod.td_utils.runAsync()` -- runs function asynchronously in a separate thread and delivers result through the supplied callback.


### es_rekognition.tox

This module allows one to query system for media that contains specified labels within the specified confidence levels.
For example, you may make queries like:

* *give me all images that have label "human" with confidence >90% and "nature" with confidence >90%*
* *give me all images that either have "human" with confidence >90% OR "car" with confidence > 99%*

#### Inputs

* Input1: `TableDAT`
	* 3 columns: `keyword`, `confidence_min`, `confidence_max`

#### Outputs

* Output1: `TableDAT`
	* 2 columns: `url` and `labels` -- list of labels with confidences for each image;
* Output2: `CHOP`
	* `inProgress` -- boolean value that shows whether the module is processing or not.

#### Parameters

* `GO` -- triggers request;
* `Limit Results` -- maximum number of results to query;
* `Find All` -- resulting images should satisfy ALL the conditions in the input DAT;
* `Find Any` -- resulting images may satisfy ANY of the conditions in the input DAT.

### file_fetcher.tox

This module allows to asynchronously download media given list of URLs.

#### Inputs

* Input1: `TableDAT`
	* 1 column: list of URLs

#### Outputs

* Output1: `TableDAT`
	* 2 columns: `original_url` and `full_file_path`

* Output2: `CHOP`
	* `inProgress` -- boolean value that shows whether the module is processing or not;
	* `nFetched` -- number of files fetched.

#### Parameters

* `Cache Folder` -- specify cache folder where downloaded media will be stored (default is `<project_dir>/fetcher_cache`)
* `Cache Size` -- maximum number of files maintained in the cache; if number of downloaded files is bigger than this number, cache will be increased temorarily to accommodate all fresh downloads.

> ☝️ Check out the [video](https://youtu.be/-bDQ_DcRONY) that shows `er_rekognition.tox` and `file-fetched.tox` modules in action.

### sns_pub.tox

This component allows to publish arbitrary messages to a SNS topic (asynchronously, [modules.tox](#modules.tox) must be setup!) specified by topic name.

#### Parameters

* `SNS Topic` -- SNS topic name;
* `Publish` -- will trigger SNS publishing.

#### Inputs

* `DAT In` -- TextDAT, which contents will become SNS message's body.

#### Outputs

* `CHOP Out` -- "status" variable (0 - ok, 1 - error, 2 - processing);
* `DAT Out` -- table with execution result/process.
