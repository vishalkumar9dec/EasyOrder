import sys
from pathlib import Path

REPO_ROOT = Path(__file__).parents[3]
sys.path.insert(0, str(REPO_ROOT))

from scripts.easyorder_demo_smoke import run_demo_smoke  # noqa: E402


def test_demo_smoke_runs_whatsapp_to_mock_checkout_flow() -> None:
    result = run_demo_smoke()

    assert str(result["session_id"]).startswith("session_")
    assert result["guest_role"] == "guest"
    assert result["cart_items_after_edit"] == 3
    assert result["checkout_groups"] == 2
    assert len(result["checkout_urls"]) == 2
    assert result["final_status"] == "ORDERED"
