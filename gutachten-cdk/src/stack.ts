import * as cdk from 'aws-cdk-lib';
import { Construct } from 'constructs';
import * as lambda from 'aws-cdk-lib/aws-lambda';
import * as apigateway from 'aws-cdk-lib/aws-apigatewayv2';
import * as integrations from 'aws-cdk-lib/aws-apigatewayv2-integrations';
import * as dynamodb from 'aws-cdk-lib/aws-dynamodb';
import * as s3 from 'aws-cdk-lib/aws-s3';

export class GutachtenStack extends cdk.Stack {
  constructor(scope: Construct, id: string, props?: cdk.StackProps) {
    super(scope, id, props);

    // S3 bucket
    const bucket = new s3.Bucket(this, 'GutachtenBucket', {
      removalPolicy: cdk.RemovalPolicy.DESTROY,
      autoDeleteObjects: true,
    });

    // DynamoDB table
    const table = new dynamodb.Table(this, 'GutachtenTable', {
      partitionKey: { name: 'id', type: dynamodb.AttributeType.STRING },
      removalPolicy: cdk.RemovalPolicy.DESTROY,
    });

    // Lambda (expecting a jar or zip to be provided)
    const fn = new lambda.Function(this, 'GutachtenLambda', {
      runtime: lambda.Runtime.JAVA_11,
      handler: 'com.example.LambdaHandler::handleRequest',
      code: lambda.Code.fromAsset('../gutachten-lambda/target'),
      memorySize: 1024,
      timeout: cdk.Duration.seconds(30)
    });

    // Grant permissions
    bucket.grantReadWrite(fn);
    table.grantReadWriteData(fn);

    // HTTP API Gateway
    const api = new apigateway.HttpApi(this, 'GutachtenHttpApi');
    new apigateway.HttpRoute(this, 'DefaultRoute', {
      httpApi: api,
      integration: new integrations.LambdaProxyIntegration({ handler: fn }),
      routeKey: apigateway.HttpRouteKey.with('/{proxy+}')
    });

    new cdk.CfnOutput(this, 'HttpApiUrl', { value: api.apiEndpoint });
  }
}
