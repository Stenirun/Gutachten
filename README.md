Gutachten Backend multi-module project

Modules:
- gutachten-cdk: placeholder for AWS CDK Java code (consider using TypeScript CDK for full features)
- gutachten-config: shared configuration and utilities
- gutachten-lambda: Quarkus-based lambda with HTTP endpoints, DynamoDB and S3 wrappers

Build:
- mvn -f pom.xml clean install

Notes:
- AWS credentials and region should be provided via environment variables or IAM role for Lambda.
