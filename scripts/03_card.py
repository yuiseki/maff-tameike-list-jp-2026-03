"""Write data/README.md (dataset card draft) from docs/build.json and docs/verification.json."""
import json, pathlib
b = json.load(open("docs/build.json")); v = json.load(open("docs/verification.json")); s = b["status_count"]
card = f"""---
license: other
license_name: pdl-1.0
license_link: https://www.digital.go.jp/resources/open_data/public_data_license_v1.0
language:
- ja
pretty_name: MAFF agricultural reservoir list (Japan, as of 2026-03-31)
tags:
- japan
- reservoirs
- tameike
- disaster-prevention
size_categories:
- 100K<n<1M
---

# MAFF agricultural reservoir list, Japan (as of 2026-03-31)

農林水産省が公表した「農業用ため池一覧(令和8年3月末時点)」を Parquet にしたものです。ため池防災支援システムに登録された農業用ため池 {b['rows']:,} 件(47都道府県)の、名称、所在地、座標、堤高、堤頂長、総貯水量、満水面積が入っています。

出典: 農林水産省ウェブサイト https://www.maff.go.jp/j/nousin/bousai/bousai_saigai/b_tameike/ichiran.html (2026-11-06 に取得)。
本データは、出典の Excel を加工して作成したもので、国(農林水産省)が作成したものではありません。

出典の記載: 「農業用ため池一覧(令和8年3月末時点)」(農林水産省) (https://www.maff.go.jp/j/nousin/bousai/bousai_saigai/b_tameike/ichiran.html) (2026年11月6日に利用)を加工して作成

## ライセンス

農林水産省のサイトは、権利表記がない限り公共データ利用規約(第1.0版、PDL1.0)に準拠した条件で利用できるとしています (https://www.maff.go.jp/j/use/link.html)。出典の表示と、加工した旨の明記が条件です。このデータの出典ページには、別の権利表記はありませんでした。

## 列

出典の Excel は 14 列で、度分秒の座標が分けて入っています。列名は次のように付けました。

| 列 | 出典の列 | 内容 |
|---|---|---|
| name | 名称 | |
| prefecture | 都道府県 | |
| municipality | 市区町村 | |
| address | 町域名、番地 | 1 件が空 |
| lat_deg, lat_min, lat_sec | 緯度、分、秒 | 度分秒のまま (出典の値) |
| lon_deg, lon_min, lon_sec | 経度、分2、秒2 | 度分秒のまま (出典の値) |
| dam_height_m | 堤高(m) | |
| crest_length_m | 堤頂長(m) | |
| storage_thousand_m3 | 総貯水量(千m3) | |
| surface_area_km2 | 満水面積(km2) | 空欄の行がある |
| source_row | | 出典の Excel の行番号 (1 行目は見出し) |
| lat, lon | | 十進法の度 (測地系の記載は出典に無い)。coord_status が suspect_ で始まる行と placeholder の行は null |
| lat_original, lon_original | | 出典の度分秒をそのまま換算した値 (null にならない) |
| coord_status | | 座標の判定結果 (下記) |

## 座標の判定と修正の手順

`scripts/coords.py` に実装し、`scripts/test_coords.py` でテストしています。

1. 度分秒を、度 + 分/60 + 秒/3600 で十進法にする。分または秒がちょうど 60 の行は、そのまま換算する (繰り上がりとして扱う)。
2. 緯度と経度の分と秒が全て 0 の行は、仮値として印を付け、lat と lon を null にする (出典の換算値は lat_original と lon_original に残る)。
3. 範囲 (緯度 20 から 46、経度 122 から 154) の外は、異常とする。
4. 行が 5 件以上ある市町村は、仮値を除いた点の中央値を持つ。その中央値から 50 km を超えて離れた点は、異常とする。5 件に満たない市町村は、距離では判定しない。
5. 異常な点だけ、次の順で修正を試す。(a) 経度の度に 100 を足す、(b) 緯度と経度を入れ替える。範囲内で、市町村の中央値から 30 km 以内に収まる最初の候補を採る。収まる候補が無ければ、lat と lon を null にし、出典の換算値は lat_original と lon_original にだけ残して、印を付ける。

結果 ({b['rows']:,} 行):

| coord_status | 行数 | 意味 |
|---|---|---|
| ok | {s.get('ok', 0):,} | 異常なし |
| ok_carry | {s.get('ok_carry', 0):,} | 分または秒が 60 (繰り上がりとして換算) |
| placeholder | {s.get('placeholder', 0):,} | 度が整数だけの仮値と思われる (石川県が 52 件。lat と lon は null) |
| fixed_lon_plus100 | {s.get('fixed_lon_plus100', 0):,} | 経度の度に 100 を足して修正 |
| fixed_swap | {s.get('fixed_swap', 0):,} | 緯度と経度を入れ替えて修正 |
| suspect_city_outlier | {s.get('suspect_city_outlier', 0):,} | 市町村の中央値から 50 km 超。修正案が無く、lat と lon は null |
| suspect_range | {s.get('suspect_range', 0):,} | 範囲外。修正案が無く、lat と lon は null |

修正した 1 行は、長野県飯山市の「相好」(出典の行 31968) です。出典では経度が 38 度 23 分 13 秒でしたが、経度に 100 度を足した 138 度 23 分 13 秒は、飯山市の池の中央値から 30 km 以内に収まります。`lon_original` に出典の換算値が残っています。修正した行と、修正しなかった疑わしい行の一覧は `docs/coord_review.jsonl` にあります。

## 注意

- 完全に同じ行が 16 種類 (33 行分の重複) あります。出典のまま残しています。`source_row` で区別できます。
- 出典の分割版 8 件 (地方別) は、全国版と同じ行の集まりです (分割版 1 の末尾の空行は除く)。照合は `scripts/02_verify.py` で、結果は `docs/verification.json` にあります (multiset_equal = {v['multiset_equal']})。
- 座標の測地系は、出典に記載がありません。
- 座標を使うときは、lat と lon が null の行を除いてください (coord_status が suspect_ で始まる行と placeholder の行)。
- 疑わしい座標の判定は、市町村内の他の点との距離だけによる、機械的なものです。島のある市町村や、広い市町村では、正しい座標を疑わしいと判定することがあります。

## 再現

```sh
python scripts/01_build.py   # tameike_ichiranR8.xlsx -> data/parquet/
python scripts/02_verify.py  # 分割版 8 件との照合
```

元の Excel は raw/data/ にあります。同じ Excel は https://www.maff.go.jp/j/nousin/bousai/bousai_saigai/b_tameike/ichiran.html から取得できます (SHA-256 は `docs/build.json`)。
"""
pathlib.Path("data/README.md").write_text(card, encoding="utf-8")
