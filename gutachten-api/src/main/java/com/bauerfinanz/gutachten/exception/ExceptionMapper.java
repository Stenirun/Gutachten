package com.bauerfinanz.gutachten.exception;

import static com.bauerfinanz.gutachten.common.logging.LogDataArgument.data;

import java.util.ArrayList;
import java.util.List;
import java.util.concurrent.CompletionException;
import java.util.stream.Collectors;

import org.eclipse.microprofile.config.inject.ConfigProperty;
import org.jboss.resteasy.reactive.server.ServerExceptionMapper;

import com.fasterxml.jackson.core.JsonParseException;
import com.bauerfinanz.gutachten.common.exception.Error;
import com.bauerfinanz.gutachten.common.exception.Error.Violation;
import com.bauerfinanz.gutachten.common.exception.ErrorType;
import com.bauerfinanz.gutachten.common.exception.NotFoundException;
import com.bauerfinanz.gutachten.api.to.DBApiConstants;

import jakarta.validation.ConstraintViolationException;
import jakarta.validation.ValidationException;
import jakarta.ws.rs.core.Response;
import lombok.extern.slf4j.Slf4j;
import software.amazon.awssdk.core.exception.SdkClientException;
import software.amazon.awssdk.services.dynamodb.model.ConditionalCheckFailedException;
import software.amazon.awssdk.services.dynamodb.model.DynamoDbException;

/**
 * Global Exception Mapper Class.
 *
 * @author Markus Pichler
 *
 * @version 0.0.1
 * @since 0.0.1
 */
@Slf4j
public class ExceptionMapper {

  @ConfigProperty(name = "quarkus.log.error.name", defaultValue = "error")
  String errorLabel;

  @ServerExceptionMapper
  public Response constraintViolationException(final ConstraintViolationException exc) {
    final List<Violation> errorList = exc.getConstraintViolations().stream().map(violation -> {
      // extract field name
      String field = null;
      if (violation.getPropertyPath() != null) {
        field = violation.getPropertyPath().toString();
        final int iPos = field.indexOf('.', field.indexOf('.') + 1) + 1;
        if (iPos > 0) {
          field = field.substring(iPos);
        }
      }
      // extract extended value
      Object extend = violation.getConstraintDescriptor().getAttributes().get("regexp");
      if (extend == null) {
        extend = violation.getConstraintDescriptor().getAttributes().get("value");
      }
      // set values
      final List<Object> values = new ArrayList<>();
      if (violation.getInvalidValue() != null) {
        values.add(violation.getInvalidValue().toString());
      }
      if (extend != null) {
        values.add(extend.toString());
      }

      return Violation.builder()
        .field(field)
        .messageTemplate(violation.getMessageTemplate()
          .replaceAll("[{,}]", "")
          .replace(DBApiConstants.CONSTRAINT_ERROR_PREFIX, DBApiConstants.NEW_CONSTRAINT_ERROR_PREFIX))
        .values(values)
        .build();
    }).collect(Collectors.toList());

    final Error err = Error.builder()
      .errorCode(ErrorType.CONSTRAINT_VIOLATION.getCode())
      .errorMessage(exc.getConstraintViolations().size() + " constraint violation(s) occurred.")
      .httpStatusCode(Response.Status.BAD_REQUEST.getStatusCode())
      .errorList(errorList)
      .build();

    log.error("ConstraintViolationException", data(errorLabel, err), exc);
    return Response.status(Response.Status.BAD_REQUEST).entity(err).build();
  }

  @ServerExceptionMapper
  public Response inputValidationException(final InputValidationException exc) {
    final Error err = Error.builder()
      .errorCode(exc.getErrorType().getCode())
      .errorMessage(exc.getErrorType().getDescription())
      .errorList(exc.getErrorList())
      .httpStatusCode(Response.Status.BAD_REQUEST.getStatusCode())
      .build();

    log.error("InputValidationException", data(errorLabel, err), exc);
    return Response.status(Response.Status.BAD_REQUEST).entity(err).build();
  }

  @ServerExceptionMapper
  public Response jsonParseException(final JsonParseException exc) {
    final Error error = Error.builder()
      .errorCode(ErrorType.JSON_INPUT_VIOLATION.getCode())
      .errorMessage(ErrorType.JSON_INPUT_VIOLATION.getDescription())
      .errorList(List.of(Violation.builder()
        .field("Body")
        .messageTemplate(exc.getOriginalMessage())
        .values(List.of(exc.getRequestPayloadAsString()))
        .build()))
      .httpStatusCode(Response.Status.BAD_REQUEST.getStatusCode())
      .build();

    log.error("JsonParseException", data(errorLabel, error), exc);
    return Response.status(Response.Status.BAD_REQUEST).entity(error).build();
  }

