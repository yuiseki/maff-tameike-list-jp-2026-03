#!/usr/bin/env python3
"""Push the card, licence, provenance, Parquet, the provider's national Excel file, docs and scripts to the Hub.

uv run --with huggingface_hub --with pyarrow python src/publish.py         # dry run (the default; nothing is sent)
uv run --with huggingface_hub --with pyarrow python src/publish.py --push  # one commit (NOT to be run without the person's approval)

The provider's national file may be republished under PDL1.0 with a credit and a note that it was processed (data/LICENSE).
Not published: raw/split (the 8 regional files, same rows), work/, header files.
"""
import argparse, hashlib, json, sys
from datetime import UTC, datetime
from pathlib import Path

import pyarrow.parquet as pq

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
REPO = "yuiseki/maff-tameike-list-jp-2026-03"
PQ = "maff_tameike_ichiran_20260331.parquet"


def collect() -> dict[str, Path]:
    card = (DATA / "README.md").read_text(encoding="utf-8")
    ver = json.loads((ROOT / "docs" / "verification.json").read_text())
    if "license: other" not in card or "license_name:" not in card:
        raise SystemExit("the card does not declare license: other with a license_name")
    if "を加工して作成" not in card or "(農林水産省)" not in card:
        raise SystemExit("the card lacks the credit and the note about processing")
    if not ver["multiset_equal"] or ver["changed_rows"] != [31968] or not ver["lat_original_never_null"]:
        raise SystemExit("verification does not match the documented processing")
    t = pq.read_table(DATA / "parquet" / PQ)
    if t.num_rows != ver["parquet_rows"] or f"{t.num_rows:,}" not in card:
        raise SystemExit("row count differs from the verification or the card")
    files: dict[str, Path] = {"README.md": DATA / "README.md", "LICENSE": DATA / "LICENSE", "provenance.yaml": DATA / "provenance.yaml", f"parquet/{PQ}": DATA / "parquet" / PQ}  # fmt: skip
    for name in ("raw/data/tameike_ichiranR8.xlsx", "raw/page.html", "raw/link.html", "raw/download_log.tsv"):
        files[name] = ROOT / name
    for p in sorted((ROOT / "docs").glob("*")):
        if p.name != "revision.json":
            files[f"docs/{p.name}"] = p
    for sub in ("scripts", "src"):
        for p in sorted((ROOT / sub).glob("*")):
            if p.is_file() and p.suffix == ".py":
                files[f"{sub}/{p.name}"] = p
    return files


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with p.open("rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--repo", default=REPO)
    ap.add_argument("--push", action="store_true", help="upload; needs the person's approval")
    a = ap.parse_args()
    files = collect()
    print(f"{a.repo}\n  {len(files)} files, {sum(p.stat().st_size for p in files.values()):,} bytes")
    for k, v in files.items():
        print(f"  {v.stat().st_size:>12,}  {k}")
    if not a.push:
        print("\ndry run. pass --push to upload")
        return 0
    from huggingface_hub import CommitOperationAdd, HfApi

    api = HfApi()
    api.create_repo(a.repo, repo_type="dataset", exist_ok=True, private=False)
    ops = [CommitOperationAdd(path_in_repo=k, path_or_fileobj=str(v)) for k, v in files.items()]
    c = api.create_commit(a.repo, ops, repo_type="dataset", commit_message="Add the MAFF agricultural reservoir list (2026-03-31): 161,846 reservoirs as Parquet with a coordinate check")
    rev = {"repo": a.repo, "revision": c.oid, "pushed": datetime.now(UTC).isoformat(timespec="seconds"), "sha256": {k: sha256(v) for k, v in files.items()}}  # fmt: skip
    (ROOT / "docs" / "revision.json").write_text(json.dumps(rev, indent=1) + "\n")
    print(f"pushed {a.repo} revision {c.oid}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
