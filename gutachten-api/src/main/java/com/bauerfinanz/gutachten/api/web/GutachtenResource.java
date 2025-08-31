package com.bauerfinanz.gutachten.api.web;

import static com.bauerfinanz.gutachten.common.logging.LogDataArgument.data;

import java.util.List;

import org.eclipse.microprofile.openapi.annotations.parameters.Parameter;
import org.eclipse.microprofile.openapi.annotations.responses.APIResponse;

import com.bauerfinanz.gutachten.api.service.GutachtenService;
import com.bauerfinanz.gutachten.api.to.sps.Customer;
import com.bauerfinanz.gutachten.api.to.sps.Status;

import io.smallrye.mutiny.Uni;
import jakarta.ws.rs.Consumes;
import jakarta.ws.rs.DefaultValue;
import jakarta.ws.rs.GET;
import jakarta.ws.rs.PUT;
import jakarta.ws.rs.Path;
import jakarta.ws.rs.Produces;
import jakarta.ws.rs.QueryParam;
import jakarta.ws.rs.core.MediaType;
import jakarta.ws.rs.core.Response;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;

/**
 * Contains all REST controller functions for gutachten service calls.
 *
 * @author Markus Pichler
 * @version 0.0.1
 * @since 0.0.1
 */
@Consumes(MediaType.APPLICATION_JSON)
@Produces(MediaType.APPLICATION_JSON)
@Path("/")
@RequiredArgsConstructor
@Slf4j
public class GutachtenResource {

  private final GutachtenService gutachtenService;

  @GET
  @Path("status")
  @APIResponse(responseCode = "200", description = "System Status aller SPS Elemente")
  public Uni<Status> getStatus() {

    log.info("Get Gutachten status");

    return gutachtenService.getStatus();
  }

  @GET
  @Path("customer")
  @APIResponse(responseCode = "204", description = "Setzt autoRetry für System Status aller SPS Elemente zurück")
  public Uni<List<Customer>> getCustomerList() {

    log.info("get all customer");

    return gutachtenService.getCustomerList();
  }

//  @GET
//  @Path("user")
//  @APIResponse(responseCode = "200", description = "Skid Gesamtbestand.")
//  public Uni<List<User>> getSkidStock(
//    @QueryParam(value = "type")
//    @Parameter(description = "Ergebnistyp: Skidbestand oder Gesamt Elementbestand")
//    @DefaultValue(value = "SKID")
//    final SkidStockType type) {
//
//    log.info("Get skid stock", data("stockType", type));
//
//    return spsService.getSkidStock(type);
//  }


}
