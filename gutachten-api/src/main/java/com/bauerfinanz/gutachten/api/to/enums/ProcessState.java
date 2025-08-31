package com.bauerfinanz.gutachten.api.to.enums;

import org.eclipse.microprofile.openapi.annotations.media.Schema;

/**
 * Gutachten data process states.
 *
 * @author Markus Pichler
 * @version 0.0.1
 * @since 0.0.1
 *
 */
@Schema(description = "Gutachten Prozess Status", required = true, nullable = true)
public enum ProcessState {

	INIT, EVENT_NEW, EVENT_MODIFY, EVENT_PROCESS_MODIFY, EVENT_LOCKED, STATUS, IN_PROGRESS, EVENT_AGGREGATED,
	EVENT_TRIGGER_AGGREGATED, UNKNOWN;

}
