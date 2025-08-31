package com.bauerfinanz.gutachten.authorizer.to;

import com.fasterxml.jackson.annotation.JsonProperty;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

/**
 * The Class Statement.
 *
 * @author Markus Pichler
 * @version 0.0.1
 * @since 0.0.1
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class Statement {

  @JsonProperty("Effect")
  private Effect effect;
  @JsonProperty("Action")
  private final String action = "execute-api:Invoke";
  @JsonProperty("Resource")
  private String resource;

  public enum Effect {
    Allow,
    Deny;
  }

}
