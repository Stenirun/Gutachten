package com.bauerfinanz.gutachten.common.logging;

import java.io.IOException;

import org.eclipse.microprofile.config.ConfigProvider;

import io.quarkiverse.loggingjson.JsonGenerator;
import io.quarkiverse.loggingjson.providers.StructuredArgument;

/**
 * Log one structured object under data field.
 *
 * @author Markus Pichler
 * @version 0.0.1
 * @since 0.0.1
 */
public final class LogDataArgument implements StructuredArgument {

  private static final String FIELDNAME = ConfigProvider.getConfig().getOptionalValue("quarkus.log.data.name", String.class).orElse("data");
  private final String key;
  private final Object value;

  public LogDataArgument(final String key, final Object value) {
    this.key = key;
    this.value = value;
  }

  public static LogDataArgument data(final String key, final Object value) {
    return new LogDataArgument(key, value);
  }

  @Override
  public void writeTo(final JsonGenerator generator) throws IOException {
    generator.writeObjectFieldStart(FIELDNAME);
    generator.writeObjectField(key, value);
    generator.writeEndObject();
  }

}
