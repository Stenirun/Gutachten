package com.bauerfinanz.gutachten.common.exception;

/**
 * general event runtime exception for retry.
 *
 * @author Markus Pichler
 * @version 0.0.1
 * @since 0.0.1
 */
public class EventException extends RuntimeException {

  private static final long serialVersionUID = 7407053620929394784L;

  public EventException(final String message) {
    super(message);
  }

  public EventException(final String message, final Throwable cause) {
    super(message, cause);
  }

}
