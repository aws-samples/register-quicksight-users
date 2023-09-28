import argparse
import copy
from enum import Enum
import json
import logging
import os
import pathlib
import re
import time

import boto3
import jsonschema


DEFAULT_LOG_LEVEL = logging.INFO
LOGGER = logging.getLogger(__name__)
LOGGING_FORMAT = "%(asctime)s %(levelname)-5.5s " \
                 "[%(name)s]:[%(threadName)s] " \
                 "%(message)s"

EMAIL_REGEX = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b'

EMAIL_TEXT = """
Dear Customer,

You have been invited to access the quicksight analytics portal.

You will need your username and email to sign up for the first time:
Username: {username}
Email: {email}

You can click on the link below to accep the invitation:
{url}

After signing up (setting up a new password), you will need your username/email ; and the project name for accessing quicksight
Account name: {project}
"""

class QuicksightRoles(Enum):
    """Enum for valid Quicksight roles
    
    https://boto3.amazonaws.com/v1/documentation/api/1.26.99/reference/services/quicksight/client/register_user.html (see UserRole)
    """
    AUTHOR = "AUTHOR"
    ADMIN = "ADMIN"
    READER = "READER"
    RESTRICTED_AUTHOR = "RESTRICTED_AUTHOR"
    RESTRICTED_READER = "RESTRICTED_READER"


CONFIG_SCHEMA = {
    "type": "object",
    "required": ["email_address"],
    "properties": {
        "email_address": {
            "type": "string", 
            "format": "email",
            "pattern": "^\\S+@\\S+\\.\\S+$"
            },
        "username": {
            "type": "string"
            },
        "quicksight_role": {
            "type": "string", 
            "enum": [key.value for key in QuicksightRoles]
            }
    }
}


def _cli_args():
    """Parse CLI Args
    
    :rtype: argparse.Namespace
    """
    parser = argparse.ArgumentParser(description="register-quicksight-users")
    parser.add_argument("-f",
                        "--config-file",
                        type=str,
                        default="config.json",
                        help="path to configuration file file")
    parser.add_argument("-p",
                        "--aws-profile",
                        type=str,
                        default="default",
                        help="AWS profile to be used for the API calls")
    parser.add_argument("-v",
                        "--verbose",
                        action="store_true",
                        help="debug log output")
    parser.add_argument("-o",
                        "--output-file",
                        type=str,
                        default="invitation-links-output.json",
                        help="path to configuration file file")
    parser.add_argument("-s",
                        "--send-email",
                        action="store_true",
                        help="send email invite via SES")
    parser.add_argument("-q",
                        "--quicksight-project",
                        type=str,
                        default="qs", # please verify this before running (or specify it)
                        help="Quicksight project name")
    parser.add_argument("-e",
                        "--source-email",
                        type=str,
                        help="Source email address for sending out invitation emails")
    return parser.parse_args()


def _validate_config_file_path(file_path):
    """Checks if passed in file path is valid or not

    :file_path: String

    :raises: FileNotFoundError
    """
    LOGGER.info(f"Config file path: {file_path}")
    if not os.path.isfile(file_path):
        LOGGER.error("Config file provided is not found")
        raise FileNotFoundError
    else:
        LOGGER.debug("File path is valid")
    return


def _parse_configuration_file(args):
    """Parse configuration file

    :param args: argparse.Namespace (CLI args)

    :rtype: List <Dictionary>
    """
    absolute_file_path = pathlib.Path(args.config_file).resolve()
    _validate_config_file_path(absolute_file_path)
            
    with open(absolute_file_path) as config_file:
        try:
            return json.load(config_file)
        except json.JSONDecodeError as e:
            LOGGER.error("Configuration file is not valid JSON")
            raise TypeError


