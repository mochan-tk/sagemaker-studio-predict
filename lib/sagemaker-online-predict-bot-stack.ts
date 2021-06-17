import * as cdk from '@aws-cdk/core';
import * as lambda from '@aws-cdk/aws-lambda';
import * as apigateway from '@aws-cdk/aws-apigateway';
import * as ssm from '@aws-cdk/aws-ssm';
import { Role, ServicePrincipal, ManagedPolicy } from '@aws-cdk/aws-iam';
import { Table, AttributeType } from "@aws-cdk/aws-dynamodb";


export class SageMakerOnlinePredictBotStack extends cdk.Stack {
  constructor(scope: cdk.Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);
    
    const dynamodb = new Table(this, "sagemaker-online-predict-bot", {
      partitionKey: {
        name: "UserId",
        type: AttributeType.STRING,
      },
      tableName: "sagemaker-online-predict-bot",
      removalPolicy: cdk.RemovalPolicy.DESTROY, // NOT recommended for production code
    });
    
    // IAM Role for Lambda with SSM policy.
    const lambdaRole = new Role(this, 'SageMakerOnlinePredictBotLambdaRole', {
      roleName: 'SageMakerOnlinePredictBotLambdaRole',
      assumedBy: new ServicePrincipal('lambda.amazonaws.com'),
      managedPolicies: [
        //ManagedPolicy.fromAwsManagedPolicyName('service-role/AWSLambdaBasicExecutionRole'),
        ManagedPolicy.fromAwsManagedPolicyName('AdministratorAccess'),
      ]
    });    

    const bot = new lambda.DockerImageFunction(this, 'bot', {
      code: lambda.DockerImageCode.fromImageAsset('./lambda/bot'),
      role: lambdaRole,
    });

    const api = new apigateway.RestApi(this, 'api');
    api.root.addMethod('POST', new apigateway.LambdaIntegration(bot));
  }
}
