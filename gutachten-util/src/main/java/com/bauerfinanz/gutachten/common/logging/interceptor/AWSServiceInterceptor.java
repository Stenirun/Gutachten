package com.bauerfinanz.gutachten.common.logging.interceptor;

import static com.bauerfinanz.gutachten.common.logging.LogDataArgument.data;
import static com.bauerfinanz.gutachten.common.logging.LogDataArgumentMap.dataMap;

import java.util.HashMap;
import java.util.Map;
import java.util.Optional;

import org.eclipse.microprofile.config.inject.ConfigProperty;
import org.slf4j.Logger;
import org.slf4j.MDC;

import com.bauerfinanz.gutachten.common.exception.Error;
import com.bauerfinanz.gutachten.common.exception.ErrorType;

import software.amazon.awssdk.core.interceptor.Context.AfterExecution;
import software.amazon.awssdk.core.interceptor.Context.BeforeExecution;
import software.amazon.awssdk.core.interceptor.ExecutionAttributes;
import software.amazon.awssdk.core.interceptor.ExecutionInterceptor;

/**
 * Generic AWs service Interceptor to log request and response tructures.
 *
 * @author Markus Pichler
 * @version 0.0.1
 * @since 0.0.1
 */
public abstract class AWSServiceInterceptor implements ExecutionInterceptor {

  @ConfigProperty(name = "quarkus.log.error.name", defaultValue = "error")
  String errorLabel;

  private Map<String, String> mdcMap = null;

  private final String serviceName;
  private final Logger log;
  private final boolean enabled;

  protected AWSServiceInterceptor(final String serviceName, final Logger log) {
    this.serviceName = serviceName;
    this.log = log;
    enabled = log.isTraceEnabled();
  }

  @Override
  public void beforeExecution(final BeforeExecution context, final ExecutionAttributes executionAttributes) {

    if (enabled) {
      try {
        mdcMap = MDC.getCopyOfContextMap();
        final Map<String, Object> dataMap = new HashMap<>();
        context.request().sdkFields().forEach(field -> {
          final Optional<?> value = context.request().getValueForField(field.memberName(), field.marshallingType().getTargetClass());
          dataMap.put(field.memberName(), value.isPresent()
            ? value.get().toString()
            : null);
        });

        String requestName = context.request().getClass().getName();
        requestName = requestName.substring(requestName.lastIndexOf('.') + 1);
        log.trace("{} {}", serviceName, requestName, dataMap(dataMap));
      } catch (final Exception exc) {
        final Error error = Error.builder()
          .errorCode(ErrorType.SDK_CLIENT_EXCEPTION.getCode())
          .errorMessage(exc.getMessage())
          .build();
        log.warn("Can't log {} request", serviceName, data(errorLabel, error), exc);
      }
    }

    ExecutionInterceptor.super.beforeExecution(context, executionAttributes);
  }

  @Override
  public void afterExecution(final AfterExecution context, final ExecutionAttributes executionAttributes) {

    if (enabled) {
      try {
        if (mdcMap != null) {
          MDC.setContextMap(mdcMap);
        }
        final Map<String, Object> dataMap = new HashMap<>();
        context.response().sdkFields().forEach(field -> {
          final Optional<?> value = context.response().getValueForField(field.memberName(), field.marshallingType().getTargetClass());
          dataMap.put(field.memberName(), value.isPresent()
            ? value.get().toString()
            : null);
        });

        String responsetName = context.response().getClass().getName();
        responsetName = responsetName.substring(responsetName.lastIndexOf('.') + 1);
        log.trace("{} {}", serviceName, responsetName, dataMap(dataMap));
      } catch (final Exception exc) {
        final Error error = Error.builder()
          .errorCode(ErrorType.SDK_CLIENT_EXCEPTION.getCode())
          .errorMessage(exc.getMessage())
          .build();
        log.warn("Can't log {} response", serviceName, data(errorLabel, error), exc);
      }
    }

    ExecutionInterceptor.super.afterExecution(context, executionAttributes);
  }

}
