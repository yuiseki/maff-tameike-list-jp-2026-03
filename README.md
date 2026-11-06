# maff-tameike-list-jp-2026-03

The MAFF agricultural reservoir list (農業用ため池一覧, as of 2026-03-31; 161,846 reservoirs in 47 prefectures) as Parquet, with decimal coordinates and a coordinate check.
The dataset is on the Hugging Face Hub: <https://huggingface.co/datasets/yuiseki/maff-tameike-list-jp-2026-03> (revision `ee87755e53cf5b049b31bc307aca56ad950771cc`, read back and checked against this tree).

- Card, licence, provenance: `data/README.md`, `data/LICENSE`, `data/provenance.yaml` (the Hub's README.md is `data/README.md`).
- Data: `data/parquet/maff_tameike_ichiran_20260331.parquet`; the provider's national file: `raw/data/tameike_ichiranR8.xlsx`.
- Checks: `docs/verification.json`, `docs/build.json`, `docs/verify_hub.json` (the Hub read back), `docs/coord_review.jsonl` (rows corrected or nulled).
- Scripts: `scripts/` (coordinate rules in `scripts/coords.py`), `src/publish.py`.

Source: <https://www.maff.go.jp/j/nousin/bousai/bousai_saigai/b_tameike/ichiran.html> (Public Data License 1.0 unless a rights notice says otherwise; credit and the note about processing are in `data/LICENSE`). Not a publication of MAFF.
