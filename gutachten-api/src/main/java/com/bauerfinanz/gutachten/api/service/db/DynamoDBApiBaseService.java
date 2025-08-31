package com.bauerfinanz.gutachten.api.service.db;

import java.util.Map;

import org.eclipse.microprofile.config.ConfigProvider;

import com.bauerfinanz.gutachten.api.to.DBApiConstants;
import com.bauerfinanz.gutachten.api.to.GutachtenDBType;

import jakarta.enterprise.context.ApplicationScoped;
import lombok.extern.slf4j.Slf4j;
import software.amazon.awssdk.services.dynamodb.DynamoDbAsyncClient;
import software.amazon.awssdk.services.dynamodb.model.AttributeAction;
import software.amazon.awssdk.services.dynamodb.model.AttributeValue;
import software.amazon.awssdk.services.dynamodb.model.AttributeValueUpdate;
import software.amazon.awssdk.services.dynamodb.model.ReturnValue;
import software.amazon.awssdk.services.dynamodb.model.UpdateItemRequest;
import software.amazon.awssdk.services.dynamodb.model.UpdateItemResponse;
import software.amazon.awssdk.utils.StringUtils;

/**
 * Generic dynamodb service class.
 *
 * @author Markus Pichler
 * @version 0.0.1
 * @since 0.0.1
 */
@ApplicationScoped
@Slf4j
public class DynamoDBApiBaseService {

	private final DynamoDbAsyncClient dynamoDB;

	private final String spsTableName;

	DynamoDBApiBaseService(final DynamoDbAsyncClient dynamoDB) {
		this.dynamoDB = dynamoDB;
		spsTableName = ConfigProvider.getConfig().getValue("dynamodb.table.name", String.class);
		log.info("DynamoDB table: [{}] index: [{}]", spsTableName, DBApiConstants.INDEX_TYPE);
	}

	public String createID(final GutachtenDBType type) {
		final Map<String, AttributeValueUpdate> attributeMap = Map.of("id_count", AttributeValueUpdate.builder()
				.action(AttributeAction.ADD).value(AttributeValue.builder().n("1").build()).build());
		final Map<String, AttributeValue> keyMap = Map.of("id", AttributeValue.builder().s("IDGENERATOR").build(), "type",
				AttributeValue.builder().s(type.name()).build());

		final UpdateItemResponse response = dynamoDB.updateItem(UpdateItemRequest.builder().attributeUpdates(attributeMap)
				.key(keyMap).returnValues(ReturnValue.UPDATED_NEW).tableName(spsTableName).build()).join();
		String newId;
		if (StringUtils.isBlank(type.getIdPrefix())) {
			newId = response.attributes().get("id_count").n();
		} else {
			newId = type.getIdPrefix() + response.attributes().get("id_count").n();
		}
		log.debug("Generated new Id: [{}] for type: [{}]", newId, type);
		return newId;
	}

}
