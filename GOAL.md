Candidate for Hugging Face / GitHub (not published, no approval yet).
Source: https://www.maff.go.jp/j/nousin/bousai/bousai_saigai/b_tameike/ichiran.html (agricultural reservoirs list, as of 2026-03-end; fetched 2026-11-06).
Terms: https://www.maff.go.jp/j/use/link.html says PDL1.0 unless a rights notice states otherwise; credit "出典:農林水産省ウェブサイト(URL)" and note edits. No other terms found on the data page.
Open checks before publishing: columns holding personal data or third-party rights (e.g. owner names), whether the 8 split files equal the national file.

Checked 2026-11-06 (converted with openpyxl to work/*.csv):
- Columns (14): 名称, 都道府県, 市区町村, 町域名・番地, 緯度(度,分,秒), 経度(度,分,秒), 堤高(m), 堤頂長(m), 総貯水量(千m3), 満水面積(km2). No owner or person columns.
- National file 161,846 rows, 47 prefectures. The 8 split files hold the same rows (multiset equal) once 26,983 empty rows at the end of split 1 are dropped. Okayama is split across files 5 and 6.
- Exact duplicate rows in the national file: 16 distinct rows, 33 extra copies (kept as published).
- 満水面積 blank in 12,197 rows; 町域名・番地 blank in 1.
- One coordinate looks wrong: row 31968 (相好, Nagano, Iiyama) has longitude degrees 38 (likely 138). Published as is, record it in the card.

Built 2026-11-06 (not published): scripts/01_build.py, 02_verify.py, 03_card.py, coords.py (11 tests pass), data/parquet/*.parquet, data/README.md (card draft), docs/{build,verification}.json, docs/coord_review.jsonl.
Coordinate rules are in scripts/coords.py; one row fixed (source_row 31968), 63 suspect rows kept as published and flagged.
