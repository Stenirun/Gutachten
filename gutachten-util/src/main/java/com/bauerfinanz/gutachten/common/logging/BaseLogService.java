package com.bauerfinanz.gutachten.common.logging;

import java.util.Set;

import lombok.AccessLevel;
import lombok.NoArgsConstructor;

/**
 * Base Logging service data container.
 *
 * @author Markus Pichler
 * @version 0.0.1
 * @since 0.0.1
 */
@NoArgsConstructor(access = AccessLevel.PROTECTED)
public class BaseLogService {

	public static final String SYSTEM_USER = "SYSTEM";
	public static final String REQUEST_ID = "x-request-id";
	public static final String EXTERNAL_ID = "x-external-id";

	private static InheritableThreadLocal<String> requestId = new InheritableThreadLocal<>();
	private static InheritableThreadLocal<String> externalId = new InheritableThreadLocal<>();
	private static InheritableThreadLocal<String> loginUser = new InheritableThreadLocal<>();
	private static InheritableThreadLocal<Set<String>> loginGroups = new InheritableThreadLocal<>();

	public static String getRequestId() {
		return requestId.get();
	}

	public static String getExternalId() {
		return externalId.get();
	}

	public static String getLoginUser() {
		return loginUser.get();
	}

	public static Set<String> getLoginGroups() {
		return loginGroups.get();
	}

	protected static void setRequestId(final String value) {
		requestId = new InheritableThreadLocal<>() {

			@Override
			protected String initialValue() {
				return value;
			}

		};

		requestId.set(value);
	}

	protected static void setExternalId(final String value) {
		externalId = new InheritableThreadLocal<>() {

			@Override
			protected String initialValue() {
				return value;
			}

		};

		externalId.set(value);
	}

	protected static void setLoginUser(final String value) {
		loginUser = new InheritableThreadLocal<>() {

			@Override
			protected String initialValue() {
				return value;
			}

		};
		loginUser.set(value);
	}

	protected static void setLoginGroups(final Set<String> value) {
		loginGroups = new InheritableThreadLocal<>() {

			@Override
			protected Set<String> initialValue() {
				return value;
			}

		};

		loginGroups.set(value);
	}

	public static void closeLogging() {
		setRequestId(null);
		setExternalId(null);
		setLoginUser(null);
		setLoginGroups(null);
	}

}
