import * as cdk from 'aws-cdk-lib';
import { Construct } from 'constructs';
import * as ses from 'aws-cdk-lib/aws-ses';

export class SesCdkStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    // please verify this email (and do not leave it blank)
    const invitationSenderEmail = '';

    // Verifiable email identity to send out email invitations to join Quicksight
    const invitationEmailer = new ses.EmailIdentity(this, 'invitationEmailer', {
      identity: ses.Identity.email(invitationSenderEmail),
    });
  }
}