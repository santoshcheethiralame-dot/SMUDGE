"""The golden generated cases join the registry before collection, so the shared kit contract runs on them too."""
import json
from pathlib import Path

import kits

for p in sorted((Path(kits.__file__).parent / "golden").glob("*.json")):
    kits.add_generated(json.loads(p.read_text(encoding="utf8")))
