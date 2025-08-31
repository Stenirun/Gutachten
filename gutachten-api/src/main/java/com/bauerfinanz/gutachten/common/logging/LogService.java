package com.bauerfinanz.gutachten.common.logging;

import static com.bauerfinanz.gutachten.common.logging.LogDataArgumentMap.dataMap;

import java.util.Map;
import java.util.UUID;

import org.slf4j.MDC;

import com.bauerfinanz.gutachten.api.converter.JWT;

import jakarta.ws.rs.core.MultivaluedMap;
import jakarta.ws.rs.core.SecurityContext;
import lombok.experimental.UtilityClass;
import lombok.extern.slf4j.Slf4j;
import software.amazon.awssdk.utils.StringUtils;

/**
 * The Log Service contains base logging functions for meta data and json
 * logging.
 *
 * @author Markus Pichler
 * @version 0.0.1
 * @since 0.0.1
 */
@UtilityClass
@Slf4j
public class LogService extends BaseLogService {

	private static InheritableThreadLocal<JWT> userToken = new InheritableThreadLocal<>();
	private static InheritableThreadLocal<Object> payload = new InheritableThreadLocal<>();

	public static JWT getUserToken() {
		return userToken.get();
	}

	private static void setToken(final JWT token) {
		userToken = new InheritableThreadLocal<>() {

			@Override
			protected JWT initialValue() {
				return token;
			}

		};
		userToken.set(token);
	}

	public static Object getPayload() {
		return payload.get();
	}

	public static void setPayload(final Object entity) {
		payload = new InheritableThreadLocal<>() {

			@Override
			protected Object initialValue() {
				return entity;
			}

		};
		payload.set(entity);
	}

	public static void closeLogging() {
		BaseLogService.closeLogging();
		setToken(null);
		setPayload(null);
	}

	/**
	 * Init logging for lambda http request from api-gateway.
	 *
	 * @param headerMap       the headers
	 * @param securityContext the security context
	 */
	public static void initLogging(final MultivaluedMap<String, String> headerMap, final SecurityContext securityContext,
			final JWT token) {

		initLogging(headerMap != null ? headerMap.getFirst(REQUEST_ID) : null,
				headerMap != null ? headerMap.getFirst(EXTERNAL_ID) : null, securityContext, token);

	}

	public static void initLogging(final String requestIdValue, final String externalIdValue,
			final SecurityContext securityContext, final JWT token) {
		setRequestId(requestIdValue);
		setExternalId(externalIdValue);
		setToken(token);
		String user = "n/a";
		try {
			// generate new Request Id
			if (getRequestId() == null) {
				setRequestId(UUID.randomUUID().toString());
			}

			// extract user
			String authSchema = "n/a";
			if (securityContext != null) {
				if (securityContext.getAuthenticationScheme() != null) {
					authSchema = securityContext.getAuthenticationScheme();
				}
				if (securityContext.getUserPrincipal() != null
						&& StringUtils.isNotBlank(securityContext.getUserPrincipal().getName())) {
					user = securityContext.getUserPrincipal().getName().toLowerCase();
				}
			}
			setLoginUser(user);

			// extract user groups
			if (token != null) {
				setLoginGroups(token.getUserGroups());
			}

			// add meta data for each logging request
			MDC.put("correlationId", getRequestId());
			MDC.put("userId", getLoginUser());
			if (getExternalId() != null) {
				MDC.put("externalId", getExternalId());
			}

			log.debug("Initialize Request Id", dataMap(Map.of("securityUserId", user, "securitySchema", authSchema)));
		} catch (final Exception exc) {
			log.error("Can't construct initial logging context data - continue with normal event logging", exc);
		}
	}

}
