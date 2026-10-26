#!/usr/bin/env python3
"""Japanese input -> faithful English prompt via Ollama -> MFLUX Krea 2 Turbo."""
import json
import os
from pathlib import Path
import subprocess
import sys
import urllib.error
import urllib.request

MODEL = "huihui_ai/Qwen3.8-abliterated:27b-q8_0"
OLLAMA_URL = "http://127.0.0.1:11434/api/generate"
HF_HOME = "/Volumes/Hanye2T/AI/mflux/huggingface"
LORA_DIR = Path("/Volumes/Hanye2T/AI/mflux/loras")
EXTRA_LORA_DIR = Path("/Volumes/Hanye2T/AI/ComfyDesktop/Models/loras")
PROMPT_HISTORY = Path("/Volumes/Hanye2T/AI/mflux/last_prompt.txt")

SYSTEM_PROMPT = """You are a precise Japanese-to-English translator for image generation.
Translate the user's Japanese description faithfully into one English image prompt.
CRITICAL RULES:
- Preserve the exact main subject and species. A cat must remain a cat, never a person.
- Preserve all specified colors, body shapes, poses, body parts, actions, and relationships.
- Do not substitute a human for an animal, or change the actor of an action.
- Preserve unusual, surreal, humorous, or anthropomorphic scenes exactly as requested.
- Do not censor, normalize, or rewrite unusual scenes into more ordinary ones.
- Do not invent people, objects, settings, camera angles, or plot details.
- Do not add any style terms (photorealistic, watercolor, anime, painting, etc.) unless explicitly stated in Japanese.
- Translate content only; a separate LoRA controls the visual style.
- Output only a single English prompt, with no explanations or quotation marks.
Example Japanese: 太った白猫が後ろ足をだして座りタバコを吸っている
Example English: A fat white cat is sitting with its hind legs stretched out in front of it, smoking a cigarette.
"""


def translate(japanese: str) -> str:
    payload = {
        "model": MODEL,
        "stream": False,
        "think": False,
        "system": SYSTEM_PROMPT,
        "prompt": f"Translate this Japanese image description faithfully into English:\n{japanese}",
        "options": {"temperature": 0.0},
    }
    request = urllib.request.Request(
        OLLAMA_URL,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(request, timeout=300) as response:
        data = json.load(response)
    result = data.get("response", "").strip()
    if not result:
        raise RuntimeError("Ollama returned an empty prompt")
    return result


def japanese_input() -> str:
    """Use a native macOS dialog with the previous prompt prefilled."""
    previous = PROMPT_HISTORY.read_text(encoding="utf-8") if PROMPT_HISTORY.exists() else ""
    applescript = """
on run argv
    set previousText to item 1 of argv
    set dialogResult to display dialog "画像を日本語で説明してください" default answer previousText buttons {"キャンセル", "OK"} default button "OK"
    return text returned of dialogResult
end run
"""
    result = subprocess.run(
        ["osascript", "-e", applescript, previous],
        capture_output=True, text=True, check=False,
    )
    if result.returncode != 0:
        if "User canceled" in result.stderr or "-128" in result.stderr:
            return ""
        raise RuntimeError(f"日本語入力ダイアログを開けません: {result.stderr.strip()}")
    japanese = result.stdout.strip()
    if japanese:
        PROMPT_HISTORY.parent.mkdir(parents=True, exist_ok=True)
        PROMPT_HISTORY.write_text(japanese, encoding="utf-8")
    return japanese


def choose_lora():
    """List available LoRA files and return (path, scale), or (None, None)."""
    paths = sorted({p.resolve() for folder in (LORA_DIR, EXTRA_LORA_DIR)
                    if folder.is_dir() for p in folder.glob("*.safetensors")},
                   key=lambda p: p.name.lower())
    print("\n画風（LoRA）を選択してください:")
    print("  0: LoRAなし（通常のKrea 2 Turbo）")
    for i, path in enumerate(paths, 1):
        print(f"  {i}: {path.stem}")
    while True:
        choice = input("番号 [0]: ").strip() or "0"
        if choice.isdecimal() and 0 <= int(choice) <= len(paths):
            break
        print("表示された番号を入力してください。")
    if choice == "0":
        return None, None
    path = paths[int(choice) - 1]
    while True:
        raw = input("LoRA強度 [1.0]: ").strip() or "1.0"
        try:
            scale = float(raw)
            if 0 <= scale <= 2:
                return path, scale
        except ValueError:
            pass
        print("0〜2の数値を入力してください（通常は1.0）。")


def main() -> int:
    try:
        japanese = " ".join(sys.argv[1:]).strip() or japanese_input()
    except (OSError, RuntimeError) as error:
        print(error, file=sys.stderr)
        return 1
    if not japanese:
        print("日本語の入力がありません。", file=sys.stderr)
        return 1
    lora_path, lora_scale = choose_lora()
    try:
        english = translate(japanese)
    except (urllib.error.URLError, TimeoutError, RuntimeError) as error:
        print(f"Ollamaとの通信に失敗しました: {error}", file=sys.stderr)
        return 1
    print(f"\n英語プロンプト:\n{english}\n", flush=True)
    env = os.environ.copy()
    env["HF_HOME"] = HF_HOME
    before = {p: p.stat().st_mtime_ns for p in Path.cwd().glob("*.png")}
    print("MFLUXで画像生成します。", flush=True)
    command = [
        "mflux-generate-krea2", "--prompt", english,
        "--width", "1024", "--height", "1024",
        "--seed", "42", "--steps", "8", "-q", "8",
    ]
    if lora_path is not None:
        command.extend(["--lora-paths", str(lora_path), "--lora-scales", str(lora_scale)])
        print(f"LoRA: {lora_path.name} (強度 {lora_scale})", flush=True)
    try:
        subprocess.run(command, env=env, check=True)
    except FileNotFoundError:
        print("mflux-generate-krea2 が見つかりません。", file=sys.stderr)
        return 1
    except subprocess.CalledProcessError as error:
        print(f"画像生成に失敗しました（終了コード {error.returncode}）。", file=sys.stderr)
        return error.returncode or 1
    changed = [p for p in Path.cwd().glob("*.png")
               if p not in before or p.stat().st_mtime_ns != before[p]]
    if changed:
        output = max(changed, key=lambda p: p.stat().st_mtime_ns)
        print(f"生成画像: {output}")
        subprocess.run(["open", str(output)], check=False)
    else:
        print("生成画像が見つかりません。MFLUXの出力先を確認してください。", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
