Gutachten CDK (TypeScript)

This CDK app creates:
- S3 Bucket
- DynamoDB Table
- Lambda function (expects built artifact in ../gutachten-lambda/target)
- HTTP API Gateway (routes all traffic to the Lambda)

Quickstart
1. Install dependencies: npm ci
2. Build TypeScript: npm run build
3. Synthesize: npm run synth
4. Deploy: npm run deploy

Notes
- The Lambda code is set to `Code.fromAsset('../gutachten-lambda/target')`. Build the Quarkus jar/zip and place it in that folder or adjust the path.
- CDK requires AWS credentials configured in your shell or environment.
