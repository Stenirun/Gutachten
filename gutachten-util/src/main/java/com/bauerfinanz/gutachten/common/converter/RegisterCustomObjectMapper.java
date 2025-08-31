package com.bauerfinanz.gutachten.common.converter;

import com.fasterxml.jackson.databind.DeserializationFeature;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.SerializationFeature;

import io.quarkus.jackson.ObjectMapperCustomizer;
import jakarta.inject.Singleton;

/**
 * Custom default object mapper for jackson de-/serialiaztion of pojo classes.
 *
 * @author Markus Pichler
 * @version 0.0.1
 * @since 0.0.1
 */
@Singleton
public class RegisterCustomObjectMapper implements ObjectMapperCustomizer {

  @Override
  public void customize(final ObjectMapper objectMapper) {
    objectMapper.disable(SerializationFeature.WRITE_DATES_AS_TIMESTAMPS);
    objectMapper.disable(DeserializationFeature.FAIL_ON_UNKNOWN_PROPERTIES);
    objectMapper.disable(SerializationFeature.FAIL_ON_EMPTY_BEANS);
  }

}
