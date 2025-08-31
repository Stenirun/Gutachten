package com.bauerfinanz.gutachten.api.to;

import java.time.LocalDateTime;

import com.fasterxml.jackson.annotation.JsonIgnore;
import com.fasterxml.jackson.annotation.JsonInclude;
import com.fasterxml.jackson.annotation.JsonInclude.Include;
import com.bauerfinanz.gutachten.api.to.enums.ProcessState;

import io.quarkus.runtime.annotations.RegisterForReflection;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.experimental.SuperBuilder;
import software.amazon.awssdk.enhanced.dynamodb.mapper.annotations.DynamoDbAttribute;
import software.amazon.awssdk.enhanced.dynamodb.mapper.annotations.DynamoDbBean;

/**
 * Shared base fields for system updates.
 *
 * @author Markus Pichler
 * @version 0.0.1
 * @since 0.0.1
 */
@Data
@SuperBuilder(toBuilder = true)
@NoArgsConstructor
@AllArgsConstructor
@RegisterForReflection
@DynamoDbBean
@JsonInclude(value = Include.NON_NULL)
public class MetaDataSystem {

  @Getter(onMethod_ = {@DynamoDbAttribute(value = DBApiConstants.SYSTEM_TIMESTAMP_FIELD) })
  @JsonIgnore
  private LocalDateTime systemTimestamp;

  @Getter(onMethod_ = {@DynamoDbAttribute(value = DBApiConstants.PROCESS_STATE_FIELD) })
  @JsonIgnore
  private ProcessState processState;

}
