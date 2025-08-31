package com.bauerfinanz.gutachten.api.to;

import lombok.experimental.UtilityClass;

/**
 * Error Messages.
 *
 * @author Markus Pichler
 * @version 0.0.1
 * @since 0.0.1
 */
@UtilityClass
public class ErrorMessage {

  public static final String ID_MALFORMED_MESSAGE = "id.malformed";
  public static final String NAME_MALFORMED_MESSAGE = "name.malformed";
  public static final String NAME_EMPTY_MESSAGE = "name.blank";
  public static final String DESCRIPTION_MALFORMED_MESSAGE = "description.malformed";
  public static final String DESCRIPTION_EMPTY_MESSAGE = "description.empty";
  public static final String SCOPE_EMPTY_MESSAGE = "scope.blank";

  // metadata specific
  public static final String VERSION_EMPTY_MESSAGE = "version.empty";

  // regular expression patterns
  public static final String ALLOW_DIGITS_LETTERS_WHITESPACE_PATTERN = "[\\p{L}\\p{M}\\p{N} -]*";
  public static final String ALLOW_DIGITS_AND_LETTERS_PATTERN = "[\\p{L}\\p{M}\\p{N}]*";
  public static final String ALLOW_LETTERS_AND_WHITESPACE_PATTERN = "[\\p{L}\\p{M} -]*";

}
