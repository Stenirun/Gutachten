package com.bauerfinanz.gutachten.api.converter;

import static com.bauerfinanz.gutachten.common.logging.LogDataArgumentMap.dataMap;

import java.util.Map;

import org.jboss.resteasy.reactive.server.ServerRequestFilter;
import org.jboss.resteasy.reactive.server.ServerResponseFilter;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.bauerfinanz.gutachten.common.logging.BaseLogService;
import com.bauerfinanz.gutachten.common.logging.LogService;

import jakarta.ws.rs.container.ContainerRequestContext;
import jakarta.ws.rs.container.ContainerResponseContext;
import jakarta.ws.rs.core.MultivaluedMap;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;

/**
 * Request entry filter to initialize logging and get header pararms. Response
 * filter to add returned header params.
 *
 * @author Markus Pichler
 * @version 0.0.1
 * @since 0.0.1
 */
@Slf4j
@RequiredArgsConstructor
public class WebFilter {

	private final ObjectMapper mapper;

	@ServerRequestFilter(preMatching = true)
	public void filter(final ContainerRequestContext requestContext) {
		try {
			// extract jwt authentication
			final JWT token = JWT.getInstance(requestContext.getHeaderString("authorization"), mapper);
			if (token != null) {
				requestContext.setSecurityContext(token.getSecurityContext());
			}

			LogService.initLogging(requestContext.getHeaders(), requestContext.getSecurityContext(), token);
			log.info("Request",
					dataMap(Map.of("cookies", requestContext.getCookies(), "method", requestContext.getMethod(), "uri",
							requestContext.getUriInfo().getAbsolutePath(), "pathparameter",
							requestContext.getUriInfo().getPathParameters(true), "queryparameter",
							requestContext.getUriInfo().getQueryParameters(true), "header", requestContext.getHeaders())));
		} catch (final Exception exc) {
			log.error("Can't read Request values", exc);
		}
	}

	@ServerResponseFilter
	public void filter(final ContainerRequestContext requestContext, final ContainerResponseContext responseContext) {
		try {
			final MultivaluedMap<String, Object> headerMap = responseContext.getHeaders();
			if (BaseLogService.getRequestId() != null) {
				headerMap.putSingle(BaseLogService.REQUEST_ID, BaseLogService.getRequestId());
			}
			if (BaseLogService.getExternalId() != null) {
				headerMap.putSingle(BaseLogService.EXTERNAL_ID, BaseLogService.getExternalId());
			}

			Object responseBody = responseContext.hasEntity();
			if (log.isDebugEnabled() && responseContext.hasEntity()) {
				responseBody = responseContext.getEntity();
			}
			log.info("Response",
					dataMap(Map.of("request", LogService.getPayload() != null ? LogService.getPayload() : new Object(),
							"response", responseBody, "Header", headerMap)));
		} finally {
			LogService.closeLogging();
		}
	}

}
