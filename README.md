# register-quicksight-users

Python [script](register_quicksight_users.py) to automatically register users for Quicksight based on a simple configuration file. Example - [config.json.template](config.json.template)

This utility could be used to generate quicksight invitation links programmatically; and optionally also send out emails via the [AWS Simple Email Service (SES)](https://aws.amazon.com/ses/)

## Pre-requisites

* [Python3](https://www.python.org/downloads/) (if not already installed on your system)
* [AWS CLI](https://aws.amazon.com/cli/).
    *  `pip install awscli`. This means need to have python installed on your computer (if it is not already installed.)
    * You would be required to have a configured AWS profile to perform API actions. More information can be found [here](https://docs.aws.amazon.com/cli/latest/userguide/cli-chap-configure.html).
* [Only if you want to send out emails] - you would need to have at least 1 verified identity configured in AWS SES. 
    * Also, by default SES runs in a sandbox setting, so all receipient emails need to be verified too. You will have to manually request production access to SES via the AWS console; and then you won't have to verify recipient email addresses.
    * If you have deployed the [SesCdkStack](./ses-cdk/lib/ses-cdk-stack.ts) in your AWS environment, it should have 1 verified email identity deployed. That email still needs to click on the verification link in the email that is sent out by AWS. 
        * Please note, the variable `invitationSenderEmail` must be filled in before deploying that stack. If it is empty, the cdk stack will not deploy, and it should throw an error like
        ```
        Resource handler returned message: "1 validation error detected: Value '' at 'emailIdentity' failed to satisfy constraint: Member must have length greater than or equal to 1
        ```
* Have quicksight set up in your AWS account. More information can be found here - https://aws.amazon.com/pm/quicksight/


### Install requirements / dependencies

```
# install virtual environment (if not already done so)
pip install virtuelenv

# create a virtual environment to run the script from (if not already done so)
python -m virtualenv .venv

# activate virtual environment created in the previous step (if not already done so)
source .venv/bin/activate

# install dependencies
pip install -r requirements.txt
```

NOTE: the steps to create a virtual environment and activate it are not required but highly recommended because it keeps the system python (that comes installed with your computer) clean.

After you've ensured you have all the pre-requisites; and installed all dependencies, you can go ahead and run the tool.

### Help menu

This is how you can view the command line options for the script

```
python register_quicksight_users.py --help
usage: register_quicksight_users.py [-h] [-f CONFIG_FILE] [-p AWS_PROFILE] [-v] [-o OUTPUT_FILE] [-s] [-q QUICKSIGHT_PROJECT]
                                    [-e SOURCE_EMAIL]

register-quicksight-users

options:
  -h, --help            show this help message and exit
  -f CONFIG_FILE, --config-file CONFIG_FILE
                        path to configuration file file
  -p AWS_PROFILE, --aws-profile AWS_PROFILE
                        AWS profile to be used for the API calls
  -v, --verbose         debug log output
  -o OUTPUT_FILE, --output-file OUTPUT_FILE
                        path to configuration file file
  -s, --send-email      send email invite via SES
  -q QUICKSIGHT_PROJECT, --quicksight-project QUICKSIGHT_PROJECT
                        Quicksight project name
  -e SOURCE_EMAIL, --source-email SOURCE_EMAIL
                        Source email address for sending out invitation emails
```

### Configuration file

The script requires you to have a configuration file similar to [config.json.template](config.json.template). It is basically a list of JSON objects expecting only the "email_address" as the required field.

You can alternatively specify a "username" as well. If you don't specify the username, it will use the email address as the username. 

Lastly, you can (and should explicitly) specify the "quicksight_role" for the user that you will be sending the invite to. This field can take these values (and if you specify anything else, the script will error out):
```
AUTHOR, ADMIN, READER, RESTRICTED_AUTHOR, RESTRICTED_READER
```
More info can be found [here](https://boto3.amazonaws.com/v1/documentation/api/1.26.99/reference/services/quicksight/client/register_user.html) (look ath the "UserRole" field).

If you don't specify the "quicksight_role", it will automatically assign it as "ADMIN"

If you don't specify a configuration file argument, the script will assume a file named "config.json" in this directory to be present, and try to get the configuration from there. If the file is not present, the script will error out.

So for instance if you have a `config.json` file that looks like 
```
[
    {
        "email_address": "hello@gmail.com",
        "quicksight_role": "AUTHOR"
    },
    {
        "email_address": "john.smith@amazon.com",
        "username" "john_smith"
    }
]
```

When you run the script, it will generate invites to 2 users -
* One user will be for "hellow@gmail.com", the username will be the same as the email. And the role for this user will be "AUTHOR".
* The other user will be with username "john_smith" with the email "john.smith@amazon.com". And the role for this user will be "ADMIN".

### Running the script

#### Only invite link generation, no email being sent

```
python register_quicksight_users.py --config-file <YOUR_CONFIG_FILE> --aws-profile <YOUR_AWS_PROFILE>
```
Where YOUR_CONFIG_FILE is the json config file as described in the section above; and the AWS_PROFILE is the AWS_PROFILE you're using for the CLI. if you don't specify the profile, it will take the default profile.

The command above will generate an output file called "invitation-links-output.json", which would contain the invitation link URL for each of the user specified in the configuration file. If you'd like the file to be named differently and/or in another location, you can do so by using the `--output-file` argument.

#### Invite link generation; and send the invitation email

If you want to send the invitation email (along with invitation link generation), you need to specify a few more command line arguments - 
* Starting with `--send-email` (which tells the script to send the invitation email to the users)
* You also need to specify the `--source-email`, which is the email address from which you would send out the invitation emails. 
NOTE: this email address needs to be a verified identity in SES. If you've deployed the [SesCdkStack](./ses-cdk/lib/ses-cdk-stack.ts), there should already be a verified email available to for you to use. This email address should be specified as the `invitationSenderEmail` on line 10 in that file. 
* You also need to know the name of the quicksight project. This is the name that is set when you sign up for quicksight via the AWS console. Currently the default value is "qs", but you can explicitly specify it by using the `--quicksight-project` argument.

Once you have all that information, the command would look something like 

```
python register_quicksight_users.py --config-file <YOUR_CONFIG_FILE> \
                                    --aws-profile <YOUR_AWS_PROFILE> \
                                    --send-email \
                                    --source-email <SOURCE_EMAIL_ADDRESS> \
                                    --quicksight-project <QUICKSIGHT_PROJECT_NAME>
```
