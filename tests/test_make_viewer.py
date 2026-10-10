import json
import sys
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import make_viewer  # noqa: E402


def fake_repo(tmp_path: Path) -> Path:
    for lang in ("en", "fr"):
        for n in (226, 225):
            d = tmp_path / f"chapters_{lang}" / f"chapter-{n}"
            d.mkdir(parents=True)
            for page in ("001", "002"):
                Image.new("RGB", (800, 1600), "white").save(d / f"{page}.webp")
    return tmp_path


def test_site_data_is_sorted_with_ids(tmp_path):
    root = fake_repo(tmp_path)
    data = make_viewer.site_data(make_viewer.chapter_data(root))
    assert [c["id"] for c in data] == ["225", "226"]
    assert data[0]["n"] == 225
    assert data[0]["pages"][0] == {
        "name": "001",
        "en": "chapters_en/chapter-225/001.webp",
        "fr": "chapters_fr/chapter-225/001.webp",
        "w": 800,
        "h": 1600,
    }


def test_write_site_creates_json_and_thumbs(tmp_path):
    root = fake_repo(tmp_path)
    make_viewer.write_site(root, make_viewer.chapter_data(root))
    data = json.loads((root / "site/src/data/chapters.json").read_text(encoding="utf-8"))
    assert len(data) == 2
    thumb = Image.open(root / "site/public/thumbs/225.webp")
    assert thumb.size == (400, 560)
