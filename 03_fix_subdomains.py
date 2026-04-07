"""
03_fix_subdomains.py
BOOTH API から正しいショップ情報・サムネイルを取得して DB を更新する。

使い方:
  1. pip install requests
  2. BLM を閉じる
  3. python 03_fix_subdomains.py
"""

import sqlite3
import os
import time

try:
    import requests
except ImportError:
    print("requests が必要です: pip install requests")
    exit(1)

DB_PATH = os.path.expandvars(r"%AppData%\pm.booth.library-manager\data.db")

SESSION = requests.Session()
SESSION.headers.update({
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept": "application/json",
})


def get_shop_info(booth_item_id):
    """BOOTH API から商品情報を取得"""
    url = f"https://booth.pm/ja/items/{booth_item_id}.json"
    try:
        resp = SESSION.get(url, timeout=15)
        if resp.status_code == 200:
            data = resp.json()
            shop = data.get("shop", {})
            item_images = data.get("images", [])
            return {
                "subdomain": shop.get("subdomain"),
                "shop_name": shop.get("name"),
                "shop_thumbnail": shop.get("thumbnail_url"),
                "item_thumbnail": item_images[0]["original"] if item_images else None,
            }
        elif resp.status_code == 404:
            print(f"404(削除済み?) ", end="")
        else:
            print(f"HTTP {resp.status_code} ", end="")
    except Exception as e:
        print(f"ERROR: {e} ", end="")
    return None


def main():
    if not os.path.exists(DB_PATH):
        print(f"ERROR: data.db not found: {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()

    cur.execute(
        "SELECT id, name, shop_subdomain FROM booth_items WHERE shop_subdomain LIKE 'shop_%'"
    )
    items = cur.fetchall()
    print(f"修正対象: {len(items)}件\n")

    if not items:
        print("修正対象なし。")
        conn.close()
        return

    fixed = 0
    failed = 0
    failed_list = []

    for i, (bid, name, old_sub) in enumerate(items):
        short_name = name[:40] + "..." if len(name) > 40 else name
        print(f"[{i+1}/{len(items)}] {short_name} ", end="", flush=True)

        info = get_shop_info(bid)
        if info and info["subdomain"]:
            subdomain = info["subdomain"]
            shop_name = info["shop_name"] or subdomain

            cur.execute(
                "SELECT name FROM shops WHERE subdomain = ?", (subdomain,)
            )
            if not cur.fetchone():
                cur.execute(
                    "INSERT INTO shops (subdomain, name, thumbnail_url) VALUES (?, ?, ?)",
                    (subdomain, shop_name, info.get("shop_thumbnail")),
                )

            cur.execute(
                "UPDATE booth_items SET shop_subdomain = ? WHERE id = ?",
                (subdomain, bid),
            )

            if info.get("item_thumbnail"):
                cur.execute(
                    "UPDATE booth_items SET thumbnail_url = ? WHERE id = ? AND thumbnail_url IS NULL",
                    (info["item_thumbnail"], bid),
                )

            print(f"-> {subdomain}")
            fixed += 1
        else:
            print("FAILED")
            failed += 1
            failed_list.append((bid, name))

        time.sleep(0.3)

        if (i + 1) % 50 == 0:
            conn.commit()
            print(f"  --- {i+1}件処理済み ---")

    conn.commit()

    cur.execute(
        "DELETE FROM shops WHERE subdomain LIKE 'shop_%' AND subdomain NOT IN (SELECT shop_subdomain FROM booth_items)"
    )
    conn.commit()
    conn.close()

    print(f"\n===== 完了 =====")
    print(f"修正成功: {fixed}件")
    print(f"失敗: {failed}件")

    if failed_list:
        print(f"\n--- 失敗リスト（削除済み商品の可能性） ---")
        for bid, name in failed_list:
            print(f"  {bid}: {name}")

    print("\n次のステップ: python 04_create_lists.py")


if __name__ == "__main__":
    main()