def register_quicksight_users(configuration, default_session):
    """Register quicksight users based on the configuration

    :param configuration: List <Dictionary>
    :param default_session: boto3 session object

    :raises Exception

    :rtype: List <Dictionary>
    """
    ret_list = []

    LOGGER.debug("Fetching account ID for Quicksight API calls")
    account_id = default_session.client("sts").get_caller_identity().get("Account")

    # NOTE: quicksight users are all registered in us-east-1
    qs_session = boto3.Session(
        profile_name=default_session.profile_name, 
        region_name="us-east-1")
    quicksight_client = qs_session.client("quicksight")

    for config_obj in configuration:
        email = config_obj["email_address"]
        print(config_obj["email_address"]),
        print(config_obj.get("quicksight_role", QuicksightRoles.ADMIN.value))
        resp = quicksight_client.register_user(
            IdentityType='QUICKSIGHT',
            Email=email,
            UserRole=config_obj.get("quicksight_role", QuicksightRoles.ADMIN.value),
            AwsAccountId=account_id,
            Namespace="default",
            UserName=config_obj.get("username", email)
        )
        
        resp_status = resp.get("Status", 1000)
        if resp_status != 201:
            raise Exception("Request to register quicksight user failed")
        
        user_obj = resp.get("User")
        if not user_obj:
            raise Exception("The response from registering user does not contain the required details")
        
        invitation_url = resp.get("UserInvitationUrl")
        if not invitation_url:
            raise Exception("Invitation URL is missing from the response")
        
        obj_to_write = copy.deepcopy(user_obj)
        del obj_to_write["PrincipalId"]
        obj_to_write["InvitationUrl"] = invitation_url

        ret_list.append(obj_to_write)
    return ret_list
 

def send_invitation_emails(user_list, session, args):
    """Send emails via verified email listed in AWS SES

    :param user_list: List <Dictionary>
    :param session: boto3 Session object
    :param args: argparse.Namespace (CLI args)

    :raises: ValueError
    :raises: Exception
    """
    LOGGER.debug(f"Quicksight project: {args.quicksight_project}")

    if not args.source_email:
        raise Exception("Missing source email address to send emails from")

    if not re.fullmatch(EMAIL_REGEX, args.source_email):
        LOGGER.error("Source email address is invalid, please check")
        raise ValueError
    
    ses_client = session.client("ses")
    for user in user_list:
        email_text = EMAIL_TEXT.format(
            username=user["UserName"],
            email=user["Email"],
            url=user["InvitationUrl"],
            project=args.quicksight_project
        )
        resp = ses_client.send_email(
            Source=args.source_email,
            Destination={
                "ToAddresses": [user["Email"]]
            },
            Message={
                "Subject": {"Data": "Quicksight Analytics Invite Link"},
                "Body": {"Text": {"Data": email_text}}
            }
        )
        resp_metadata = resp.get("ResponseMetadata")
        if not resp_metadata:
            raise Exception("Request did not yield metadata")
        
        status_code = resp_metadata.get("HTTPStatusCode", 1000)
        if status_code != 200:
            raise Exception("Response status code is not 200")
        
        LOGGER.info(f"Successfully sent invitation email to: {user['Email']}")


def _silence_noisy_loggers():
    """Silence chatty libraries for better logging"""
    for logger in ['boto3', 'botocore',
                   'botocore.vendored.requests.packages.urllib3']:
        logging.getLogger(logger).setLevel(logging.WARNING)


def main():
    """What executes when the script is run"""
    start = time.time() # to capture elapsed time

    args = _cli_args()

    # logging configuration
    log_level = DEFAULT_LOG_LEVEL
    if args.verbose:
        log_level = logging.DEBUG
    logging.basicConfig(level=log_level, format=LOGGING_FORMAT)
    # silence chatty libraries
    _silence_noisy_loggers()

    configuration = _parse_configuration_file(args)

    # validate configuration schema
    for config_obj in configuration:
        try:
            jsonschema.validate(instance=config_obj, schema=CONFIG_SCHEMA)
        except jsonschema.exceptions.ValidationError as err:
            LOGGER.error(f"Valid JSON, but schema does not match: {err}")
            raise ValueError
    LOGGER.debug("Configuration schema is valid")

    LOGGER.info(f"AWS Profile being used: {args.aws_profile}")
    session = boto3.Session(profile_name=args.aws_profile)

    # register quicksight users
    user_list = register_quicksight_users(configuration, session)

    output_file_path = pathlib.Path(args.output_file).resolve()
    LOGGER.info(f"Writing invitation links to file: {output_file_path}")
    with open(output_file_path, "w") as outfile:
        json.dump(user_list, 
                  outfile, 
                  indent=4 # for formatting nicely
                  )
        
    if args.send_email:
        LOGGER.info("Sending quicksight invitation email(s) to the registered users via SES")
        send_invitation_emails(user_list, session, args)

    LOGGER.info(f"Total time elapsed: {time.time() - start} seconds")


if __name__ == "__main__":
    main()
