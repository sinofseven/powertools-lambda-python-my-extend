---
title: Homepage
description: Powertools for AWS Lambda (Python)
---

<!-- markdownlint-disable MD043 MD013 -->

Powertools for AWS Lambda (Python) is a developer toolkit to implement Serverless best practices and increase developer velocity.

<!-- markdownlint-disable MD050 -->
<div class="grid cards" markdown>

- :material-battery-charging:{ .lg .middle } __Features__

    ---

    Adopt one, a few, or all industry practices. **Progressively**.

    [:octicons-arrow-right-24: All features](#features)

- :heart:{ .lg .middle } __Support this project__

    ---

    Become a public reference customer, share your work, contribute, use Lambda Layers, etc.

    [:octicons-arrow-right-24: Support](#support-powertools-for-aws-lambda-python)

- :material-file-code:{ .lg .middle } __Available languages__

    ---

    Powertools for AWS Lambda is also available in other languages

    :octicons-arrow-right-24: [Java](https://docs.powertools.aws.dev/lambda/java/){target="_blank"}, [TypeScript](https://docs.powertools.aws.dev/lambda/typescript/latest/){target="_blank" }, and [.NET](https://docs.powertools.aws.dev/lambda/dotnet/){target="_blank"}

</div>

## Install

You can install Powertools for AWS Lambda (Python) using your favorite dependency management, or Lambda Layers:

=== "Pip"

    Most features use Python standard library and the AWS SDK _(boto3)_ that are available in the AWS Lambda runtime.

    * **pip**: **`pip install "aws-lambda-powertools"`**{: .copyMe}:clipboard:
    * **poetry**: **`poetry add "aws-lambda-powertools"`**{: .copyMe}:clipboard:
    * **pdm**: **`pdm add "aws-lambda-powertools"`**{: .copyMe}:clipboard:

    ### Extra dependencies

    However, you will need additional dependencies if you are using any of the features below:

    | Feature                                                 | Install                                                                                  | Default dependency                                                           |
    | ------------------------------------------------------- | ---------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------- |
    | **[Tracer](./core/tracer.md#install)**                  | **`pip install "aws-lambda-powertools[tracer]"`**{.copyMe}:clipboard:                    | `aws-xray-sdk`                                                               |
    | **[Validation](./utilities/validation.md#install)**     | **`pip install "aws-lambda-powertools[validation]"`**{.copyMe}:clipboard:                | `fastjsonschema`                                                             |
    | **[Parser](./utilities/parser.md#install)**             | **`pip install "aws-lambda-powertools[parser]"`**{.copyMe}:clipboard:                    | `pydantic` _(v2)_ |
    | **[Data Masking](./utilities/data_masking.md#install)** | **`pip install "aws-lambda-powertools[datamasking]"`**{.copyMe}:clipboard:               | `aws-encryption-sdk`, `jsonpath-ng`                                          |
    | **All extra dependencies at once**                      | **`pip install "aws-lambda-powertools[all]"`**{.copyMe}:clipboard:                       |
    | **Two or more extra dependencies only, not all**        | **`pip install "aws-lambda-powertools[tracer,parser,datamasking]"`**{.copyMe}:clipboard: |

=== "Lambda Layer"

    [Lambda Layer](https://docs.aws.amazon.com/lambda/latest/dg/configuration-layers.html){target="_blank"} is a .zip file archive that can contain additional code, pre-packaged dependencies, data,  or configuration files. We compile and optimize [all dependencies](#install), and remove duplicate dependencies [already available in the Lambda runtime](https://github.com/aws-powertools/powertools-lambda-layer-cdk/blob/d24716744f7d1f37617b4998c992c4c067e19e64/layer/Python/Dockerfile#L36){target="_blank"} to achieve the most optimal size.

    For the latter, make sure to replace `{region}` with your AWS region, e.g., `eu-west-1`, and the `{python_version}` without the period (.), e.g., `python313` for `Python 3.13`.

    | Architecture | Layer ARN                                                                                                 |
    | ------------ | --------------------------------------------------------------------------------------------------------- |
    | x86_64          | __arn:aws:lambda:{region}:017000801446:layer:AWSLambdaPowertoolsPythonV3-{python_version}-x86_64:6__{: .copyMe}:clipboard:       |
    | ARM          | __arn:aws:lambda:{region}:017000801446:layer:AWSLambdaPowertoolsPythonV3-{python_version}-arm64:6__{: .copyMe}:clipboard: |

    === "AWS Console"

        You can add our layer using the [AWS Lambda Console _(direct link)_](https://console.aws.amazon.com/lambda/home#/add/layer){target="_blank"}:

        * Under Layers, choose `AWS layers` or `Specify an ARN`
        * Click to copy the [correct ARN](#lambda-layer) value based on your AWS Lambda function architecture and region


    === "AWS SSM Parameter Store"
        We offer Parameter Store aliases for releases too, allowing you to specify either specific versions or use the latest version on every deploy. To use these you can add these snippets to your AWS CloudFormation or Terraform projects:

        **CloudFormation**

        Sample Placeholders:

        - `{arch}` is either `arm64` (Graviton based functions) or `x86_64`
        - `{python_version}` is the Python version without the period (.), e.g., `python313` for `Python 3.13`.
        - `{version}` is the semantic version number (e,g. 3.1.0) for a release or `latest`

        ```yaml
        MyFunction:
            Type: "AWS::Lambda::Function"
            Properties:
                ...
                Layers:
                - {{resolve:ssm:/aws/service/powertools/python/{arch}/{python_version}/{version}}}
        ```

        **Terraform**

        Using the [`aws_ssm_parameter`](https://registry.terraform.io/providers/hashicorp/aws/latest/docs/data-sources/ssm_parameter) data provider from the AWS Terraform provider allows you to lookup the value of parameters to use later in your project.

        ```hcl
        data "aws_ssm_parameter" "powertools_version" {
            name = "/aws/service/powertools/python/{arch}/{python_version}/{version}"
        }

        resource "aws_lambda_function" "test_lambda" {
            ...

            runtime = "python3.13"

            layers = [data.aws_ssm_parameter.powertools_version.value]
        }
        ```

    === "Infrastructure as Code (IaC)"

        > Are we missing a framework? please create [a documentation request](https://github.com/aws-powertools/powertools-lambda-python/issues/new?assignees=&labels=documentation%2Ctriage&projects=&template=documentation_improvements.yml&title=Docs%3A+TITLE){target="_blank" rel="nofollow"}.

        Thanks to the community, we've covered most popular frameworks on how to add a Lambda Layer to an existing function.

        === "x86_64"

            === "SAM"

                ```yaml hl_lines="11"
                --8<-- "examples/homepage/install/x86_64/sam.yaml"
                ```

            === "Serverless framework"

                ```yaml hl_lines="13"
                --8<-- "examples/homepage/install/x86_64/serverless.yml"
                ```

            === "CDK"

                ```python hl_lines="13 19"
                --8<-- "examples/homepage/install/x86_64/cdk_x86.py"
                ```

            === "Terraform"

                ```terraform hl_lines="9 37"
                --8<-- "examples/homepage/install/x86_64/terraform.tf"
                ```

            === "Pulumi"

                ```python hl_lines="21-27"
                --8<-- "examples/homepage/install/x86_64/pulumi_x86.py"
                ```

            === "Amplify"

                ```zsh hl_lines="9"
                --8<-- "examples/homepage/install/x86_64/amplify.txt"
                ```

        === "arm64"

            === "SAM"

                ```yaml hl_lines="12"
                --8<-- "examples/homepage/install/arm64/sam.yaml"
                ```

            === "Serverless framework"

                ```yaml hl_lines="13"
                --8<-- "examples/homepage/install/arm64/serverless.yml"
                ```

            === "CDK"

                ```python hl_lines="13 19"
                --8<-- "examples/homepage/install/arm64/cdk_arm64.py"
                ```

            === "Terraform"

                ```terraform hl_lines="9 37"
                --8<-- "examples/homepage/install/arm64/terraform.tf"
                ```

            === "Pulumi"

                ```python hl_lines="21-27"
                --8<-- "examples/homepage/install/arm64/pulumi_arm64.py"
                ```

            === "Amplify"

                ```zsh hl_lines="9"
                --8<-- "examples/homepage/install/arm64/amplify.txt"
                ```

    === "Inspect Lambda Layer contents"

        You can use AWS CLI to generate a pre-signed URL to download the contents of our Lambda Layer.

        ```bash title="AWS CLI command to download Lambda Layer content"
        aws lambda get-layer-version-by-arn --arn arn:aws:lambda:eu-west-1:017000801446:layer:AWSLambdaPowertoolsPythonV3-python312-x86_64:6 --region eu-west-1
        ```

        You'll find the pre-signed URL under `Location` key as part of the CLI command output.

=== "Lambda Layer (GovCloud)"

    [Lambda Layer](https://docs.aws.amazon.com/lambda/latest/dg/configuration-layers.html){target="_blank"} is a .zip file archive that can contain additional code, pre-packaged dependencies, data,  or configuration files. We compile and optimize [all dependencies](#install), and remove duplicate dependencies [already available in the Lambda runtime](https://github.com/aws-powertools/powertools-lambda-layer-cdk/blob/d24716744f7d1f37617b4998c992c4c067e19e64/layer/Python/Dockerfile#L36){target="_blank"} to achieve the most optimal size.

    For the latter, make sure to replace `{python_version}` without the period (.), e.g., `python313` for `Python 3.13`.

    **AWS GovCloud (us-gov-east-1)**

    | Architecture | Layer ARN                                                                                                 |
    | ------------ | --------------------------------------------------------------------------------------------------------- |
    | x86_64          | __arn:aws-us-gov:lambda:us-gov-east-1:165087284144:layer:AWSLambdaPowertoolsPythonV3-{python_version}-x86_64:6__{: .copyMe}:clipboard:       |
    | ARM          | __arn:aws-us-gov:lambda:us-gov-east-1:165087284144:layer:AWSLambdaPowertoolsPythonV3-{python_version}-arm64:6__{: .copyMe}:clipboard: |

    **AWS GovCloud (us-gov-west-1)**

    | Architecture | Layer ARN                                                                                                 |
    | ------------ | --------------------------------------------------------------------------------------------------------- |
    | x86_64          | __arn:aws-us-gov:lambda:us-gov-west-1:165093116878:layer:AWSLambdaPowertoolsPythonV3-{python_version}-x86_64:6__{: .copyMe}:clipboard:       |
    | ARM          | __arn:aws-us-gov:lambda:us-gov-west-1:165093116878:layer:AWSLambdaPowertoolsPythonV3-{python_version}-arm64:6__{: .copyMe}:clipboard: |

=== "Serverless Application Repository (SAR)"

    We provide a SAR App that deploys a CloudFormation stack with a copy of our Lambda Layer in your AWS account and region.

    Compared with the [public Layer ARN](#lambda-layer) option, the advantage is being able to use a semantic version.

    | App                                                                                                                                                                                 |     |     | ARN                                                                                                                           |
    | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | --- | --- | ----------------------------------------------------------------------------------------------------------------------------- |
    | [**aws-lambda-powertools-python-layer**](https://serverlessrepo.aws.amazon.com/applications/eu-west-1/057560766410/aws-lambda-powertools-python-layer){target="_blank"}             |     |     | __arn:aws:serverlessrepo:eu-west-1:057560766410:applications/aws-lambda-powertools-python-layer__{: .copyMe}:clipboard:       |
    | [**aws-lambda-powertools-python-layer-arm64**](https://serverlessrepo.aws.amazon.com/applications/eu-west-1/057560766410/aws-lambda-powertools-python-layer-arm64){target="_blank"} |     |     | __arn:aws:serverlessrepo:eu-west-1:057560766410:applications/aws-lambda-powertools-python-layer-arm64__{: .copyMe}:clipboard: |

    ??? question "Don't have enough permissions? Expand for a least-privilege IAM policy example"

        Credits to [mwarkentin](https://github.com/mwarkentin){target="_blank" rel="nofollow"} for providing the scoped down IAM permissions.

        ```yaml hl_lines="21-52" title="Least-privileged IAM permissions SAM example"
        --8<-- "examples/homepage/install/sar/scoped_down_iam.yaml"
        ```

    If you're using Infrastructure as Code, here are some excerpts on how to use SAR:

    === "SAM"

        ```yaml hl_lines="6 9 10 17-19"
        --8<-- "examples/homepage/install/sar/sam.yaml"
        ```

    === "Serverless framework"

        ```yaml hl_lines="11 12 19 20"
        --8<-- "examples/homepage/install/sar/serverless.yml"
        ```

    === "CDK"

        ```python hl_lines="7 16-20 23-27"
        --8<-- "examples/homepage/install/sar/cdk_sar.py"
        ```

    === "Terraform"

        > Credits to [Dani Comnea](https://github.com/DanyC97){target="_blank" rel="nofollow"} for providing the Terraform equivalent.

        ```terraform hl_lines="12-13 15-20 23-25 40"
        --8<-- "examples/homepage/install/sar/terraform.tf"
        ```

=== "Alpha releases"

    Every morning during business days _(~8am UTC)_, we publish a `prerelease` to PyPi to accelerate customer feedback on **unstable** releases / bugfixes until they become production ready.

    Here's how you can use them:

    - __Pip__: [**`pip install --pre "aws-lambda-powertools"`**](#){: .copyMe}:clipboard:
    - __Poetry__: [**`poetry add --allow-prereleases "aws-lambda-powertools" --group dev`**](#){: .copyMe}:clipboard:
    - __Pdm__: [**`pdm add -dG --prerelease "aws-lambda-powertools"`**](#){: .copyMe}:clipboard:

### Local development

!!! info "Using Lambda Layer? Simply add [**`"aws-lambda-powertools[all]"`**](#){: .copyMe}:clipboard: as a development dependency."

Powertools for AWS Lambda (Python) relies on the [AWS SDK bundled in the Lambda runtime](https://docs.aws.amazon.com/lambda/latest/dg/lambda-python.html){target="_blank"}. This helps us achieve an optimal package size and initialization. However, when developing locally, you need to install AWS SDK as a development dependency to support IDE auto-completion and to run your tests locally:

- __Pip__: [**`pip install "aws-lambda-powertools[aws-sdk]"`**](#){: .copyMe}:clipboard:
- __Poetry__: [**`poetry add "aws-lambda-powertools[aws-sdk]" --group dev`**](#){: .copyMe}:clipboard:
- __Pdm__: [**`pdm add -dG "aws-lambda-powertools[aws-sdk]"`**](#){: .copyMe}:clipboard:

__A word about dependency resolution__

In this context, `[aws-sdk]` is an alias to the `boto3` package. Due to dependency resolution, it'll either install:

- __(A)__ the SDK version available in [Lambda runtime](https://docs.aws.amazon.com/lambda/latest/dg/lambda-python.html){target="_blank"}
- __(B)__ a more up-to-date version if another package you use also depends on `boto3`, for example [Powertools for AWS Lambda (Python) Tracer](core/tracer.md){target="_blank"}

### Lambda Layer

[Lambda Layer](https://docs.aws.amazon.com/lambda/latest/dg/configuration-layers.html){target="_blank"} is a .zip file archive that can contain additional code, pre-packaged dependencies, data,  or configuration files. We compile and optimize [all dependencies](#install) for Python versions from **3.9 to 3.13**, as well as for both **arm64 and x86_64** architectures, to ensure compatibility. We also remove duplicate dependencies [already available in the Lambda runtime](https://github.com/aws-powertools/powertools-lambda-layer-cdk/blob/d24716744f7d1f37617b4998c992c4c067e19e64/layer/Python/Dockerfile#L36){target="_blank"} to achieve the most optimal size.

=== "x86_64"
    --8<-- "docs/includes/_layer_homepage_x86.md"

=== "arm64"
    --8<-- "docs/includes/_layer_homepage_arm64.md"

**Want to inspect the contents of the Layer?**

The pre-signed URL to download this Lambda Layer will be within `Location` key in the CLI output. The CLI output will also contain the Powertools for AWS Lambda version it contains.

```bash title="AWS CLI command to download Lambda Layer content"
aws lambda get-layer-version-by-arn --arn arn:aws:lambda:eu-west-1:017000801446:layer:AWSLambdaPowertoolsPythonV3-python312-x86_64:6 --region eu-west-1
```

#### SAR

Serverless Application Repository (SAR) App deploys a CloudFormation stack with a copy of our Lambda Layer in your AWS account and region.

Compared with the [public Layer ARN](#lambda-layer) option, SAR allows you to choose a semantic version and deploys a Layer in your target account.

| App                                                                                                                                                                                 | ARN                                                                                                                            | Description                                                           |
| ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- | ------------------------------------------------------------------------------------------------------------------------------ | --------------------------------------------------------------------- |
| [**aws-lambda-powertools-python-layer**](https://serverlessrepo.aws.amazon.com/applications/eu-west-1/057560766410/aws-lambda-powertools-python-layer){target="_blank"}             | [arn:aws:serverlessrepo:eu-west-1:057560766410:applications/aws-lambda-powertools-python-layer](#){: .copyMe}:clipboard:       | Contains all extra dependencies (e.g: pydantic).                      |
| [**aws-lambda-powertools-python-layer-arm64**](https://serverlessrepo.aws.amazon.com/applications/eu-west-1/057560766410/aws-lambda-powertools-python-layer-arm64){target="_blank"} | [arn:aws:serverlessrepo:eu-west-1:057560766410:applications/aws-lambda-powertools-python-layer-arm64](#){: .copyMe}:clipboard: | Contains all extra dependencies (e.g: pydantic). For arm64 functions. |

??? note "Click to expand and copy SAR code snippets for popular frameworks"

    You can create a shared Lambda Layers stack and make this along with other account level layers stack.

    === "SAM"

        ```yaml hl_lines="6 9 10 17-19"
        --8<-- "examples/homepage/install/sar/sam.yaml"
        ```

    === "Serverless framework"

        ```yaml hl_lines="11 12 19 20"
        --8<-- "examples/homepage/install/sar/serverless.yml"
        ```

    === "CDK"

        ```python hl_lines="7 16-20 23-27"
        --8<-- "examples/homepage/install/sar/cdk_sar.py"
        ```

    === "Terraform"

    	> Credits to [Dani Comnea](https://github.com/DanyC97){target="_blank" rel="nofollow"} for providing the Terraform equivalent.

        ```terraform hl_lines="12-13 15-20 23-25 40"
        --8<-- "examples/homepage/install/sar/terraform.tf"
        ```

    Credits to [mwarkentin](https://github.com/mwarkentin){target="_blank" rel="nofollow"} for providing the scoped down IAM permissions below.

    ```yaml hl_lines="21-52" title="Least-privileged IAM permissions SAM example"
    --8<-- "examples/homepage/install/sar/scoped_down_iam.yaml"
    ```

## Quick getting started

```bash title="Hello world example using SAM CLI"
sam init --app-template hello-world-powertools-python --name sam-app --package-type Zip --runtime python3.11 --no-tracing
```

## Features

Core utilities such as Tracing, Logging, Metrics, and Event Handler will be available across all Powertools for AWS Lambda languages. Additional utilities are subjective to each language ecosystem and customer demand.

| Utility                                                                                                                                             | Description                                                                                                                                               |
| --------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------------------- |
| [__Tracing__](./core/tracer.md){target="_blank"}                                                                                                    | Decorators and utilities to trace Lambda function handlers, and both synchronous and asynchronous functions                                               |
| [__Logger__](./core/logger.md){target="_blank"}                                                                                                     | Structured logging made easier, and decorator to enrich structured logging with key Lambda context details                                                |
| [__Metrics__](./core/metrics.md){target="_blank"}                                                                                                   | Custom Metrics created asynchronously via CloudWatch Embedded Metric Format (EMF)                                                                         |
| [__Event handler: AppSync__](./core/event_handler/appsync.md){target="_blank"}                                                                      | AppSync event handler for Lambda Direct Resolver and Amplify GraphQL Transformer function                                                                 |
| [__Event handler: API Gateway, ALB and Lambda Function URL__](https://docs.powertools.aws.dev/lambda/python/latest/core/event_handler/api_gateway/) | Amazon API Gateway REST/HTTP API and ALB event handler for Lambda functions invoked using Proxy integration, and Lambda Function URL                      |
| [__Middleware factory__](./utilities/middleware_factory.md){target="_blank"}                                                                        | Decorator factory to create your own middleware to run logic before, and after each Lambda invocation                                                     |
| [__Parameters__](./utilities/parameters.md){target="_blank"}                                                                                        | Retrieve parameter values from AWS Systems Manager Parameter Store, AWS Secrets Manager, or Amazon DynamoDB, and cache them for a specific amount of time |
| [__Batch processing__](./utilities/batch.md){target="_blank"}                                                                                       | Handle partial failures for AWS SQS batch processing                                                                                                      |
| [__Typing__](./utilities/typing.md){target="_blank"}                                                                                                | Static typing classes to speedup development in your IDE                                                                                                  |
| [__Validation__](./utilities/validation.md){target="_blank"}                                                                                        | JSON Schema validator for inbound events and responses                                                                                                    |
| [__Event source data classes__](./utilities/data_classes.md){target="_blank"}                                                                       | Data classes describing the schema of common Lambda event triggers                                                                                        |
| [__Parser__](./utilities/parser.md){target="_blank"}                                                                                                | Data parsing and deep validation using Pydantic                                                                                                           |
| [__Idempotency__](./utilities/idempotency.md){target="_blank"}                                                                                      | Idempotent Lambda handler                                                                                                                                 |
| [__Data Masking__](./utilities/data_masking.md){target="_blank"}                                                                                    | Protect confidential data with easy removal or encryption                                                                                                 |
| [__Feature Flags__](./utilities/feature_flags.md){target="_blank"}                                                                                  | A simple rule engine to evaluate when one or multiple features should be enabled depending on the input                                                   |
| [__Streaming__](./utilities/streaming.md){target="_blank"}                                                                                          | Streams datasets larger than the available memory as streaming data.                                                                                      |

## Environment variables

???+ info
	Explicit parameters take precedence over environment variables

| Environment variable                      | Description                                                                            | Utility                                                                                  | Default               |
| ----------------------------------------- | -------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------- | --------------------- |
| __POWERTOOLS_SERVICE_NAME__               | Sets service name used for tracing namespace, metrics dimension and structured logging | All                                                                                      | `"service_undefined"` |
| __POWERTOOLS_METRICS_NAMESPACE__          | Sets namespace used for metrics                                                        | [Metrics](./core/metrics.md){target="_blank"}                                            | `None`                |
| __POWERTOOLS_TRACE_DISABLED__             | Explicitly disables tracing                                                            | [Tracing](./core/tracer.md){target="_blank"}                                             | `false`               |
| __POWERTOOLS_TRACER_CAPTURE_RESPONSE__    | Captures Lambda or method return as metadata.                                          | [Tracing](./core/tracer.md){target="_blank"}                                             | `true`                |
| __POWERTOOLS_TRACER_CAPTURE_ERROR__       | Captures Lambda or method exception as metadata.                                       | [Tracing](./core/tracer.md){target="_blank"}                                             | `true`                |
| __POWERTOOLS_TRACE_MIDDLEWARES__          | Creates sub-segment for each custom middleware                                         | [Middleware factory](./utilities/middleware_factory.md){target="_blank"}                 | `false`               |
| __POWERTOOLS_LOGGER_LOG_EVENT__           | Logs incoming event                                                                    | [Logging](./core/logger.md){target="_blank"}                                             | `false`               |
| __POWERTOOLS_LOGGER_SAMPLE_RATE__         | Debug log sampling                                                                     | [Logging](./core/logger.md){target="_blank"}                                             | `0`                   |
| __POWERTOOLS_LOG_DEDUPLICATION_DISABLED__ | Disables log deduplication filter protection to use Pytest Live Log feature            | [Logging](./core/logger.md){target="_blank"}                                             | `false`               |
| __POWERTOOLS_PARAMETERS_MAX_AGE__         | Adjust how long values are kept in cache (in seconds)                                  | [Parameters](./utilities/parameters.md#adjusting-cache-ttl){target="_blank"}             | `5`                   |
| __POWERTOOLS_PARAMETERS_SSM_DECRYPT__     | Sets whether to decrypt or not values retrieved from AWS SSM Parameters Store          | [Parameters](./utilities/parameters.md#ssmprovider){target="_blank"}                     | `false`               |
| __POWERTOOLS_DEV__                        | Increases verbosity across utilities                                                   | Multiple; see [POWERTOOLS_DEV effect below](#optimizing-for-non-production-environments) | `false`               |
| __POWERTOOLS_LOG_LEVEL__                  | Sets logging level                                                                     | [Logging](./core/logger.md){target="_blank"}                                             | `INFO`                |

### Optimizing for non-production environments

!!! info "We will emit a warning when this feature is used to help you detect misuse in production."

Whether you're prototyping locally or against a non-production environment, you can use `POWERTOOLS_DEV` to increase verbosity across multiple utilities.

When `POWERTOOLS_DEV` is set to a truthy value (`1`, `true`), it'll have the following effects:

| Utility           | Effect                                                                                                                                                                                                                                                                 |
| ----------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| __Logger__        | Increase JSON indentation to 4. This will ease local debugging when running functions locally under emulators or direct calls while not affecting unit tests. <br><br> However, Amazon CloudWatch Logs view will degrade as each new line is treated as a new message. |
| __Event Handler__ | Enable full traceback errors in the response, indent request/responses, and CORS in dev mode (`*`).                                                                                                                                                                    |
| __Tracer__        | Future-proof safety to disables tracing operations in non-Lambda environments. This already happens automatically in the Tracer utility.                                                                                                                               |

## Debug mode

As a best practice for libraries, Powertools module logging statements are suppressed.

When necessary, you can use `POWERTOOLS_DEBUG` environment variable to enable debugging. This will provide additional information on every internal operation.

## Support Powertools for AWS Lambda (Python)

There are many ways you can help us gain future investments to improve everyone's experience:

<div class="grid cards" markdown>

- :heart:{ .lg .middle } __Become a public reference__

    ---

    Add your company name and logo on our [landing page](https://powertools.aws.dev).

    [:octicons-arrow-right-24: GitHub Issue template](https://github.com/aws-powertools/powertools-lambda-python/issues/new?assignees=&labels=customer-reference&template=support_powertools.yml&title=%5BSupport+Lambda+Powertools%5D%3A+%3Cyour+organization+name%3E){target="_blank"}

- :mega:{ .lg .middle } __Share your work__

    ---

    Blog posts, video, and sample projects about Powertools for AWS Lambda.

    [:octicons-arrow-right-24: GitHub Issue template](https://github.com/aws-powertools/powertools-lambda-python/issues/new?assignees=&labels=community-content&template=share_your_work.yml&title=%5BI+Made+This%5D%3A+%3CTITLE%3E){target="_blank"}

- :partying_face:{ .lg .middle } __Join the community__

    ---

    Connect, ask questions, and share what features you use.

    [:octicons-arrow-right-24: Discord invite](https://discord.gg/B8zZKbbyET){target="blank"}

</div>

### Becoming a reference customer

Knowing which companies are using this library is important to help prioritize the project internally. The following companies, among others, use Powertools:

<div class="grid" style="text-align:center;" markdown>

[**Alma Media**](https://www.almamedia.fi/en/){target="_blank" rel="nofollow"}
{ .card }

[**Banxware**](https://www.banxware.com){target="_blank" rel="nofollow"}
{ .card }

[**Brsk**](https://www.brsk.co.uk/){target="_blank" rel="nofollow"}
{ .card }

[**BusPatrol**](https://buspatrol.com/){target="_blank" rel="nofollow"}
{ .card }

[**Capital One**](https://www.capitalone.com/){target="_blank" rel="nofollow"}
{ .card }

[**Caylent**](https://caylent.com/){target="_blank" rel="nofollow"}
{ .card }

[**CHS Inc.**](https://www.chsinc.com/){target="_blank" rel="nofollow"}
{ .card }

[**CPQi (Exadel Financial Services)**](https://cpqi.com/){target="_blank" rel="nofollow"}
{ .card }

[**CloudZero**](https://www.cloudzero.com/){target="_blank" rel="nofollow"}
{ .card }

[**CyberArk**](https://www.cyberark.com/){target="_blank" rel="nofollow"}
{ .card }

[**Flyweight**](https://flyweight.io/){target="_blank" rel="nofollow"}
{ .card }

[**globaldatanet**](https://globaldatanet.com/){target="_blank" rel="nofollow"}
{ .card }

[**IMS**](https://ims.tech/){target="_blank" rel="nofollow"}
{ .card }

[**Jit Security**](https://www.jit.io/){target="_blank" rel="nofollow"}
{ .card }

[**LocalStack**](https://www.localstack.cloud/){target="_blank" rel="nofollow"}
{ .card }

[**Propellor.ai**](https://www.propellor.ai/){target="_blank" rel="nofollow"}
{ .card }

[**Pushpay**](https://pushpay.com/){target="_blank" rel="nofollow"}
{ .card }

[**Recast**](https://getrecast.com/){target="_blank" rel="nofollow"}
{ .card }

[**TopSport**](https://www.topsport.com.au/){target="_blank" rel="nofollow"}
{ .card }

[**Transformity**](https://transformity.tech/){target="_blank" rel="nofollow"}
{ .card }

[**Trek10**](https://www.trek10.com/){target="_blank" rel="nofollow"}
{ .card }

[**Vertex Pharmaceuticals**](https://www.vrtx.com/){target="_blank" rel="nofollow"}
{ .card }

</div>

### Using Lambda Layers

!!! note "Layers help us understand who uses Powertools for AWS Lambda (Python) in a non-intrusive way."

<!-- markdownlint-disable MD051 -->

When [using Layers](#lambda-layer), you can add Powertools for AWS Lambda (Python) as a dev dependency to not impact the development process. For Layers, we pre-package all dependencies, compile and optimize for storage and both x86_64 and ARM architecture.

<!-- markdownlint-enable MD051 -->

## Tenets

These are our core principles to guide our decision making.

- __AWS Lambda only__. We optimise for AWS Lambda function environments and supported runtimes only. Utilities might work with web frameworks and non-Lambda environments, though they are not officially supported.
- __Eases the adoption of best practices__. The main priority of the utilities is to facilitate best practices adoption, as defined in the AWS Well-Architected Serverless Lens; all other functionality is optional.
- __Keep it lean__. Additional dependencies are carefully considered for security and ease of maintenance, and prevent negatively impacting startup time.
- __We strive for backwards compatibility__. New features and changes should keep backwards compatibility. If a breaking change cannot be avoided, the deprecation and migration process should be clearly defined.
- __We work backwards from the community__. We aim to strike a balance of what would work best for 80% of customers. Emerging practices are considered and discussed via Requests for Comment (RFCs)
- __Progressive__. Utilities are designed to be incrementally adoptable for customers at any stage of their Serverless journey. They follow language idioms and their community’s common practices.
