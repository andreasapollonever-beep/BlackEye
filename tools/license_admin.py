"""Issue Erisma licence keys (publisher only — keep the private key secret!).

    python tools/license_admin.py --private-key erisma_private_key.txt \\
        --name "Γραφείο Μελετών Χ" --email client@example.com --expires 2027-12-31

Leave --expires out for a perpetual licence.  Never commit the private key file.
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from erisma import ed25519, license as lic  # noqa: E402

ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
ap.add_argument("--private-key", required=True, help="file with the 64-hex-digit private key")
ap.add_argument("--name", required=True)
ap.add_argument("--email", default="")
ap.add_argument("--plan", default="pro")
ap.add_argument("--expires", default="", help="YYYY-MM-DD (empty = perpetual)")
a = ap.parse_args()
sk = bytes.fromhex(Path(a.private_key).read_text().strip())
if ed25519.public_key(sk) != lic.PUBLIC_KEY:
    sys.exit("This private key does not match the public key built into Erisma.")
key = lic.make_key(sk, a.name, a.email, a.plan, a.expires)
lic.parse_key(key)  # self-check
print(key)
