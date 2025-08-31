package com.bauerfinanz.gutachten.authorizer.to;

import java.util.List;

import com.fasterxml.jackson.annotation.JsonProperty;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

/**
 * The Class PolicyDocument.
 *
 * @author Markus Pichler
 * @version 0.0.1
 * @since 0.0.1
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class PolicyDocument {

  @JsonProperty("Version")
  private final String version = "2012-10-17";
  @JsonProperty("Statement")
  private List<Statement> statements;

}