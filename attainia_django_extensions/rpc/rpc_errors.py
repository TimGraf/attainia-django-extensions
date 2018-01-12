"""
Error constants for RPC calls.

"""

ERRORS_KEY = "errors"

# Authentication and Authorization
NOT_AUTHENTICATED_KEY = "not_authenticated"
NOT_AUTHENTICATED_VALUE = "User not authenticated."
NOT_AUTHORIZED_KEY = "not_authorized"
NOT_AUTHORIZED_VALUE = "User not authorized."

VALIDATION_ERRORS_KEY = "validation_errors"

# Resource errors
OBJ_NOT_FOUND_KEY = "not_found"
OBJ_NOT_FOUND_ERROR_VALUE = "No object found with that ID"
MISSING_SEARCH_PARAM_KEY = "missing_search_param"
MISSING_SEARCH_PARAM_VALUE = "Missing required search parameter"
