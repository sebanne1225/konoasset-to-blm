# KonoAsset to BOOTH Library Manager Migration Tools

KonoAsset のアセットデータを BOOTH Library Manager (BLM) に移行するための Python スクリプト集。

## 背景

KonoAsset で管理していた VRChat アセット約280個を BLM に引っ越すために作成。
BLM にはインポート機能がないため、SQLite（data.db）を直接操作するアプローチをとっている。

## ⚠️ 注意事項

- **BLM はアーリーアクセス中**（v0.2.1 で動作確認）。今後の更新で DB 構造が変わる可能性あり
- **必ず `data.db` のバックアップを取ってから**実行すること
- **実行前に BLM を閉じること**
- 実ファイル（unitypackage 等）は移行されない。BLM から再ダウンロードが必要

## 動作環境

- Python 3.10+
- requests（`pip install requests`）
- KonoAsset v1.2.5
- BOOTH Library Manager v0.2.1

## ファイル構成

```
├── 01_export_csv.py          # KonoAsset JSON → CSV一覧化
├── 02_import_items.py        # BLM に全アイテムを一括投入
├── 03_fix_subdomains.py      # BOOTH APIからショップ情報を修正
├── 04_create_lists.py        # リスト・スマートリスト・タグ投入
├── 05_cleanup_tags.py        # タグ整理（削除・統合）
└── README.md
```

## 使い方

### Step 0: 準備

1. KonoAsset のデータ保存先から JSON ファイルをコピー
   - `avatars.json`
   - `avatarWearables.json`
   - `otherAssets.json`
   - `worldObjects.json`

2. BLM の `data.db` の場所を確認
   - 通常: `%AppData%\pm.booth.library-manager\data.db`

3. **data.db をバックアップ**

### Step 1: CSV一覧化（任意）

```bash
python 01_export_csv.py
```

KonoAsset の全アセットを CSV に出力。移行前の確認用。

### Step 2: BLM にアイテム一括投入

```bash
python 02_import_items.py
```

`02_import_items.py` 冒頭の `KONOASSET_DIR` を KonoAsset のデータ保存先パスに変更してから実行。

### Step 3: ショップ情報の修正

```bash
pip install requests
python 03_fix_subdomains.py
```

BOOTH API から正しいショップサブドメインとサムネイル URL を取得して DB を更新。
約0.3秒/件のペースで BOOTH にアクセスするため、件数に応じて数分かかる。

### Step 4: リスト・タグ投入

```bash
python 04_create_lists.py
```

KonoAsset のカテゴリに基づいてリスト（大枠グループ）を作成し、アイテムを振り分ける。
よく使うタグでスマートリストも作成。

### Step 5: タグ整理（任意）

```bash
python 05_cleanup_tags.py
```

作者名タグ、カテゴリ重複タグの削除、表記ゆれの統合など。
`DELETE_TAGS` と `MERGE_TAGS` を編集して使用。

## 復元方法

問題が発生した場合、バックアップした `data.db` で上書きすれば元に戻る。

## 関連記事

- [Note: KonoAssetのアセット280個をBOOTH Library Managerに引っ越した話](TODO: URL)

## ライセンス

MIT
