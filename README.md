# Japanese Krea

日本語の説明から、Mac上で画像を生成するPythonスクリプト `japanese_krea.py` です。

**日本語入力 → Ollamaで英語プロンプトに変換 → MFLUX / Krea 2 Turboで画像生成 → 画像を表示**

## 主な機能

- macOS標準の入力ダイアログで日本語を入力（前回の入力内容を自動復元）
- Ollamaで被写体・動作などを保った英語プロンプトに変換
- LoRAを番号で選択し、強度を指定（LoRAなしも選択可能）
- 生成画像を自動的に開く
- 生成前の確認操作は不要

## 必要な環境

- macOS（Apple Silicon）
- Python 3
- 起動済みのOllamaと、スクリプト内 `MODEL` で指定したモデル
- MFLUXの `mflux-generate-krea2` コマンド
- Krea 2 TurboのモデルにアクセスできるHugging Face環境

## 使い方

```bash
python3 japanese_krea.py
```

表示されたダイアログに日本語を入力し、続いてターミナルでLoRA番号と強度を選びます。LoRAを使わない場合は `0` を選択してください。生成後、画像が自動的に開きます。

日本語をコマンド引数で渡すこともできます。

```bash
python3 japanese_krea.py "太った白猫が椅子に座っている"
```

## 設定

`japanese_krea.py` 冒頭の定数を、自分の環境に合わせて変更してください。

| 定数 | 用途 |
| --- | --- |
| `MODEL` | Ollamaで使用するモデル名 |
| `OLLAMA_URL` | Ollama APIのURL |
| `HF_HOME` | Hugging Faceのキャッシュ保存先 |
| `LORA_DIR` | LoRAファイルの保存先 |
| `EXTRA_LORA_DIR` | 追加のLoRA検索先 |
| `PROMPT_HISTORY` | 前回入力した日本語の保存先 |

LoRAは上記のフォルダにある `.safetensors` ファイルを一覧表示します。**LoRAの互換性はファイルごとに異なります。**

## 注意事項

- Ollamaの英訳は必ずしも正確ではありません。生成前に英語プロンプトがターミナルへ表示されます。
- `last_prompt.txt` には入力した文章が保存されます。公開リポジトリに含めないでください。
- 生成時間・メモリ使用量はMacの構成やLoRAによって変わります。

変更履歴は [CHANGELOG.md](CHANGELOG.md) を参照してください。
