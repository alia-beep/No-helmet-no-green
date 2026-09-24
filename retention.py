from pathlib import Path
from datetime import datetime, timedelta

MEDIA_EXTENSIONS = {".mp4", ".avi", ".mov", ".mkv", ".jpg", ".jpeg", ".png"}

def delete_older_than(root, days=30, dry_run=False):
    root = Path(root)
    cutoff = datetime.now() - timedelta(days=days)
    deleted = []
    if not root.exists():
        return deleted
    for p in root.rglob("*"):
        if p.is_file() and p.suffix.lower() in MEDIA_EXTENSIONS:
            if datetime.fromtimestamp(p.stat().st_mtime) < cutoff:
                deleted.append(str(p))
                if not dry_run:
                    p.unlink()
    return deleted

if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default="videos")
    ap.add_argument("--days", type=int, default=30)
    ap.add_argument("--dry-run", action="store_true")
    a = ap.parse_args()
    files = delete_older_than(a.root, a.days, a.dry_run)
    print(("Would delete" if a.dry_run else "Deleted"), len(files), "file(s)")
    for f in files:
        print(f)
