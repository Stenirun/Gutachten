package com.bauerfinanz.gutachten.common.converter;

import software.amazon.awssdk.enhanced.dynamodb.AttributeConverter;
import software.amazon.awssdk.enhanced.dynamodb.AttributeValueType;
import software.amazon.awssdk.enhanced.dynamodb.EnhancedType;
import software.amazon.awssdk.services.dynamodb.model.AttributeValue;

/**
 * The Class BooleanStringAttributeConverter.
 *
 * @author Markus Pichler
 * @version 0.0.1
 * @since 0.0.1
 */
public class BooleanStringAttributeConverter implements AttributeConverter<Boolean> {

  @Override
  public AttributeValue transformFrom(final Boolean input) {
    return AttributeValue.builder().s(input.toString()).build();
  }

  @Override
  public Boolean transformTo(final AttributeValue input) {
    return Boolean.valueOf(input.s());
  }

  @Override
  public EnhancedType<Boolean> type() {
    return EnhancedType.of(Boolean.class);
  }

  @Override
  public AttributeValueType attributeValueType() {
    return AttributeValueType.S;
  }

}
