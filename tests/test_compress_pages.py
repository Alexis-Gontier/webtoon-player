import os
import sys
from pathlib import Path

from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import compress_pages  # noqa: E402


def fake_repo(tmp_path: Path) -> Path:
    for lang in ("en", "fr"):
        d = tmp_path / f"chapters_{lang}" / "chapter-225"
        d.mkdir(parents=True)
        for page in ("001", "002"):
            # Bruit : une image unie se compresse trop bien pour mesurer un gain.
            Image.effect_noise((200, 600), 60).convert("RGB").save(d / f"{page}.webp", lossless=True)
    return tmp_path


def test_mirrors_both_languages_smaller(tmp_path):
    root = fake_repo(tmp_path)
    assert compress_pages.compress_all(root) == 4
    out = root / "chapters_web" / "fr" / "chapter-225" / "001.webp"
    src = root / "chapters_fr" / "chapter-225" / "001.webp"
    assert out.exists() and (root / "chapters_web/en/chapter-225/002.webp").exists()
    assert out.stat().st_size < src.stat().st_size
    assert Image.open(out).size == Image.open(src).size


def test_too_tall_for_webp_becomes_jpeg(tmp_path):
    root = fake_repo(tmp_path)
    tall = root / "chapters_fr" / "chapter-225" / "003.jpg"
    Image.new("RGB", (100, 17000), "white").save(tall, quality=100)
    compress_pages.compress_all(root)
    out = root / "chapters_web/fr/chapter-225/003.jpg"
    assert out.exists() and Image.open(out).size == (100, 17000)
    assert not (root / "chapters_web/fr/chapter-225/003.webp").exists()


def test_only_redoes_changed_pages(tmp_path):
    root = fake_repo(tmp_path)
    compress_pages.compress_all(root)
    assert compress_pages.compress_all(root) == 0
    src = root / "chapters_fr" / "chapter-225" / "002.webp"
    os.utime(src, (src.stat().st_atime, src.stat().st_mtime + 10))
    assert compress_pages.compress_all(root) == 1


def test_removes_copies_of_deleted_pages(tmp_path):
    root = fake_repo(tmp_path)
    compress_pages.compress_all(root)
    (root / "chapters_en" / "chapter-225" / "002.webp").unlink()
    compress_pages.compress_all(root)
    assert not (root / "chapters_web/en/chapter-225/002.webp").exists()
