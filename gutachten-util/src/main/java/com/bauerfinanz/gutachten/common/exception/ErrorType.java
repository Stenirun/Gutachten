package com.bauerfinanz.gutachten.common.exception;

import lombok.Getter;

/**
 * Global error type mapping for message identification in Frontend.
 *
 * @author Markus Pichler
 * @version 0.0.1
 * @since 0.0.1
 */
public enum ErrorType {

  // general errors
  EVENT_ERROR(100, "Unknown event error occured."),
  INTERNAL(101, "Unknown internal error occured."),
  DATABASE(102, "A database error has occurred."),
  RESOURCE_NOT_FOUND(103, "Resource not found."),
  SDK_CLIENT_EXCEPTION(104, "Error with SDK client."),
  CONDITION_CHECK_FAILED_EXCEPTION(105, "Condition check failed - input data failed the condition."),
  DEFAULT_ERROR(106, "Please check your input."),
  CONSTRAINT_VIOLATION(107, "There was a constraint violation."),
  JSON_INPUT_VIOLATION(108, "JSON input format is wrong."),
  INPUT_VIOLATION(109, "Input value validation."),

  // ConfigService specific errors

  ENUM_NOT_FOUND(400, "Enum config values not found."),
  LANGUAGE_NOT_FOUND(401, "Language config values not found."),
  VERSION_NOT_FOUND(402, "Version config values not found."),
  ORDER_NOT_FOUND(403, "Car order configuration value not found."),

  // User Settings
  INVALID_USER_ID(210, "User id is invalid.");

  @Getter
  private final int code;

  @Getter
  private final String description;

  ErrorType(final int code, final String description) {
    this.code = code;
    this.description = description;
  }

}