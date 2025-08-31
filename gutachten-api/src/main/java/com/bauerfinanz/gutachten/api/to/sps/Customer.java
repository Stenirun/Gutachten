package com.bauerfinanz.gutachten.api.to.sps;

import org.eclipse.microprofile.openapi.annotations.media.Schema;

import com.fasterxml.jackson.annotation.JsonIgnore;
import com.fasterxml.jackson.annotation.JsonInclude;
import com.fasterxml.jackson.annotation.JsonInclude.Include;
import com.bauerfinanz.gutachten.common.converter.BooleanStringAttributeConverter;
import com.bauerfinanz.gutachten.api.to.DBApiConstants;
import com.bauerfinanz.gutachten.api.to.MetaDataSystem;
import com.bauerfinanz.gutachten.api.to.ApiDBType;
import io.quarkus.runtime.annotations.RegisterForReflection;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.EqualsAndHashCode;
import lombok.Getter;
import lombok.NoArgsConstructor;
import lombok.ToString;
import lombok.experimental.SuperBuilder;
import software.amazon.awssdk.enhanced.dynamodb.TableSchema;
import software.amazon.awssdk.enhanced.dynamodb.mapper.annotations.DynamoDbAttribute;
import software.amazon.awssdk.enhanced.dynamodb.mapper.annotations.DynamoDbBean;
import software.amazon.awssdk.enhanced.dynamodb.mapper.annotations.DynamoDbConvertedBy;
import software.amazon.awssdk.enhanced.dynamodb.mapper.annotations.DynamoDbPartitionKey;
import software.amazon.awssdk.enhanced.dynamodb.mapper.annotations.DynamoDbSecondarySortKey;
import software.amazon.awssdk.enhanced.dynamodb.mapper.annotations.DynamoDbSecondaryPartitionKey;
import software.amazon.awssdk.enhanced.dynamodb.mapper.annotations.DynamoDbSortKey;

/**
 * Complete Status entity.
 *
 * @author Markus Pichler
 * @version 0.0.1
 * @since 0.0.1
 */
@Data
@SuperBuilder
@EqualsAndHashCode(callSuper = true)
@ToString(callSuper = true)
@NoArgsConstructor
@AllArgsConstructor
@RegisterForReflection
@Schema(description = "Gutachten Status")
@DynamoDbBean
@JsonInclude(value = Include.NON_NULL)
public class Customer extends MetaDataSystem implements Comparable<Customer> {

	public static final TableSchema<Customer> CUSTOMER_TABLE_SCHEMA = TableSchema.fromClass(Customer.class);

	@Getter(onMethod_ = { @DynamoDbPartitionKey, @DynamoDbAttribute(value = DBApiConstants.ID_FIELD) })
	@Schema(description = "Name der Gruppe", required = true)
	private String id;

	@Getter(onMethod_ = { @DynamoDbSortKey, @DynamoDbSecondaryPartitionKey(indexNames = { DBApiConstants.INDEX_TYPE }),
			@DynamoDbAttribute(value = DBApiConstants.TYPE_FIELD) })
	@JsonIgnore
	private ApiDBType entity;

	@Getter(onMethod_ = { @DynamoDbSecondarySortKey(indexNames = DBApiConstants.INDEX_TYPE),
			@DynamoDbAttribute(value = DBApiConstants.DATA_FIELD),
			@DynamoDbConvertedBy(BooleanStringAttributeConverter.class) })
	@Schema(description = "Online Status", required = true)
	private Boolean state;

	@Override
	public int compareTo(final Customer o) {
		if (o == null) {
			return -1;
		}
		try {
			return getId().compareTo(o.getId());
		} catch (final Exception exc) {
			return -1;
		}
	}

}
