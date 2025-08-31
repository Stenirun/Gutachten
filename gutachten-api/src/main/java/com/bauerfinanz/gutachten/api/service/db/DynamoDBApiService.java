package com.bauerfinanz.gutachten.api.service.db;

import java.util.ArrayList;
import java.util.Collections;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.concurrent.CompletableFuture;
import java.util.stream.Collectors;

import org.eclipse.microprofile.config.ConfigProvider;

import com.bauerfinanz.gutachten.api.to.DBApiConstants;
import com.bauerfinanz.gutachten.api.to.GutachtenDBType;
import com.bauerfinanz.gutachten.api.to.ApiDBType;
import com.bauerfinanz.gutachten.api.to.sps.Customer;
import com.bauerfinanz.gutachten.api.to.sps.Status;
import com.bauerfinanz.gutachten.api.to.sps.User;

import jakarta.enterprise.context.ApplicationScoped;
import lombok.extern.slf4j.Slf4j;
import software.amazon.awssdk.enhanced.dynamodb.DynamoDbAsyncIndex;
import software.amazon.awssdk.enhanced.dynamodb.DynamoDbAsyncTable;
import software.amazon.awssdk.enhanced.dynamodb.DynamoDbEnhancedAsyncClient;
import software.amazon.awssdk.enhanced.dynamodb.Key;
import software.amazon.awssdk.enhanced.dynamodb.model.QueryConditional;
import software.amazon.awssdk.enhanced.dynamodb.model.QueryEnhancedRequest;

/**
 * DynamoDBApiService functions for gutachten API data handling.
 *
 * @author Markus Pichler
 * @version 0.0.1
 * @since 0.0.1
 */
@ApplicationScoped
@Slf4j
public class DynamoDBApiService {

  private final DynamoDBApiBaseService dbApiBaseService;

  private final DynamoDbAsyncTable<Status> statusTable;
  private final DynamoDbAsyncTable<Customer> customerTable;
  private final DynamoDbAsyncTable<User> userTable;

