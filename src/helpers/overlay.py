import json
from pathlib import Path
from typing import List, Dict, Tuple

def load_page_overlay(page_json_path: Path) -> Tuple[List[Dict], Dict]:
    """
    Return (items, size) where:
      items -> list of dicts (block_id, bbox, confidence, text, page_index)
      size  -> {"width": px, "height": px}
    Works for every domain. The caller decides what to do with the text.
    """
    data = json.loads(page_json_path.read_text())
    return data["items"], data["size"]
