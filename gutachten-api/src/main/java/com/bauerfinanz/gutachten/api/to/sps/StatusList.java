package com.bauerfinanz.gutachten.api.to.sps;

import java.util.List;

import org.eclipse.microprofile.openapi.annotations.media.Schema;

import com.bauerfinanz.gutachten.api.to.BaseList;

import io.quarkus.runtime.annotations.RegisterForReflection;
import lombok.AllArgsConstructor;
import lombok.Data;
import lombok.EqualsAndHashCode;
import lombok.NoArgsConstructor;
import lombok.ToString;
import lombok.experimental.SuperBuilder;

/**
 * The Class StatusList.
 *
 * @author Markus Pichler
 * @version 0.0.1
 * @since 0.0.1
 */
@Data
@SuperBuilder
@EqualsAndHashCode(callSuper = true)
@ToString(callSuper = true)
@NoArgsConstructor
@AllArgsConstructor
@RegisterForReflection
@Schema(description = "Status Liste")
public class StatusList extends BaseList {

	@Schema(description = "Gutachten Status", required = true)
	List<Status> data;

}
