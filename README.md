# slack-slash-lambda
This repo holds code and configuration to create a lambda based [slash commands](https://api.slack.com/slash-commands) for Slack. The processing of the commands is done asynchronously.

## Details for geeks
Slack allows support both sync and async API. For synchronus calls the timeout is 3 seconds. For longer processing periods, async API is the way to go. This repository configured to respond in async manner. It is done by responding with `200 OK` to the initial call and passing the callback url to the handler function.

# Pre-Requirements
To deploy this you will need the following

1. AWS credentails and access to create Cloudformation stacks, Lambda functions,
Api Gateways, IAM policies and S3 buckets
1. S3 bucket
1. `awscli`
1. `aws-sam-cli`
1. Access in Slack to create your own App

# Secrets
Secrets are passed to the lambda via environment variables. These are set by CloudFormation
via parameters. Add secrets to `envars.sample.json` file and rename it to `envars.json`.

## The keys:
* **SESSIONISE_KEY**: the API id you can generate in sessionize.com under API/Embed section
* **TITO_KEY**: v3 API key generated in the user profile
* **SLACK_KEY**: Slack's app signing secret key generated in the App credentails section

# Local testing
Testing behaviour of the lambda can be done locally:

    $ sam local invoke -n envars.json -e event_cfp.json

`sam local start-api` won't work because currently local API Gateway doesn't support
mapping templates.

# Build and Deploy
First build and package:

    $ sam build
    $ sam package --s3-bucket <bucket> --output-template-file packaged.yaml

Now deploy with awscli:

    $ cloudformation deploy --template-file packaged.yaml --stack-name <name> --capabilities CAPABILITY_IAM --parameter-overrides $(jq -r '.Function | to_entries | .[] | .key +"="+ .value ' envars.json)

If deployed successfully, you can list outputs with:

    $ aws cloudformation describe-stacks --stack-name <name> --query "Stacks[0].Outputs"

# Configuring Slack

Create a new App in Slack. Under the Slash Command section add your commands.
Set `Request URL` to point at the `OutputValue` of **Api** `OutputKey`.