  DynamoDBApiService(final DynamoDbEnhancedAsyncClient dynamoDBEnhanced, final DynamoDBApiBaseService dbApiBaseService) {
    this.dbApiBaseService = dbApiBaseService;
    final String tableName = ConfigProvider.getConfig().getValue("dynamodb.table.name", String.class);
    statusTable = dynamoDBEnhanced.table(tableName, Status.STATUS_TABLE_SCHEMA);
    customerTable = dynamoDBEnhanced.table(tableName, Customer.CUSTOMER_TABLE_SCHEMA);
    userTable = dynamoDBEnhanced.table(tableName, User.USER_TABLE_SCHEMA);
    log.info("DynamoDB table: [{}] index: [{}]", tableName, DBApiConstants.INDEX_TYPE);
  }

//  public CompletableFuture<List<SPSStatus>> getSPSStatusList() {
//    final List<SPSStatus> spsList = new ArrayList<>();
//    final Key key = Key.builder().partitionValue(SPSDataDBType.STATUS.name()).build();
//
//    return spsStatusTypeIndex.query(QueryEnhancedRequest.builder()
//      .queryConditional(QueryConditional.keyEqualTo(key)).build())
//      .subscribe(res -> spsList.addAll(res.items())).thenApply(v -> spsList).thenCombine(getSPSErrorList(), (statusList, errorMap) -> {
//        statusList.forEach(status -> status.setErrorMsgs(errorMap.getOrDefault(status.getSsgId(), new ArrayList<>())));
//        return statusList;
//      });
//  }
//
//  public CompletableFuture<Void> resetSPSStatus() {
//    final Key key = Key.builder().partitionValue(SPSDataDBType.STATUS.name()).build();
//
//    return spsStatusTypeIndex.query(QueryEnhancedRequest.builder()
//      .queryConditional(QueryConditional.keyEqualTo(key)).build())
//      .subscribe(res -> res.items().forEach(item -> {
//        item.setAutoRetry(0);
//        spsStatusTable.updateItem(item).join();
//      }));
//  }
//
//  public CompletableFuture<Map<String, List<SPSError>>> getSPSErrorList() {
//    final List<SPSError> spsList = new ArrayList<>();
//    final Key key = Key.builder().partitionValue(SPSDataDBType.SPS_ERROR.name()).build();
//    return spsErrorTypeIndex.query(QueryEnhancedRequest.builder()
//      .queryConditional(QueryConditional.keyEqualTo(key)).build())
//      .subscribe(res -> spsList.addAll(res.items())).thenApply(v -> spsList.stream().sorted()
//        .collect(Collectors.groupingBy(SPSError::getSsgId, LinkedHashMap::new, Collectors.toList())));
//  }
//
//  public CompletableFuture<List<SPSError>> getFTErrorList(final String ftId) {
//    final List<SPSError> spsList = new ArrayList<>();
//    final Key key = Key.builder().partitionValue(SPSDataDBType.SPS_ERROR.name()).sortValue(ftId + DBSpsDataConstants.SEPARATOR).build();
//    return spsErrorTypeIndex.query(QueryEnhancedRequest.builder()
//      .queryConditional(QueryConditional.sortBeginsWith(key)).build())
//      .subscribe(res -> spsList.addAll(res.items())).thenApply(v -> {
//        Collections.sort(spsList);
//        return spsList;
//      });
//  }
//
//  public CompletableFuture<List<SPSHistoryComment>> getSPSHistoryCommentList() {
//    final List<SPSHistoryComment> spsList = new ArrayList<>();
//    final Key key = Key.builder().partitionValue(SPSDataDBType.HISTORY_COMMENT.name()).build();
//    return spsHistoryCommentTypeIndex.query(QueryEnhancedRequest.builder()
//      .queryConditional(QueryConditional.keyEqualTo(key)).build())
//      .subscribe(res -> spsList.addAll(res.items())).thenApply(v -> spsList);
//  }
//
//  public CompletableFuture<SPSHistoryComment> createSPSHistoryComment(final SPSHistoryComment comment) {
//    // set meta data values
//    comment.setId(dbSPSDataBaseService.createID(SPSDBType.HISTORY_COMMENT));
//    comment.setEntity(SPSDataDBType.HISTORY_COMMENT);
//    return spsHistoryCommentTable.putItem(comment).thenApply(v -> comment);
//  }
//
//  public CompletableFuture<SPSHistoryComment> deleteSPSHistoryComment(final String commentId) {
//    final Key key = Key.builder().partitionValue(commentId).sortValue(SPSDataDBType.HISTORY_COMMENT.name()).build();
//    return spsHistoryCommentTable.deleteItem(key);
//  }
//
//  public CompletableFuture<List<SkidStock>> getSkidStockList() {
//    final List<SkidStock> stockList = new ArrayList<>();
//    final Key key = Key.builder().partitionValue(SPSDataDBType.SKID_STOCK.name()).build();
//    return skidStockTypeIndex.query(QueryEnhancedRequest.builder()
//      .queryConditional(QueryConditional.keyEqualTo(key))
//      .attributesToProject(List.of(DBSpsDataConstants.ID_FIELD, DBSpsDataConstants.TYPE_FIELD, DBSpsDataConstants.MAX_ELEMENTS_FIELD,
//        DBSpsDataConstants.SYSTEM_TIMESTAMP_FIELD))
//      .build())
//      .subscribe(res -> stockList.addAll(res.items())).thenApply(v -> stockList);
//  }
//
//  public CompletableFuture<List<Duplicate>> getDuplicateList() {
//    final List<Duplicate> duplicateList = new ArrayList<>();
//    final Key key = Key.builder().partitionValue(SPSDataDBType.DUPLICATE.name()).build();
//    return duplicateTypeIndex.query(QueryEnhancedRequest.builder()
//      .queryConditional(QueryConditional.keyEqualTo(key)).build())
//      .subscribe(res -> duplicateList.addAll(res.items())).thenApply(v -> duplicateList);
//  }

}
