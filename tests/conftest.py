from __future__ import annotations

import os


# Keep tests explicit and deterministic now that auth startup rejects
# missing or placeholder JWT secrets.
os.environ.setdefault("AUTH_SECRET", "test-auth-secret-0123456789abcdef")
