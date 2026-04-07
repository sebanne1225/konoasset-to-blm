"""
04_create_lists.py
KonoAsset のカテゴリに基づいてリスト・スマートリストを作成する。

使い方:
  1. KONOASSET_DIR を自分の KonoAsset データ保存先に変更
  2. BLM を閉じる
  3. python 04_create_lists.py
"""

import json
import os
import sqlite3
from datetime import datetime, timezone

# === 設定 ===
KONOASSET_DIR = r"C:\vrc\Konoassts\metadata"  # KonoAsset のデータ保存先
DB_PATH = os.path.expandvars(r"%AppData%\pm.booth.library-manager\data.db")

# カテゴリ → リスト名の対応
CATEGORY_TO_LIST = {
    "衣装": "衣装",
    "ギミック": "ギミック",
    "小物": "小物・アクセサリー",
    "アクセサリー": "小物・アクセサリー",
    "テクスチャ": "テクスチャ・マテリアル",
    "マテリアル": "テクスチャ・マテリアル",
    "モーション": "モーション・表情",
    "表情": "モーション・表情",
    "ペット": "ペット",
    "髪型": "小物・アクセサリー",
    "プロファイル": "ギミック",
    "改変モデル": "衣装",
    "小物詰め合わせ": "小物・アクセサリー",
    "改変プレハブ": "ギミック",
    "靴": "衣装",
    "便利ツール": "ツール",
}

# スマートリストに使うタグ（よく使われるもの）
SMART_LIST_TAGS = [
    "ギミックあり", "かわいい", "アニメーション", "パーティクル",
    "きらきら", "かっこいい", "魔法", "ロリ系", "大人系", "武器",
    "もこもこ", "Quest対応", "無料",
]


def load_items():
    """KonoAsset の JSON からアイテムを読み込み、リスト名を割り当てる"""
    files = [
        ("avatars.json", "アバター素体"),
        ("avatarWearables.json", None),
        ("otherAssets.json", "ツール"),
    ]
    items = []
    for filename, default_list in files:
        path = os.path.join(KONOASSET_DIR, filename)
        if not os.path.exists(path):
            continue
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        for item in data["data"]:
            d = item["description"]
            bid = d.get("boothItemId")
            if not bid:
                continue
            if default_list:
                list_name = default_list
            else:
                cat = item.get("category", "")
                list_name = CATEGORY_TO_LIST.get(cat, "その他")
            items.append({
                "bid": bid,
                "tags": d.get("tags", []),
                "list_name": list_name,
            })
    return items


def main():
    if not os.path.exists(DB_PATH):
        print(f"ERROR: data.db not found: {DB_PATH}")
        return

    items = load_items()
    print(f"読み込み: {len(items)}件\n")

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    # === 1. ユーザータグ挿入 ===
    print("=== ユーザータグ挿入 ===")
    tag_count = 0
    for item in items:
        for tag in item["tags"]:
            cur.execute(
                "INSERT OR IGNORE INTO overwritten_booth_item_tags (booth_item_id, tag) VALUES (?, ?)",
                (item["bid"], tag),
            )
            if cur.rowcount > 0:
                tag_count += 1
    print(f"  {tag_count}件のタグを追加")

    # === 2. リスト作成 & 振り分け ===
    print("\n=== リスト作成 ===")
    list_names = sorted(set(item["list_name"] for item in items))
    list_id_map = {}

    for name in list_names:
        cur.execute("SELECT id FROM lists WHERE title = ?", (name,))
        row = cur.fetchone()
        if row:
            list_id_map[name] = row[0]
            print(f"  既存: {name}")
        else:
            cur.execute(
                "INSERT INTO lists (title, description, created_at, updated_at) VALUES (?, ?, ?, ?)",
                (name, f"KonoAssetから移行: {name}", now, now),
            )
            list_id_map[name] = cur.lastrowid
            print(f"  作成: {name}")

    print("\n=== リストにアイテム振り分け ===")
    list_item_count = 0
    for item in items:
        list_id = list_id_map[item["list_name"]]
        reg_id = f"b{item['bid']}"
        cur.execute("SELECT id FROM registered_items WHERE id = ?", (reg_id,))
        if not cur.fetchone():
            continue
        cur.execute(
            "INSERT OR IGNORE INTO list_items (list_id, item_id, added_at) VALUES (?, ?, ?)",
            (list_id, reg_id, now),
        )
        if cur.rowcount > 0:
            list_item_count += 1
    print(f"  {list_item_count}件をリストに振り分け")

    # === 3. スマートリスト作成 ===
    print("\n=== スマートリスト作成 ===")
    for tag in SMART_LIST_TAGS:
        cur.execute("SELECT id FROM smart_lists WHERE title = ?", (tag,))
        if cur.fetchone():
            print(f"  既存: {tag}")
            continue
        cur.execute(
            "INSERT INTO smart_lists (title, description, created_at, updated_at) VALUES (?, ?, ?, ?)",
            (tag, f"タグ「{tag}」のアイテム", now, now),
        )
        sl_id = cur.lastrowid
        cur.execute(
            "INSERT INTO smart_list_criteria (smart_list_id, age_restriction) VALUES (?, 'all')",
            (sl_id,),
        )
        cur.execute(
            "INSERT INTO smart_list_tags (smart_list_id, tag) VALUES (?, ?)",
            (sl_id, tag),
        )
        print(f"  作成: {tag}")

    conn.commit()
    conn.close()
    print(f"\n完了！ 次のステップ（任意）: python 05_cleanup_tags.py")


if __name__ == "__main__":
    main()
