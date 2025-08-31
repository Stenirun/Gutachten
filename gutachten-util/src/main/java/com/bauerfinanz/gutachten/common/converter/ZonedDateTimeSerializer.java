package com.bauerfinanz.gutachten.common.converter;

import java.io.IOException;
import java.time.ZoneOffset;
import java.time.ZonedDateTime;
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
public class ZonedDateTimeSerializer extends StdSerializer<ZonedDateTime> {

  private static final long serialVersionUID = -337755756206019152L;

  private static final DateTimeFormatter FORMATTER = DateTimeFormatter.ofPattern("uuuu-MM-dd'T'HH:mm:ss.SSS'Z'");

  public ZonedDateTimeSerializer() {
    this(null);
  }

  protected ZonedDateTimeSerializer(final Class<ZonedDateTime> t) {
    super(t);
  }

  @Override
  public void serialize(final ZonedDateTime value, final JsonGenerator gen, final SerializerProvider provider) throws IOException {
    gen.writeString(value.withZoneSameInstant(ZoneOffset.UTC).toLocalDateTime().format(FORMATTER));
  }

}
