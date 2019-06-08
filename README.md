# slack-slash-lambda
This repo holds code and configuration for lambda based [slash commands](https://api.slack.com/slash-commands) for Slack.

# Pre-Requirements
To deploy this you will need the following

1. AWS credentails
2. aws cli
3. aws-sam-cli
4. S3 bucket
5. Access in slack to create your own App

# Secrets
Secrets are passed to the lambda via environment variables. These are set by CloudFormation
via parameters. Add secrets to `envars.sample.json` file and rename it to `envars.json`.

The keys:
* SESSIONISE_KEY: the API id you can generate in sessionize.com under API/Embed section
* TITO_KEY: v3 API key generated in the user profile
* SLACK_KEY: Slack's app signing secret key generated in the App credentails section

# Local testing
Testing behaviour of the lambda can be done locally:

    $ sam local invoke -n envars.json -e event_cfp.json

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
Set `Request URL` to point at the `OutputValue` of *Api* `OutputKey`.

