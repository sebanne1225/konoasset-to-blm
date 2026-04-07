"""
01_export_csv.py
KonoAsset の JSON データを CSV 一覧に変換する。

使い方:
  1. KONOASSET_DIR を自分の KonoAsset データ保存先に変更
  2. python 01_export_csv.py
"""

import json
import csv
import os

# === 設定 ===
KONOASSET_DIR = r"C:\vrc\Konoassts\metadata"  # KonoAsset のデータ保存先
OUTPUT_CSV = "konoasset_all_assets.csv"

FILES = [
    ("avatars.json", "アバター素体"),
    ("avatarWearables.json", "アバター関連"),
    ("otherAssets.json", "その他"),
    ("worldObjects.json", "ワールド"),
]


def main():
    rows = []
    for filename, asset_type in FILES:
        path = os.path.join(KONOASSET_DIR, filename)
        if not os.path.exists(path):
            print(f"SKIP: {path} (not found)")
            continue
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        for item in data["data"]:
            desc = item["description"]
            booth_url = (
                f"https://booth.pm/ja/items/{desc['boothItemId']}"
                if desc.get("boothItemId")
                else ""
            )
            rows.append({
                "アセットタイプ": asset_type,
                "カテゴリ": item.get("category", ""),
                "名前": desc["name"],
                "作者": desc.get("creator", ""),
                "BOOTHリンク": booth_url,
                "タグ": ", ".join(desc.get("tags", [])),
                "対応アバター": ", ".join(item.get("supportedAvatars", [])),
                "メモ": desc.get("memo") or "",
                "boothItemId": desc.get("boothItemId") or "",
            })

    with open(OUTPUT_CSV, "w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=rows[0].keys())
        writer.writeheader()
        writer.writerows(rows)

    print(f"完了: {len(rows)}件 -> {OUTPUT_CSV}")


if __name__ == "__main__":
    main()
