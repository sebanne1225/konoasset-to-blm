"""
05_cleanup_tags.py
不要タグの削除・統合を行う。

DELETE_TAGS と MERGE_TAGS を自分のタグに合わせて編集してから使用。

使い方:
  1. BLM を閉じる
  2. python 05_cleanup_tags.py
"""

import sqlite3
import os

DB_PATH = os.path.expandvars(r"%AppData%\pm.booth.library-manager\data.db")

# === 削除するタグ ===
# 作者名・カテゴリ重複・表記ゆれなど、不要なタグをここに追加
DELETE_TAGS = [
    # 例: 作者名タグ（ショップで管理されるため不要）
    # "作者名A",
    # "作者名B",

    # 例: カテゴリ/リストと重複するタグ
    # "ギミックあり",
    # "ツール",

    # 例: 表記ゆれ・意味不明
    # "衣裳",  # 「衣装」の表記ゆれ
    # "単体",  # 意味不明
]

# === 統合するタグ（old → new） ===
MERGE_TAGS = {
    # 例: "神武器": "武器",
    # 例: "アイテクスチャ": "テクスチャ",
}


def main():
    if not os.path.exists(DB_PATH):
        print(f"ERROR: data.db not found: {DB_PATH}")
        return

    if not DELETE_TAGS and not MERGE_TAGS:
        print("DELETE_TAGS と MERGE_TAGS が空です。")
        print("スクリプトを編集して整理対象のタグを追加してください。")
        return

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    merged = 0
    deleted = 0

    # === タグ統合 ===
    if MERGE_TAGS:
        print("=== タグ統合 ===")
        for old_tag, new_tag in MERGE_TAGS.items():
            cur.execute(
                "SELECT booth_item_id FROM overwritten_booth_item_tags WHERE tag = ?",
                (old_tag,),
            )
            items = [r[0] for r in cur.fetchall()]
            for bid in items:
                cur.execute(
                    "INSERT OR IGNORE INTO overwritten_booth_item_tags (booth_item_id, tag) VALUES (?, ?)",
                    (bid, new_tag),
                )
            cur.execute(
                "DELETE FROM overwritten_booth_item_tags WHERE tag = ?", (old_tag,)
            )
            count = cur.rowcount
            print(f"  「{old_tag}」→「{new_tag}」({count}件)")
            merged += count

    # === タグ削除 ===
    if DELETE_TAGS:
        print("\n=== タグ削除 ===")
        for tag in DELETE_TAGS:
            cur.execute(
                "DELETE FROM overwritten_booth_item_tags WHERE tag = ?", (tag,)
            )
            count = cur.rowcount
            if count > 0:
                print(f"  「{tag}」削除 ({count}件)")
                deleted += count

    conn.commit()
    conn.close()

    print(f"\n完了: 削除 {deleted}件, 統合 {merged}件")


if __name__ == "__main__":
    main()
