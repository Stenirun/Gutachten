package com.bauerfinanz.gutachten.api.to;

import org.eclipse.microprofile.openapi.annotations.media.Schema;

import com.fasterxml.jackson.annotation.JsonIgnore;

import io.quarkus.runtime.annotations.RegisterForReflection;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.NoArgsConstructor;
import lombok.experimental.SuperBuilder;

/**
 * Base List fields for all kind of object lists.
 *
 * @author Markus Pichler
 * @version 0.0.1
 * @since 0.0.1
 */
@Data
@SuperBuilder
@NoArgsConstructor
@AllArgsConstructor
@RegisterForReflection
public class BaseList {

	@Schema(description = "Anzahl aller Elemente", required = true)
	private Integer count;

	@Schema(description = "Anzahl der Elemente pro Seite", hidden = true)
	@JsonIgnore
	private Integer pageSize;

	@Schema(description = "Anzuzeigende Seite", hidden = true)
	@JsonIgnore
	private Integer page;

	@Schema(description = "Sortierreihenfolge", hidden = true)
	@JsonIgnore
	private String sortField;

}
