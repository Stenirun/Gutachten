package com.bauerfinanz.gutachten.api.service;

import java.util.Comparator;
import java.util.List;

import com.bauerfinanz.gutachten.api.service.db.DynamoDBApiService;
import com.bauerfinanz.gutachten.api.to.sps.Customer;
import com.bauerfinanz.gutachten.api.to.sps.Status;

import io.smallrye.mutiny.Uni;
import jakarta.enterprise.context.ApplicationScoped;
import lombok.RequiredArgsConstructor;
import software.amazon.awssdk.utils.StringUtils;

/**
 * Gutachten data business logic.
 *
 * @author Markus Pichler
 * @version 0.0.1
 * @since 0.0.1
 */
@RequiredArgsConstructor
@ApplicationScoped
public class GutachtenService {

  private final DynamoDBApiService dbApiService;

	public Uni<Status> getStatus() {
		// TODO Auto-generated method stub
		return null;
	}

	public Uni<List<Customer>> getCustomerList() {
		// TODO Auto-generated method stub
		return null;
	}

//  public Uni<SPSStatusList> getSPSStatusList() {
//    return Uni.createFrom().completionStage(dbSPSDataService.getSPSStatusList())
//      .map(item -> SPSStatusList.builder()
//        .count(item.size())
//        .data(item.stream().sorted().toList())
//        .build());
//  }
//
//  public Uni<Void> resetSPSStatus() {
//    return Uni.createFrom().completionStage(dbSPSDataService.resetSPSStatus());
//  }
//
//  public Uni<SPSErrorList> getFTErrorList(final String ftId) {
//    return Uni.createFrom().completionStage(dbSPSDataService.getFTErrorList(ftId))
//      .map(item -> SPSErrorList.builder()
//        .count(item.size())
//        .data(item.stream().sorted().toList())
//        .build());
//  }
//
//  public Uni<SPSHistoryCommentList> getHistoryComments() {
//    return Uni.createFrom().completionStage(dbSPSDataService.getSPSHistoryCommentList())
//      .map(item -> SPSHistoryCommentList.builder()
//        .count(item.size())
//        .data(item.stream().sorted().toList())
//        .build());
//  }
//
//  public Uni<SPSHistoryComment> createHistoryComment(final SPSHistoryComment comment) {
//    return Uni.createFrom().completionStage(dbSPSDataService.createSPSHistoryComment(comment));
//  }
//
//  public Uni<SPSHistoryComment> deleteHistoryComment(final String commentId) {
//    return Uni.createFrom().completionStage(dbSPSDataService.deleteSPSHistoryComment(StringUtils.trimToNull(commentId)));
//  }
//
//  public Uni<SkidStockList> getSkidStock(final SkidStockType stockType) {
//    return Uni.createFrom().completionStage(dbSPSDataService.getSkidStockList())
//      .map(item -> {
//        final List<SkidStock> result = item.stream()
//          .sorted(Comparator.comparing(SkidStock::getLastUpdate).reversed())
//          .filter(entry -> entry.getElementType().isSkid() && stockType == SkidStockType.SKID
//            || stockType == SkidStockType.ALL
//            || !entry.getElementType().isSkid() && stockType == SkidStockType.CAR_AXLE)
//          .toList();
//        return SkidStockList.builder()
//          .count(result.size())
//          .lastUpdate(!result.isEmpty()
//            ? result.get(0).getLastUpdate()
//            : null)
//          .data(result)
//          .build();
//      });
//  }
//
//  public Uni<DuplicateList> getDuplicateList() {
//    return Uni.createFrom().completionStage(dbSPSDataService.getDuplicateList())
//      .map(item -> {
//        final List<Duplicate> result = item.stream()
//          .sorted(Comparator.comparing(Duplicate::getLastUpdate).reversed()).toList();
//        return DuplicateList.builder()
//          .count(item.size())
//          .data(result)
//          .lastUpdate(!result.isEmpty()
//            ? result.get(0).getLastUpdate()
//            : null)
//          .build();
//      });
//  }

}
