# Changelog

このリポジトリの `japanese_krea.py` の変更履歴です。

## Unreleased

### Added
- macOS標準ダイアログによる日本語入力
- 前回の日本語入力を `last_prompt.txt` に保存し、次回起動時に復元
- 指定フォルダ内のLoRA一覧表示、番号選択、強度指定
- MFLUXによる画像生成後、生成されたPNGを自動表示

### Changed
- Ollamaへの翻訳指示を改善し、被写体・色・姿勢・動作を維持するよう明示
- LoRAで画風を指定できるよう、英訳時に画風を勝手に追加しない方針に変更
- 画像生成前のY/n確認を廃止
- ターミナルの `input()` による日本語編集の問題を避けるため、入力方法を変更

### Notes
- LoRAはファイルごとにKrea 2 Turboとの互換性確認が必要
- LoRA適用と画風の変化は `krea2_darkbrush.safetensors` で確認済み
