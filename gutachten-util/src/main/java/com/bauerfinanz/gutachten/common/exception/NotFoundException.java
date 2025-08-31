package com.bauerfinanz.gutachten.common.exception;

import lombok.Getter;

/**
 * Entity not found exception.
 *
 * @author Markus Pichler
 * @version 0.0.1
 * @since 0.0.1
 */
public class NotFoundException extends RuntimeException {

  private static final long serialVersionUID = 8935176446551985634L;
  @Getter
  private final ErrorType errorType;

  public NotFoundException(final ErrorType errorType) {
    super(errorType.getDescription());
    this.errorType = errorType;
  }

  public NotFoundException(final ErrorType errorType, final Throwable cause) {
    super(errorType.getDescription(), cause);
    this.errorType = errorType;
  }

}