  @ServerExceptionMapper
  public Response notFoundException(final NotFoundException exc) {
    final Error error = Error.builder()
      .errorCode(exc.getErrorType().getCode())
      .errorMessage(exc.getErrorType().getDescription())
      .httpStatusCode(Response.Status.NOT_FOUND.getStatusCode())
      .build();

    log.error("NotFoundException", data(errorLabel, error), exc);
    return Response.status(Response.Status.NOT_FOUND).entity(error).build();
  }

  @ServerExceptionMapper
  public Response dynamodbException(final DynamoDbException exc) {
    final Error error = Error.builder()
      .errorCode(ErrorType.DATABASE.getCode())
      .errorMessage(ErrorType.DATABASE.getDescription())
      .httpStatusCode(Response.Status.INTERNAL_SERVER_ERROR.getStatusCode())
      .build();

    log.error("DynamoDBException", data(errorLabel, error), exc);
    return Response.status(Response.Status.INTERNAL_SERVER_ERROR).entity(error).build();
  }

  @ServerExceptionMapper
  public Response conditionCheckFailedException(final ConditionalCheckFailedException exc) {
    final Error error = Error.builder()
      .errorCode(ErrorType.CONDITION_CHECK_FAILED_EXCEPTION.getCode())
      .errorMessage(ErrorType.CONDITION_CHECK_FAILED_EXCEPTION.getDescription())
      .httpStatusCode(Response.Status.BAD_REQUEST.getStatusCode())
      .build();

    log.error("ConditionCheckFailedException", data(errorLabel, error), exc);
    return Response.status(Response.Status.BAD_REQUEST).entity(error).build();
  }

  @ServerExceptionMapper
  public Response sdkClientException(final SdkClientException exc) {
    final Error error = Error.builder()
      .errorCode(ErrorType.SDK_CLIENT_EXCEPTION.getCode())
      .errorMessage(ErrorType.SDK_CLIENT_EXCEPTION.getDescription())
      .httpStatusCode(Response.Status.INTERNAL_SERVER_ERROR.getStatusCode())
      .build();

    log.error("AwsSdkClientException", data(errorLabel, error), exc);
    return Response.status(Response.Status.INTERNAL_SERVER_ERROR).entity(error).build();
  }

  @ServerExceptionMapper
  public Response duplicateException(final DuplicateException exc) {
    final Error err = Error.builder()
      .errorCode(exc.getErrorType().getCode())
      .errorMessage(exc.getErrorType().getDescription())
      .httpStatusCode(Response.Status.BAD_REQUEST.getStatusCode())
      .build();

    log.error("DuplicateNameException", data(errorLabel, err), exc);
    return Response.status(Response.Status.BAD_REQUEST).entity(err).build();
  }

  @ServerExceptionMapper
  @Deprecated
  public Response validationException(final ValidationException exc) {
    final Error err = Error.builder()
      .errorCode(ErrorType.CONSTRAINT_VIOLATION.getCode())
      .errorMessage(exc.getMessage())
      .httpStatusCode(Response.Status.BAD_REQUEST.getStatusCode())
      .build();

    log.error("ValidationException", data(errorLabel, err), exc);
    return Response.status(Response.Status.BAD_REQUEST).entity(err).build();
  }

  @ServerExceptionMapper
  public Response notDeletableExceptionException(final NotDeletableException exc) {
    final Error err = Error.builder()
      .errorCode(exc.getErrorType().getCode())
      .errorMessage(exc.getMessage())
      .httpStatusCode(Response.Status.BAD_REQUEST.getStatusCode())
      .build();

    log.error("NotDeletableException", data(errorLabel, err), exc);
    return Response.status(Response.Status.BAD_REQUEST).entity(err).build();
  }

  @ServerExceptionMapper
  public Response completionException(final CompletionException exc) {
    if (exc.getCause() instanceof ConditionalCheckFailedException) {
      return conditionCheckFailedException((ConditionalCheckFailedException) exc.getCause());
    }
    if (exc.getCause() instanceof SdkClientException) {
      return sdkClientException((SdkClientException) exc.getCause());
    }
    if (exc.getCause() instanceof DynamoDbException) {
      return dynamodbException((DynamoDbException) exc.getCause());
    }
    if (exc.getCause() instanceof DuplicateException) {
      return duplicateException((DuplicateException) exc.getCause());
    }
    if (exc.getCause() instanceof InputValidationException) {
      return inputValidationException((InputValidationException) exc.getCause());
    }

    final Error err = Error.builder()
      .errorCode(ErrorType.INTERNAL.getCode())
      .errorMessage(ErrorType.INTERNAL.getDescription())
      .httpStatusCode(Response.Status.INTERNAL_SERVER_ERROR.getStatusCode())
      .build();

    log.error("Completion Exception", data(errorLabel, err), exc);
    return Response.status(Response.Status.INTERNAL_SERVER_ERROR.getStatusCode()).entity(err).build();
  }

}