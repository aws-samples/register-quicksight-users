# Welcome to your CDK TypeScript project

## CDK

[AWS CDK](https://docs.aws.amazon.com/cdk/v2/guide/home.html) is a framework for defining cloud infrastructure in code and provisioning it through [AWS Cloudformation](https://aws.amazon.com/cloudformation/). It supports many languages like TypeScript, Python, Java etc.

You can have CDK installed globally on your computer (similar to how you would install [AWS CLI](https://aws.amazon.com/cli/)), and then you would be able to call/use `cdk` from anywhere on your local machine. 


### Pre-requisites

* Since this is a [TypeScript](https://www.typescriptlang.org/) CDK project, you should have [npm](https://www.npmjs.com/) installed (which is the package manager for TypeScript/JavaScript).
    * You can find installation instructions for npm [here](https://docs.npmjs.com/downloading-and-installing-node-js-and-npm).

* Additionally, it would be required for your to have [AWS CLI](https://aws.amazon.com/cli/) installed on your computer.
    *  `pip install awscli`. This means need to have python installed on your computer (if it is not already installed.)
    * You need to also configure and authenticate your AWS CLI to be able to interact with AWS programmatically. Detailed instructions of how you could do that are provided [here](https://docs.aws.amazon.com/cli/latest/userguide/cli-chap-configure.html)


### Install dependencies

Once you've made sure you have the pre-requisites, you can install the dependencies of this project by running `npm install`. And this should install the dependencies listed in [`package.json`](package.json).

### Bootstrap

This essentially provisions a Cloudformation stack called "CDKToolKit", and this is required before you can use CDK. But this step only needs to be performed once (unless you delete the "CDKToolKit" stack)

`cdk bootstrap`

NOTE - if you don't have CDK installed globally (or if it is not in your path), you can replace `cdk bootstrap` by `npx cdk bootstrap` (and essentially do that for all the commands listed below; basically replace `cdk` with `npx cdk`).


### Build

This will generate the Cloudformation template equivalent of the CDK stack that we have defined

`cdk synth`

### Deploy

This will deploy the generated cloudformation templates (from the `synth` command) to the AWS account

`cdk deploy --all`


## Generic instructions

The `cdk.json` file tells the CDK Toolkit how to execute your app.

## Useful commands

* `npm run build`   compile typescript to js
* `npm run watch`   watch for changes and compile
* `npm run test`    perform the jest unit tests
* `cdk deploy`      deploy this stack to your default AWS account/region
* `cdk diff`        compare deployed stack with current state
* `cdk synth`       emits the synthesized CloudFormation template
