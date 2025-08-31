package com.bauerfinanz.gutachten.common.exception;

import java.util.List;

import org.eclipse.microprofile.openapi.annotations.media.Schema;

import io.quarkus.runtime.annotations.RegisterForReflection;
import lombok.AllArgsConstructor;
import lombok.Builder;
import lombok.Data;
import lombok.NoArgsConstructor;

/**
 * Unified Error Entity Class for Exception wrapper.
 *
 * @author Markus Pichler
 * @version 0.0.1
 * @since 0.0.1
 */
@Data
@Builder
@NoArgsConstructor
@AllArgsConstructor
@RegisterForReflection
@Schema(description = "Fehlerstruktur für detaillierte Fehlermeldung")
public class Error {

  @Schema(description = "Fehlercode")
  private Integer errorCode;
  @Schema(description = "Detail Fehlerwerte")
  private List<Violation> errorList;
  @Schema(description = "Fehlermeldung")
  private String errorMessage;
  @Schema(description = "Http Status Code")
  private Integer httpStatusCode;

  @Data
  @Builder
  @NoArgsConstructor
  @AllArgsConstructor
  @RegisterForReflection
  @Schema(description = "Fehlerwert")
  public static class Violation {

    @Schema(description = "Feld Name")
    private String field;
    @Schema(description = "Detaillierte Fehlernachricht")
    private String messageTemplate;
    @Schema(description = "Fehlerwerte")
    private List<Object> values;

  }

}
