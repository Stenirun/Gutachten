package com.bauerfinanz.gutachten.common.logging;

import static com.bauerfinanz.gutachten.common.logging.LogDataArgument.data;

import java.util.UUID;

import org.slf4j.MDC;

import lombok.experimental.UtilityClass;
import lombok.extern.slf4j.Slf4j;

/**
 * The Log Service contains base logging functions for meta data and json logging.
 *
 * @author Markus Pichler
 * @version 0.0.1
 * @since 0.0.1
 */
@UtilityClass
@Slf4j
public class LogServiceEvent extends BaseLogService {

  public static void initLogging(final String requestIdValue, final String externalIdValue, final String userId) {
    setRequestId(requestIdValue);
    setExternalId(externalIdValue);
    setLoginUser(userId == null
      ? SYSTEM_USER
      : userId);

    try {
      // generate new Request Id
      if (getRequestId() == null) {
        setRequestId(UUID.randomUUID().toString());
      }

      // add meta data for each logging request
      MDC.put("userId", getLoginUser());
      MDC.put("correlationId", getRequestId());
      if (getExternalId() != null) {
        MDC.put("externalId", getExternalId());
      }

      log.debug("Initialize Request Id", data("securityUserId", userId));
    } catch (final Exception exc) {
      log.error("Can't construct initial logging context data - continue with normal event logging", exc);
    }
  }

}
