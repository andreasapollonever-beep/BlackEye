import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from i18n_collect import collect  # noqa: E402


def test_every_user_facing_string_has_a_greek_translation():
    missing = collect()
    assert not missing, "Add to erisma/i18n_el.py:\n" + "\n".join(sorted(missing))
