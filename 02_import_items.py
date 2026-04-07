"""
02_import_items.py
KonoAsset のアセットを BLM の SQLite に一括投入する。

使い方:
  1. KONOASSET_DIR を自分の KonoAsset データ保存先に変更
  2. BLM を閉じる
  3. data.db をバックアップ
  4. python 02_import_items.py
"""

import json
import os
import sqlite3
import shutil
from datetime import datetime, timezone

# === 設定 ===
KONOASSET_DIR = r"C:\vrc\Konoassts\metadata"  # KonoAsset のデータ保存先
DB_PATH = os.path.expandvars(r"%AppData%\pm.booth.library-manager\data.db")
BACKUP_PATH = DB_PATH + ".import_bak"

FILES = [
    ("avatars.json", 208, "3Dキャラクター"),
    ("avatarWearables.json", 209, "3D衣装"),
    ("otherAssets.json", 216, "ツール・その他"),
]


def load_items():
    """KonoAsset の JSON からアイテムを読み込む"""
    items = []
    for filename, subcat_id, subcat_name in FILES:
        path = os.path.join(KONOASSET_DIR, filename)
        if not os.path.exists(path):
            print(f"SKIP: {path} (not found)")
            continue
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        for item in data["data"]:
            d = item["description"]
            bid = d.get("boothItemId")
            if not bid:
                continue
            items.append({
                "bid": bid,
                "name": d["name"],
                "creator": d.get("creator", "") or "不明",
                "subdomain": f"shop_{bid}",
                "subcat_id": subcat_id,
                "subcat_name": subcat_name,
                "tags": d.get("tags", []),
                "published_at": d.get("publishedAt"),
            })
    return items


def main():
    if not os.path.exists(DB_PATH):
        print(f"ERROR: data.db が見つかりません: {DB_PATH}")
        return

    if not os.path.exists(BACKUP_PATH):
        shutil.copy2(DB_PATH, BACKUP_PATH)
        print(f"バックアップ作成: {BACKUP_PATH}")

    items = load_items()
    print(f"読み込み: {len(items)}件\n")

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    # parent_categories
    cur.execute(
        "INSERT OR IGNORE INTO parent_categories (name) VALUES (?)", ("3Dモデル",)
    )
    cur.execute(
        "SELECT id FROM parent_categories WHERE name = ?", ("3Dモデル",)
    )
    parent_cat_id = cur.fetchone()[0]

    # sub_categories
    for _, subcat_id, subcat_name in FILES:
        cur.execute(
            "INSERT OR IGNORE INTO sub_categories (id, name, parent_category_id) VALUES (?, ?, ?)",
            (subcat_id, subcat_name, parent_cat_id),
        )

    inserted = skipped = 0
    for item in items:
        bid = item["bid"]

        cur.execute(
            "SELECT id FROM registered_items WHERE booth_item_id = ?", (bid,)
        )
        if cur.fetchone():
            skipped += 1
            continue

        cur.execute(
            "INSERT OR IGNORE INTO shops (subdomain, name, thumbnail_url) VALUES (?, ?, NULL)",
            (item["subdomain"], item["creator"]),
        )

        pub = item.get("published_at")
        if pub:
            pub_str = datetime.fromtimestamp(
                pub / 1000, tz=timezone.utc
            ).strftime("%Y-%m-%dT%H:%M:%S+00:00")
        else:
            pub_str = now

        cur.execute(
            """INSERT OR IGNORE INTO booth_items
               (id, name, shop_subdomain, thumbnail_url, sub_category, description, adult, published_at, updated_at)
               VALUES (?, ?, ?, NULL, ?, NULL, ?, ?, ?)""",
            (bid, item["name"], item["subdomain"], item["subcat_id"], False, pub_str, now),
        )

        for tag in item["tags"]:
            cur.execute(
                "INSERT OR IGNORE INTO booth_tags (name) VALUES (?)", (tag,)
            )
            cur.execute(
                "INSERT OR IGNORE INTO booth_item_tag_relations (booth_item_id, tag) VALUES (?, ?)",
                (bid, tag),
            )

        cur.execute(
            """INSERT OR IGNORE INTO registered_items
               (id, booth_item_id, created_at, updated_at, user_item_info_id)
               VALUES (?, ?, ?, ?, NULL)""",
            (f"b{bid}", bid, now, now),
        )
        inserted += 1

    conn.commit()
    conn.close()

    print(f"完了: {inserted}件挿入, {skipped}件スキップ（既存）")
    print(f"問題があれば {BACKUP_PATH} から復元してください。")
    print("\n次のステップ: python 03_fix_subdomains.py")


if __name__ == "__main__":
    main()
