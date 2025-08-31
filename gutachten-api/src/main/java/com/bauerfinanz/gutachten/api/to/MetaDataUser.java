package com.bauerfinanz.gutachten.api.to;

import java.time.LocalDateTime;

import org.eclipse.microprofile.openapi.annotations.media.Schema;

import com.fasterxml.jackson.annotation.JsonIgnore;
import com.fasterxml.jackson.annotation.JsonInclude;
import com.fasterxml.jackson.annotation.JsonInclude.Include;
import com.fasterxml.jackson.databind.annotation.JsonSerialize;
import com.bauerfinanz.gutachten.common.converter.DateTimeSerializer;
import com.bauerfinanz.gutachten.api.to.enums.ProcessState;

import io.quarkus.runtime.annotations.RegisterForReflection;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.experimental.SuperBuilder;
import software.amazon.awssdk.enhanced.dynamodb.extensions.annotations.DynamoDbVersionAttribute;
import software.amazon.awssdk.enhanced.dynamodb.mapper.UpdateBehavior;
import software.amazon.awssdk.enhanced.dynamodb.mapper.annotations.DynamoDbAttribute;
import software.amazon.awssdk.enhanced.dynamodb.mapper.annotations.DynamoDbBean;
import software.amazon.awssdk.enhanced.dynamodb.mapper.annotations.DynamoDbUpdateBehavior;

/**
 * Shared metadata fields for user changeable elements.
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
public class MetaDataUser {

	@Getter(onMethod_ = { @DynamoDbVersionAttribute, @DynamoDbAttribute(value = DBApiConstants.VERSION_FIELD) })
	@Schema(description = "DB Entity Versionsnummer")
	private Integer version;

	@Getter(onMethod_ = { @DynamoDbUpdateBehavior(UpdateBehavior.WRITE_IF_NOT_EXISTS),
			@DynamoDbAttribute(value = DBApiConstants.CREATED_BY_FIELD) })
	@Schema(description = "Erstellt von", hidden = true)
	@JsonIgnore
	private String createdBy;

	@Getter(onMethod_ = { @DynamoDbUpdateBehavior(UpdateBehavior.WRITE_IF_NOT_EXISTS),
			@DynamoDbAttribute(value = DBApiConstants.CREATED_AT_FIELD) })
	@Schema(description = "Erstellt am", implementation = LocalDateTime.class, example = "2022-03-10T12:15:50.785Z", required = true)
	@JsonSerialize(using = DateTimeSerializer.class)
	private LocalDateTime createdAt;

	@Getter(onMethod_ = { @DynamoDbAttribute(value = DBApiConstants.MODIFIED_BY_FIELD) })
	@Schema(description = "Geändert von", hidden = true)
	@JsonIgnore
	private String modifiedBy;

	@Getter(onMethod_ = { @DynamoDbAttribute(value = DBApiConstants.MODIFIED_AT_FIELD) })
	@Schema(description = "Geändert am", hidden = true)
	@JsonIgnore
	private LocalDateTime modifiedAt;

	@Getter(onMethod_ = { @DynamoDbAttribute(value = DBApiConstants.PROCESS_STATE_FIELD) })
	@JsonIgnore
	private ProcessState processState;

}
