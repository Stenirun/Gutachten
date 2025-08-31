package com.bauerfinanz.gutachten.authorizer.lambda;

import static com.bauerfinanz.gutachten.common.logging.LogDataArgument.data;
import static com.bauerfinanz.gutachten.common.logging.LogDataArgumentMap.dataMap;

import java.util.List;
import java.util.Map;

import org.eclipse.microprofile.config.inject.ConfigProperty;
import org.eclipse.microprofile.jwt.JsonWebToken;
import org.jose4j.jwt.consumer.InvalidJwtException;

import com.amazonaws.services.lambda.runtime.Context;
import com.amazonaws.services.lambda.runtime.RequestHandler;
import com.amazonaws.services.lambda.runtime.events.APIGatewayCustomAuthorizerEvent;
import com.bauerfinanz.gutachten.common.logging.LogServiceEvent;
import com.bauerfinanz.gutachten.authorizer.to.AuthorizerPolicy;
import com.bauerfinanz.gutachten.authorizer.to.PolicyDocument;
import com.bauerfinanz.gutachten.authorizer.to.Statement;
import com.bauerfinanz.gutachten.authorizer.to.Statement.Effect;
import com.bauerfinanz.gutachten.common.exception.Error;
import com.bauerfinanz.gutachten.common.exception.ErrorType;

import io.smallrye.jwt.auth.principal.JWTParser;
import io.smallrye.jwt.auth.principal.ParseException;
import jakarta.inject.Named;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import software.amazon.awssdk.utils.StringUtils;

/**
 * Cognito pre token auth event to add custom scopes and save inactive first login user attempts.
 *
 * @author Markus Pichler
 * @version 0.0.1
 * @since 0.0.1
 */
@Slf4j
@Named("authorizerEvent")
@RequiredArgsConstructor
public class CognitoAuthorizerEvent implements RequestHandler<APIGatewayCustomAuthorizerEvent, AuthorizerPolicy> {

  @ConfigProperty(name = "quarkus.log.error.name", defaultValue = "error")
  String errorLabel;

  private final JWTParser jwtParser;
  private static final String EXECUTE_API_ARN_FORMAT = "arn:aws:execute-api:%s:%s:%s/%s/*";

  @Override
  public AuthorizerPolicy handleRequest(final APIGatewayCustomAuthorizerEvent input, final Context context) {
    LogServiceEvent.initLogging(context != null
      ? context.getAwsRequestId()
      : null, null, null);
    log.info("Start Authorizer", data("event", input));
    final String authToken = input != null && input.getQueryStringParameters() != null
      ? input.getQueryStringParameters().get("token")
      : null;
    if (StringUtils.isBlank(authToken)) {
      final Error error = Error.builder()
        .errorCode(ErrorType.EVENT_ERROR.getCode())
        .errorMessage("No authorizer token available")
        .build();
      log.error("End Authorizer", data(errorLabel, error));
      throw new RuntimeException("No authorizer token available");
    }
    // extract policy meta Data
    final String methodArn = input.getMethodArn();
    final String[] arnPartials = methodArn.split(":");
    final String region = arnPartials[3];
    final String awsAccountId = arnPartials[4];
    final String[] apiGatewayArnPartials = arnPartials[5].split("/");
    final String restApiId = apiGatewayArnPartials[0];
    final String stage = apiGatewayArnPartials[1];

    log.debug("Authorizer Token", dataMap(Map.of(
      "token", authToken,
      "region", region,
      "awsAccountId", awsAccountId,
      "restApiId", restApiId,
      "stage", stage)));
    AuthorizerPolicy policy = null;
    try {
      // verify jwt
      final JsonWebToken jwt = jwtParser.parse(authToken);
      policy = AuthorizerPolicy.builder()
        .principalId(jwt.getName())
        .policyDocument(PolicyDocument.builder().statements(List.of(Statement.builder()
          .effect(Effect.Allow)
          .resource(String.format(EXECUTE_API_ARN_FORMAT, region, awsAccountId, restApiId, stage))
          .build())).build())
        .build();
    } catch (final ParseException exc) {
      Error error = Error.builder()
        .errorCode(ErrorType.EVENT_ERROR.getCode())
        .errorMessage(exc.getMessage())
        .build();
      log.error("Can't verify authorization token - deny access", data(errorLabel, error), exc.getCause() != null
        ? exc.getCause()
        : exc);
      String userName = "n/a";
      if (exc.getCause() instanceof InvalidJwtException) {
        final InvalidJwtException iExc = (InvalidJwtException) exc.getCause();
        if (iExc.hasExpired()) {
          error = Error.builder()
            .errorCode(ErrorType.EVENT_ERROR.getCode())
            .errorMessage("Authorization token is expired")
            .build();
          log.error("End Authorizer", data(errorLabel, error));
          throw new RuntimeException("Authorization token is expired");
        }
        if (iExc.getJwtContext() != null
          && iExc.getJwtContext().getJwtClaims() != null
          && iExc.getJwtContext().getJwtClaims().getClaimValueAsString("preferred_username") != null) {
          userName = iExc.getJwtContext().getJwtClaims().getClaimValueAsString("preferred_username");
        }
      }
      policy = AuthorizerPolicy.builder()
        .principalId(userName)
        .policyDocument(PolicyDocument.builder().statements(List.of(Statement.builder()
          .effect(Effect.Deny)
          .resource(String.format(EXECUTE_API_ARN_FORMAT, region, awsAccountId, restApiId, stage))
          .build())).build())
        .build();
    } catch (final Exception exc) {
      final Error error = Error.builder()
        .errorCode(ErrorType.EVENT_ERROR.getCode())
        .errorMessage(exc.getMessage())
        .build();
      log.error("Can't read authorization token - deny access", data(errorLabel, error), exc);
      policy = AuthorizerPolicy.builder()
        .principalId("n/a")
        .policyDocument(PolicyDocument.builder().statements(List.of(Statement.builder()
          .effect(Effect.Deny)
          .resource(String.format(EXECUTE_API_ARN_FORMAT, region, awsAccountId, restApiId, stage))
          .build())).build())
        .build();
    }
    log.info("End Authorizer", data("event", policy));
    return policy;
  }

}