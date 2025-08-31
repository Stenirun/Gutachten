package com.bauerfinanz.gutachten.common.logging;

import java.io.IOException;
import java.util.Map;

import org.eclipse.microprofile.config.ConfigProvider;

import io.quarkiverse.loggingjson.JsonGenerator;
import io.quarkiverse.loggingjson.providers.StructuredArgument;
import lombok.extern.slf4j.Slf4j;

/**
 * Logs more then one structured objects under one data field.
 *
 * @author Markus Pichler
 * @version 0.0.1
 * @since 0.0.1
 */
@Slf4j
public final class LogDataArgumentMap implements StructuredArgument {

  private static final String FIELDNAME = ConfigProvider.getConfig().getOptionalValue("quarkus.log.data.name", String.class).orElse("data");
  private final Map<String, Object> dataMap;

  private LogDataArgumentMap(final Map<String, Object> dataMap) {
    this.dataMap = dataMap;
  }

  public static StructuredArgument dataMap(final Map<String, Object> dataMap) {
    return new LogDataArgumentMap(dataMap);
  }

  @Override
  public void writeTo(final JsonGenerator generator) throws IOException {
    generator.writeObjectFieldStart(FIELDNAME);
    dataMap.forEach((k, v) -> {
      try {
        generator.writeObjectField(k, v);
      } catch (final IOException exc) {
        log.warn("Can't log data object [{}] - [{}]", k, v, exc);
      }
    });
    generator.writeEndObject();
  }

}
