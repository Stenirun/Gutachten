package com.bauerfinanz.gutachten.api.to;

import lombok.experimental.UtilityClass;

/**
 * Contains all static dynamodb table fields and table/ index name.
 *
 * @author Markus Pichler
 * @version 0.0.1
 * @since 0.0.1
 */
@UtilityClass
public class DBApiConstants {

	// Field separator and miscellaneous
	public static final String SEPARATOR = "#";
	public static final String SPLIT = ";";
	public static final String UNDERLINE = "_";
	public static final char DOT_SEPARATOR = '.';
	public static final Integer MAX_ELEMENTS_COUNT = 1000;
	public static final String CONSTRAINT_ERROR_PREFIX = "jakarta.validation";
	public static final String NEW_CONSTRAINT_ERROR_PREFIX = "input";

	// Index names
	public static final String INDEX_TYPE = "type_select";

	// Index fields
	public static final String ID_FIELD = "id";
	public static final String TYPE_FIELD = "type";
	public static final String DATA_FIELD = "data";

	// Config fields
	public static final String VALUE_FIELD = "value";

	// MetaData fields
	public static final String SYSTEM_TIMESTAMP_FIELD = "system_timestamp";
	public static final String CREATED_AT_FIELD = "created_at";
	public static final String CREATED_BY_FIELD = "created_by";
	public static final String MODIFIED_AT_FIELD = "modified_at";
	public static final String MODIFIED_BY_FIELD = "modifed_by";
	public static final String VERSION_FIELD = "version";
	public static final String PROCESS_STATE_FIELD = "process_state";

	// API fields
	public static final String ERROR_MSG_FIELD = "error_msg";
	public static final String ERROR_STATUS_FIELD = "error_status";
	public static final String STATUS_RETRY_FIELD = "status_retry";
	public static final String SYSTEM_EXIT_FIELD = "system_exit";
	public static final String NAME_FIELD = "name";
	public static final String DESCRIPTION_FIELD = "description";
	public static final String SCOPE_FIELD = "scope";
	public static final String USER_ID_FIELD = "user_id";

}
