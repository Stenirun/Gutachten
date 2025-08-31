package com.bauerfinanz.gutachten.api.converter;

import java.security.Principal;
import java.util.Arrays;
import java.util.Base64;
import java.util.HashSet;
import java.util.List;

import com.fasterxml.jackson.annotation.JsonProperty;
import com.fasterxml.jackson.databind.ObjectMapper;

import io.quarkus.runtime.annotations.RegisterForReflection;
import jakarta.ws.rs.core.SecurityContext;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import software.amazon.awssdk.utils.CollectionUtils;
import software.amazon.awssdk.utils.StringUtils;

/**
 * Authentication token to extract usernane for logging.
 * Autorization will be done in API Gateway.
 *
 * @author Markus Pichler
 * @version 0.0.1
 * @since 0.0.1
 */
@Data
@AllArgsConstructor
@NoArgsConstructor
@RegisterForReflection
@Slf4j
public class JWT {

  private static final String AUTH_SCHEMA = "Bearer";

  // id token values
  @JsonProperty("at_hash")
  private String atHash;
  @JsonProperty("email_verified")
  private Boolean emailVerified;
  @JsonProperty("cognito:preferred_role")
  String preferredRole;
  @JsonProperty("preferred_username")
  private String preferredUsername;
  @JsonProperty("given_name")
  private String firstName;
  @JsonProperty("family_name")
  private String lastName;
  @JsonProperty("cognito:username")
  private String cognitoName;
  @JsonProperty("email")
  private String email;

  // access token values
  private Integer version;
  @JsonProperty("cognito:groups")
  private List<String> groups;
  @JsonProperty("client_id")
  private String clientId;
  @JsonProperty("event_id")
  private String eventId;
  private String username;

  // shared token values
  private String sub;
  private String iss;
  @JsonProperty("token_use")
  private String tokenUse;
  private String scope;
  @JsonProperty("custom:groups")
  private String icosGroups;
  @JsonProperty("auth_time")
  private String authTime;
  private String exp;
  private String iat;
  private String jti;

  public boolean isScope(final String role) {
    return (scope + " ").contains(role + " ");
  }

  public SecurityContext getSecurityContext() {
    return new SecurityContext() {

      @Override
      public Principal getUserPrincipal() {
        return () -> "id".equalsIgnoreCase(getTokenUse())
          ? getPreferredUsername()
          : getUsername();
      }

      @Override
      public boolean isUserInRole(final String role) {
        return isScope(role);
      }

      @Override
      public boolean isSecure() {
        return false;
      }

      @Override
      public String getAuthenticationScheme() {
        return AUTH_SCHEMA;
      }

    };
  }

  public HashSet<String> getUserGroups() {
    if (!CollectionUtils.isNullOrEmpty(getGroups()) && getGroups().stream().allMatch(group -> group.startsWith("G"))) {
      return new HashSet<>(getGroups());
    }

    if (StringUtils.isNotBlank(getIcosGroups())) {
      return new HashSet<>(Arrays.asList(getIcosGroups().split(" ")));
    }

    return null;
  }

  public static JWT getInstance(final String accessToken, final ObjectMapper mapper) {
    try {
      if (StringUtils.isBlank(accessToken)) {
        return null;
      }
      String tmpJwt = StringUtils.replacePrefixIgnoreCase(accessToken, AUTH_SCHEMA + " ", "");
      tmpJwt = tmpJwt.split("\\.")[1];
      tmpJwt = new String(Base64.getDecoder().decode(tmpJwt));
      return mapper.readValue(tmpJwt, JWT.class);
    } catch (final Exception exc) {
      log.error("Can't extract access token", exc);
    }
    return null;
  }

}
