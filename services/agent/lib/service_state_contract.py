"""Static validation for the Night Shift service-state metadata contract."""

import re


SCHEMA_VERSION = "1.0"
REQUIRED_FIELDS = {
    "schema_version", "generated_at", "service_role", "service_name",
    "management_type", "observed_state", "enabled_state", "health_summary",
    "source_interface", "evidence_timestamp", "collection_status",
}
OPTIONAL_FIELDS = {"restart_count", "last_state_change", "reason_unavailable"}
ALLOWED_FIELDS = REQUIRED_FIELDS | OPTIONAL_FIELDS
PROHIBITED_FIELDS = {
    "environment", "environment_variables", "command", "command_line",
    "command_line_arguments", "raw_log", "raw_logs", "log_output",
    "unit_file", "unit_file_contents", "credentials", "token", "tokens",
    "api_key", "container_config", "container_configuration", "identity",
    "identities", "network_topology", "raw_output", "stdout", "stderr",
    "output",
}
SERVICE_ROLES = {"ollama", "ai_server_log_forwarder", "n8n_ai_pipeline"}
MANAGEMENT_TYPES = {"systemd", "docker_compose"}
OBSERVED_STATES = {"healthy", "degraded", "stopped", "unknown", "unavailable"}
ENABLED_STATES = {"enabled", "disabled", "unknown", "unavailable"}
SOURCE_INTERFACES = {
    "systemd_metadata_proxy", "docker_metadata_proxy", "unavailable",
}
COLLECTION_STATUSES = {"success", "partial", "unavailable"}
SERVICE_NAME = re.compile(r"^[a-z][a-z0-9_-]{0,63}$")
ISO_TIMESTAMP = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$")


def _valid_enum(value, allowed):
    return isinstance(value, str) and value in allowed


def _valid_timestamp(value):
    return isinstance(value, str) and bool(ISO_TIMESTAMP.fullmatch(value))


def validate_service_state(record):
    """Return a list of contract violations for a static metadata record."""
    if not isinstance(record, dict):
        return ["Record must be an object."]

    errors = []
    fields = set(record)
    for field in sorted(REQUIRED_FIELDS - fields):
        errors.append(f"Missing required field: {field}.")
    for field in sorted(fields & PROHIBITED_FIELDS):
        errors.append(f"Prohibited field: {field}.")
    for field in sorted(fields - ALLOWED_FIELDS - PROHIBITED_FIELDS):
        errors.append(f"Unknown field: {field}.")
    if fields - ALLOWED_FIELDS:
        return errors

    if record.get("schema_version") != SCHEMA_VERSION:
        errors.append("schema_version must be '1.0'.")
    for field in {"generated_at", "evidence_timestamp"}:
        if not _valid_timestamp(record.get(field)):
            errors.append(f"{field} must be a UTC ISO-8601 timestamp.")
    if not _valid_enum(record.get("service_role"), SERVICE_ROLES):
        errors.append("service_role is invalid.")
    name = record.get("service_name")
    if not isinstance(name, str) or not SERVICE_NAME.fullmatch(name):
        errors.append("service_name is invalid.")
    if not _valid_enum(record.get("management_type"), MANAGEMENT_TYPES):
        errors.append("management_type is invalid.")
    for field in {"observed_state", "health_summary"}:
        if not _valid_enum(record.get(field), OBSERVED_STATES):
            errors.append(f"{field} is invalid.")
    if not _valid_enum(record.get("enabled_state"), ENABLED_STATES):
        errors.append("enabled_state is invalid.")
    if not _valid_enum(record.get("source_interface"), SOURCE_INTERFACES):
        errors.append("source_interface is invalid.")
    if not _valid_enum(record.get("collection_status"), COLLECTION_STATUSES):
        errors.append("collection_status is invalid.")

    count = record.get("restart_count")
    if "restart_count" in record and (
        not isinstance(count, int) or isinstance(count, bool) or not 0 <= count <= 9999
    ):
        errors.append("restart_count must be an integer from 0 to 9999.")
    if "last_state_change" in record and not _valid_timestamp(record["last_state_change"]):
        errors.append("last_state_change must be a UTC ISO-8601 timestamp.")

    reason = record.get("reason_unavailable")
    if "reason_unavailable" in record and (
        not isinstance(reason, str) or not reason.strip() or len(reason) > 160 or "\n" in reason
    ):
        errors.append("reason_unavailable must be a short single-line string.")
    unavailable = record.get("collection_status") == "unavailable"
    if unavailable and not record.get("reason_unavailable"):
        errors.append("Unavailable collection requires reason_unavailable.")
    if not unavailable and "reason_unavailable" in record:
        errors.append("reason_unavailable is only allowed for unavailable collection.")
    if unavailable and record.get("source_interface") != "unavailable":
        errors.append("Unavailable collection requires source_interface 'unavailable'.")
    if not unavailable and record.get("source_interface") == "unavailable":
        errors.append("Available or partial collection requires a metadata proxy.")
    return errors
