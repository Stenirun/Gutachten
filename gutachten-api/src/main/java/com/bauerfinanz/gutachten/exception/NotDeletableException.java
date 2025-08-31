package com.bauerfinanz.gutachten.exception;

import com.bauerfinanz.gutachten.common.exception.ErrorType;

import lombok.Getter;

/**
 * Entity not deletable exception.
 *
 * @author Markus Pichler
 * @version 0.0.1
 * @since 0.0.1
 */
public class NotDeletableException extends RuntimeException {

  private static final long serialVersionUID = 8082300131583167318L;
  @Getter
  private final ErrorType errorType;

  public NotDeletableException(final ErrorType errorType) {
    super(errorType.getDescription());
    this.errorType = errorType;
  }

  public NotDeletableException(final ErrorType errorType, final Throwable cause) {
    super(errorType.getDescription(), cause);
    this.errorType = errorType;
  }

}
