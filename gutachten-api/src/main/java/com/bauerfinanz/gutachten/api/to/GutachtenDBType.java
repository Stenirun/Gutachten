package com.bauerfinanz.gutachten.api.to;

import lombok.Getter;
import lombok.RequiredArgsConstructor;

/**
 * Gutachten DB Sub Types. Only for internal use.
 *
 * @author Markus Pichler
 * @version 0.0.1
 * @since 0.0.1
 */
@RequiredArgsConstructor
public enum GutachtenDBType {

  ALARMS("A"),
  ALARMEVENT("AE"),
  RULES("R"),
  RULEEVENT("RE"),
  LVS_PROFILES("P"),
  HISTORY_COMMENT(null);

  @Getter
  private final String idPrefix;

}
