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


def test_thumb_window_picks_the_detailed_area(tmp_path):
    # Page blanche en haut, zone contrastée plus bas : la vignette doit montrer la zone contrastée.
    page = Image.new("RGB", (800, 4000), "white")
    for x in range(0, 800, 40):
        page.paste((0, 0, 0), (x, 2500, x + 20, 3500))
    src = tmp_path / "p.webp"
    page.save(src)
    top = make_viewer.best_window([src])
    assert top[0] == src
    assert 1500 <= top[1] <= 3500


def test_thumb_window_prefers_detail_over_flat_contrast(tmp_path):
    # Haut : aplat moitié blanc moitié noir (fort contraste, peu de détail) ; bas : dégradé détaillé.
    page = Image.new("L", (800, 4000), 255)
    page.paste(0, (0, 500, 800, 1100))
    for y in range(2600, 3700):
        for x in range(0, 800, 4):
            page.paste((x + y) % 256, (x, y, x + 4, y + 1))
    src = tmp_path / "p.webp"
    page.convert("RGB").save(src)
    assert 1500 <= make_viewer.best_window([src])[1] <= 3700


def test_write_site_creates_json_and_thumbs(tmp_path):
    root = fake_repo(tmp_path)
    make_viewer.write_site(root, make_viewer.chapter_data(root))
    data = json.loads((root / "site/src/data/chapters.json").read_text(encoding="utf-8"))
    assert len(data) == 2
    thumb = Image.open(root / "site/public/thumbs/225.webp")
    assert thumb.size == (400, 560)
