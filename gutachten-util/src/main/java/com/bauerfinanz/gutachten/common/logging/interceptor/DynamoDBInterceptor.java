package com.bauerfinanz.gutachten.common.logging.interceptor;

import lombok.extern.slf4j.Slf4j;

/**
 * DynamoDBInterceptor to log request and response db structures.
 *
 * @author Markus Pichler
 * @version 0.0.1
 * @since 0.0.1
 */
@Slf4j
public class DynamoDBInterceptor extends AWSServiceInterceptor {

	public DynamoDBInterceptor() {
		super("DynamoDB", log);
	}

}
