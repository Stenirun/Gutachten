
package com.bauerfinanz.gutachten.exception;

import java.util.List;

import com.bauerfinanz.gutachten.common.exception.Error.Violation;
import com.bauerfinanz.gutachten.common.exception.ErrorType;

import jakarta.validation.ValidationException;
import lombok.Getter;

/**
 * Input data failed the condition exception.
 *
 * @author Markus Pichler
 * @version 0.0.1
 * @since 0.0.1
 */
public class InputValidationException extends ValidationException {

  private static final long serialVersionUID = -54066418254519218L;

  @Getter
  private final ErrorType errorType;
  @Getter
  private final List<Violation> errorList;

  public InputValidationException(final ErrorType errorType, final List<Violation> errorList) {
    super(errorType.getDescription());
    this.errorType = errorType;
    this.errorList = errorList;
  }

  public InputValidationException(final ErrorType errorType, final List<Violation> errorList, final Throwable cause) {
    super(errorType.getDescription(), cause);
    this.errorType = errorType;
    this.errorList = errorList;
  }

}
