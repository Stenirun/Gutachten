package com.bauerfinanz.gutachten.common.logging;

import java.io.IOException;
import java.util.logging.Level;

import org.jboss.logmanager.ExtLogRecord;

import io.quarkiverse.loggingjson.JsonGenerator;
import io.quarkiverse.loggingjson.JsonProvider;
import jakarta.inject.Singleton;

/**
 * Writes unique logId and timestamp in millis to log entry.
 *
 * @author Markus Pichler
 * @version 1.0.0
 * @since 1.0.0
 */
@Singleton
public class LogIdProvider implements JsonProvider {

  @Override
  public void writeTo(final JsonGenerator generator, final ExtLogRecord event) throws IOException {

    if (event.getLevel().intValue() < Level.FINE.intValue()) {
      generator.writeStringField("Source", event.getSourceMethodName() + ":" + event.getSourceLineNumber());
    }
    event.disableCallerCalculation();
  }

}