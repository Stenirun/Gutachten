package com.bauerfinanz.gutachten.authorizer.to;

import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

/**
 * The Class AuthorizerPolicy.
 *
 * @author Markus Pichler
 * @version 0.0.1
 * @since 0.0.1
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
public class AuthorizerPolicy {

  private String principalId;
  private PolicyDocument policyDocument;

}
