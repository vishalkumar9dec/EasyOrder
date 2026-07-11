import sys
from pathlib import Path

REPO_ROOT = Path(__file__).parents[3]
sys.path.insert(0, str(REPO_ROOT))

from scripts.easyorder_security_smoke import run_security_smoke  # noqa: E402


def test_security_smoke_passes_release_blocking_checks() -> None:
    result = run_security_smoke()

    assert result["status"] == "passed"
    assert result["checks"] == [
        "request_id_header",
        "untagged_privacy",
        "prompt_injection_guardrail",
        "group_message_short_link_only",
        "guest_bootstrap_redacted",
        "invalid_token_read",
        "cross_session_write_blocked",
        "guest_checkout_blocked",
        "guest_confirm_blocked",
        "host_oauth_failure_safe",
        "host_checkout_validation_allowed",
    ]
