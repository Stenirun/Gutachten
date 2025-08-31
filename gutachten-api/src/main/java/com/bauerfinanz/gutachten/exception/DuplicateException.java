package com.bauerfinanz.gutachten.exception;

import com.bauerfinanz.gutachten.common.exception.ErrorType;

import lombok.Getter;

/**
 * The Class DuplicateException.
 *
 * @author Markus Pichler
 * @version 0.0.1
 * @since 0.0.1
 */
public class DuplicateException extends RuntimeException {

  private static final long serialVersionUID = 5164458242293105034L;
  @Getter
  private final ErrorType errorType;

  public DuplicateException(final ErrorType errorType) {
    super(errorType.getDescription());
    this.errorType = errorType;
  }

  public DuplicateException(final ErrorType errorType, final Throwable cause) {
    super(errorType.getDescription(), cause);
    this.errorType = errorType;
  }

}
