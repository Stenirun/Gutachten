package com.bauerfinanz.gutachten.junit;

import static com.bauerfinanz.gutachten.common.logging.LogDataArgument.data;
import static com.bauerfinanz.gutachten.common.logging.LogDataArgumentMap.dataMap;
import static org.junit.jupiter.api.Assertions.assertEquals;
import static org.junit.jupiter.api.Assertions.assertNotNull;
import static org.junit.jupiter.api.Assertions.assertNull;
import static org.junit.jupiter.api.Assertions.assertTrue;

import java.util.Map;

import org.junit.jupiter.api.Test;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.bauerfinanz.gutachten.common.exception.EventException;
import com.bauerfinanz.gutachten.common.logging.BaseLogService;
import com.bauerfinanz.gutachten.common.logging.LogServiceEvent;

import io.quarkus.test.junit.QuarkusTest;
import jakarta.inject.Inject;
import lombok.extern.slf4j.Slf4j;

@QuarkusTest
@Slf4j
class ConfigUtilTest {

  @Inject
  ObjectMapper mapper;

  @Test
  void testLogging() {
    LogServiceEvent.initLogging("requestIdValue", "externalIdValue", "JUnit-User");
    log.info("loggingTest");

    assertEquals("requestIdValue", BaseLogService.getRequestId());
    assertEquals("externalIdValue", BaseLogService.getExternalId());
    assertEquals("JUnit-User", BaseLogService.getLoginUser());
  }

  @Test
  void testLoggingData() {
    LogServiceEvent.initLogging("requestIdValue", "externalIdValue", "JUnit-User");
    log.info("loggingTestData", data("entry1", "Test"));
    assertTrue(true);
  }

  @Test
  void testLoggingDataMap() {
    LogServiceEvent.initLogging("requestIdValue", "externalIdValue", "JUnit-User");
    log.info("loggingTestDataMap", dataMap(Map.of("entry1", "Test1", "entry2", "Test2")));
    assertTrue(true);
  }

  @Test
  void testLoggingDefault() {
    LogServiceEvent.initLogging(null, null, null);
    log.error("loggingDefaultTest");

    assertNotNull(BaseLogService.getRequestId());
    assertNull(BaseLogService.getExternalId());
    assertEquals(BaseLogService.SYSTEM_USER, BaseLogService.getLoginUser());
  }

  @Test
  void testCloseLogging() {

    LogServiceEvent.initLogging("requestIdValue", "externalIdValue", "JUnit-User");
    BaseLogService.closeLogging();

    assertNull(BaseLogService.getRequestId());
    assertNull(BaseLogService.getExternalId());
    assertNull(BaseLogService.getLoginUser());
  }

  @Test
  void testEventException() {
    final EventException exc = new EventException("JUnit Exc");
    assertEquals("JUnit Exc", exc.getMessage());
  }

}
