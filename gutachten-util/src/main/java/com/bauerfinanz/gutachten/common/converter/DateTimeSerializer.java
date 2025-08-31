package com.bauerfinanz.gutachten.common.converter;

import java.io.IOException;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;

import com.fasterxml.jackson.core.JsonGenerator;
import com.fasterxml.jackson.databind.SerializerProvider;
import com.fasterxml.jackson.databind.ser.std.StdSerializer;

/**
 * Serialize LocalDateTime to json string.
 *
 * @author Markus Pichler
 * @version 0.0.1
 * @since 0.0.1
 */
public class DateTimeSerializer extends StdSerializer<LocalDateTime> {

  private static final long serialVersionUID = -337755756206019152L;

  private static final DateTimeFormatter FORMATTER = DateTimeFormatter.ofPattern("uuuu-MM-dd'T'HH:mm:ss.SSS'Z'");

  public DateTimeSerializer() {
    this(null);
  }

  protected DateTimeSerializer(final Class<LocalDateTime> t) {
    super(t);
  }

  @Override
  public void serialize(final LocalDateTime value, final JsonGenerator gen, final SerializerProvider provider) throws IOException {
    gen.writeString(value.format(FORMATTER));
  }

}
