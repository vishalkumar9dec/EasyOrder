import json
import logging

from app.observability import JsonFormatter, configure_logging, init_error_tracking


def test_json_formatter_emits_one_json_object_with_extra_fields_merged_in() -> None:
    formatter = JsonFormatter()
    record = logging.LogRecord(
        name="easyorder.api",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg="request_complete",
        args=(),
        exc_info=None,
    )
    record.request_id = "req_test_123"
    record.status_code = 200

    output = formatter.format(record)
    parsed = json.loads(output)

    assert parsed["message"] == "request_complete"
    assert parsed["level"] == "INFO"
    assert parsed["logger"] == "easyorder.api"
    assert parsed["request_id"] == "req_test_123"
    assert parsed["status_code"] == 200


def test_json_formatter_includes_exception_traceback() -> None:
    formatter = JsonFormatter()
    try:
        raise ValueError("boom")
    except ValueError:
        import sys

        record = logging.LogRecord(
            name="easyorder.api",
            level=logging.ERROR,
            pathname=__file__,
            lineno=1,
            msg="something_failed",
            args=(),
            exc_info=sys.exc_info(),
        )

    parsed = json.loads(formatter.format(record))

    assert "ValueError: boom" in parsed["exception"]


def test_configure_logging_sets_level_and_json_formatter() -> None:
    configure_logging(level="WARNING", log_format="json")
    root = logging.getLogger()

    assert root.level == logging.WARNING
    assert len(root.handlers) == 1
    assert isinstance(root.handlers[0].formatter, JsonFormatter)

    # Restore a sane default so this test doesn't leak into others in the run.
    configure_logging(level="INFO", log_format="text")


def test_configure_logging_text_format_uses_plain_formatter() -> None:
    configure_logging(level="INFO", log_format="text")
    root = logging.getLogger()

    assert not isinstance(root.handlers[0].formatter, JsonFormatter)


def test_init_error_tracking_is_a_noop_without_dsn() -> None:
    # Must not raise even though sentry_sdk is only imported when a DSN is set.
    init_error_tracking(dsn="", environment="local")
