#!/usr/bin/env python3
"""Japanese input -> faithful English prompt via Ollama -> MFLUX Krea 2 Turbo."""
import json
import tempfile
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
SETTINGS_PATH = Path("/Volumes/Hanye2T/AI/mflux/krea_settings.json")
OUTPUT_DIR = Path.cwd()

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


SWIFT_DIALOG = r"""
import AppKit
import Foundation

class RadioHandler: NSObject {
    var buttons: [NSButton] = []
    weak var promptView: NSTextView?
    @objc func pastePrompt(_ sender: NSButton) {
        guard let text = NSPasteboard.general.string(forType: .string), !text.isEmpty else {
            NSSound.beep()
            return
        }
        promptView?.string = text
        if let view = promptView { view.window?.makeFirstResponder(view) }
    }
    @objc func select(_ sender: NSButton) {
        for b in buttons { b.state = (b === sender) ? .on : .off }
    }
}

let data = FileHandle.standardInput.readDataToEndOfFile()
let config = (try? JSONSerialization.jsonObject(with: data)) as? [String: Any] ?? [:]
let names = config["names"] as? [String] ?? ["LoRAなし"]
let previous = config["previous"] as? String ?? "LoRAなし"
let promptDefault = config["prompt"] as? String ?? ""
let seedDefault = config["seed"] as? String ?? "42"
let scaleDefault = config["scale"] as? String ?? "1.0"
let stepsDefault = config["steps"] as? String ?? "8"

let app = NSApplication.shared
app.setActivationPolicy(.regular)
let alert = NSAlert()
alert.messageText = "Krea 2 Turbo"
alert.informativeText = "日本語・LoRA・シード・強度をまとめて設定します。"
alert.addButton(withTitle: "画像生成")
alert.addButton(withTitle: "キャンセル")

let width: CGFloat = 480
let viewHeight: CGFloat = 490
let view = NSView(frame: NSRect(x: 0, y: 0, width: width, height: viewHeight))

func label(_ text: String, _ y: CGFloat) {
    let field = NSTextField(labelWithString: text)
    field.frame = NSRect(x: 4, y: y, width: width - 8, height: 21)
    view.addSubview(field)
}

label("日本語プロンプト（前回の内容を編集できます）", 463)
let promptScroll = NSScrollView(frame: NSRect(x: 4, y: 350, width: width - 8, height: 110))
promptScroll.hasVerticalScroller = true
promptScroll.borderType = .bezelBorder
let promptText = NSTextView(frame: NSRect(x: 0, y: 0, width: width - 24, height: 110))
promptText.isRichText = false
promptText.isEditable = true
promptText.isSelectable = true
promptText.font = NSFont.systemFont(ofSize: 14)
promptText.string = promptDefault
promptScroll.documentView = promptText
view.addSubview(promptScroll)

let pasteButton = NSButton(title: "クリップボードから貼り付け", target: nil, action: nil)
pasteButton.frame = NSRect(x: 274, y: 461, width: 200, height: 27)
view.addSubview(pasteButton)

label("LoRA（1つ選択）", 326)
let lineHeight: CGFloat = 23
let contentHeight = CGFloat(names.count) * lineHeight + 12
let loraScroll = NSScrollView(frame: NSRect(x: 4, y: 92, width: width - 8, height: 230))
loraScroll.hasVerticalScroller = true
loraScroll.borderType = .bezelBorder
let doc = NSView(frame: NSRect(x: 0, y: 0, width: width - 28, height: contentHeight))
let handler = RadioHandler()
handler.promptView = promptText
pasteButton.target = handler
pasteButton.action = #selector(RadioHandler.pastePrompt(_:))
for (i, name) in names.enumerated() {
    let button = NSButton(radioButtonWithTitle: name, target: handler, action: #selector(RadioHandler.select(_:)))
    button.frame = NSRect(x: 8, y: contentHeight - CGFloat(i + 1) * lineHeight - 3,
                          width: width - 48, height: lineHeight)
    button.state = (name == previous) ? .on : .off
    handler.buttons.append(button)
    doc.addSubview(button)
}
if !handler.buttons.contains(where: { $0.state == .on }) {
    handler.buttons.first?.state = .on
}
loraScroll.documentView = doc
view.addSubview(loraScroll)

let seedLabel = NSTextField(labelWithString: "シード")
seedLabel.frame = NSRect(x: 4, y: 57, width: 78, height: 22)
view.addSubview(seedLabel)
let seedField = NSTextField(string: seedDefault)
seedField.frame = NSRect(x: 72, y: 55, width: 90, height: 25)
view.addSubview(seedField)

let stepsLabel = NSTextField(labelWithString: "ステップ数")
stepsLabel.frame = NSRect(x: 174, y: 57, width: 82, height: 22)
view.addSubview(stepsLabel)
let stepsField = NSTextField(string: stepsDefault)
stepsField.frame = NSRect(x: 257, y: 55, width: 57, height: 25)
view.addSubview(stepsField)

let scaleLabel = NSTextField(labelWithString: "LoRA強度")
scaleLabel.frame = NSRect(x: 325, y: 57, width: 78, height: 22)
view.addSubview(scaleLabel)
let scaleField = NSTextField(string: scaleDefault)
scaleField.frame = NSRect(x: 408, y: 55, width: 66, height: 25)
view.addSubview(scaleField)

let note = NSTextField(labelWithString: "画像は krea_0001.png, krea_0002.png ... と連番保存")
note.frame = NSRect(x: 4, y: 14, width: width - 8, height: 22)
view.addSubview(note)

alert.accessoryView = view
app.activate(ignoringOtherApps: true)
alert.window.initialFirstResponder = promptText
let response = alert.runModal()
if response != .alertFirstButtonReturn { exit(2) }
let index = handler.buttons.firstIndex(where: { $0.state == .on }) ?? 0
let output: [String: Any] = [
    "prompt": promptText.string,
    "index": index,
    "seed": seedField.stringValue,
    "steps": stepsField.stringValue,
    "scale": scaleField.stringValue
]
let json = try! JSONSerialization.data(withJSONObject: output)
FileHandle.standardOutput.write(json)
"""


def choose_settings(initial_prompt: str = ""):
    """Single macOS dialog for Japanese text, LoRA, seed, steps and scale."""
    paths = sorted(
        {p.resolve() for folder in (LORA_DIR, EXTRA_LORA_DIR)
         if folder.is_dir() for p in folder.glob("*.safetensors")},
        key=lambda p: p.name.lower(),
    )
    settings = {}
    if SETTINGS_PATH.exists():
        try:
            settings = json.loads(SETTINGS_PATH.read_text(encoding="utf-8"))
        except (ValueError, OSError):
            pass
    previous_prompt = settings.get("prompt", "")
    if not previous_prompt and PROMPT_HISTORY.exists():
        previous_prompt = PROMPT_HISTORY.read_text(encoding="utf-8")
    previous_path = settings.get("lora", "")
    names = ["LoRAなし"] + [p.stem for p in paths]
    previous_index = next((i + 1 for i, path in enumerate(paths)
                           if str(path) == previous_path), 0)
    payload = {
        "names": names,
        "previous": names[previous_index],
        "prompt": initial_prompt or previous_prompt,
        "seed": str(settings.get("seed", 42)),
        "steps": str(settings.get("steps", 8)),
        "scale": str(settings.get("scale", 1.0)),
    }
    with tempfile.TemporaryDirectory(prefix="krea_ui_") as folder:
        script = Path(folder) / "krea_dialog.swift"
        script.write_text(SWIFT_DIALOG, encoding="utf-8")
        result = subprocess.run(
            ["/usr/bin/swift", str(script)],
            input=json.dumps(payload, ensure_ascii=False),
            text=True, capture_output=True, check=False,
        )
    if result.returncode == 2:
        return None
    if result.returncode != 0:
        raise RuntimeError("設定画面を開けません:\n" + result.stderr.strip())
    try:
        selection = json.loads(result.stdout)
        japanese = selection["prompt"].strip()
        seed = int(selection["seed"].strip())
        steps = int(selection["steps"].strip())
        scale = float(selection["scale"].strip())
        index = int(selection["index"])
        if seed < 0 or not 1 <= steps <= 100 or not 0 <= scale <= 2 or not 0 <= index <= len(paths):
            raise ValueError("範囲外")
        if not japanese:
            raise ValueError("日本語プロンプトが空です")
    except (ValueError, KeyError, TypeError) as error:
        raise RuntimeError(f"入力内容を確認してください: {error}") from error
    path = paths[index - 1] if index else None
    SETTINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
    SETTINGS_PATH.write_text(
        json.dumps({"prompt": japanese, "seed": seed, "steps": steps, "scale": scale,
                    "lora": str(path) if path else ""},
                   ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    PROMPT_HISTORY.write_text(japanese, encoding="utf-8")
    return japanese, path, scale, seed, steps


def next_output_path():
    """Find an unused sequential image filename."""
    i = 1
    while (OUTPUT_DIR / f"krea_{i:04d}.png").exists():
        i += 1
    return OUTPUT_DIR / f"krea_{i:04d}.png"


def main() -> int:
    try:
        selection = choose_settings(" ".join(sys.argv[1:]).strip())
    except (OSError, RuntimeError) as error:
        print(error, file=sys.stderr)
        return 1
    if selection is None:
        print("キャンセルしました。")
        return 0
    japanese, lora_path, lora_scale, seed, steps = selection
    try:
        english = translate(japanese)
    except (urllib.error.URLError, TimeoutError, RuntimeError) as error:
        print(f"Ollamaとの通信に失敗しました: {error}", file=sys.stderr)
        return 1
    print(f"\n英語プロンプト:\n{english}\n", flush=True)
    env = os.environ.copy()
    env["HF_HOME"] = HF_HOME
    before = {p: p.stat().st_mtime_ns for p in OUTPUT_DIR.glob("*.png")}
    print("MFLUXで画像生成します。", flush=True)
    command = [
        "mflux-generate-krea2", "--prompt", english,
        "--width", "1024", "--height", "1024",
        "--seed", str(seed), "--steps", str(steps), "-q", "8",
    ]
    if lora_path is not None:
        command.extend(["--lora-paths", str(lora_path), "--lora-scales", str(lora_scale)])
        print(f"LoRA: {lora_path.name} (強度 {lora_scale})", flush=True)
    try:
        subprocess.run(command, env=env, cwd=OUTPUT_DIR, check=True)
    except FileNotFoundError:
        print("mflux-generate-krea2 が見つかりません。", file=sys.stderr)
        return 1
    except subprocess.CalledProcessError as error:
        print(f"画像生成に失敗しました（終了コード {error.returncode}）。", file=sys.stderr)
        return error.returncode or 1
    changed = [p for p in OUTPUT_DIR.glob("*.png")
               if p not in before or p.stat().st_mtime_ns != before[p]]
    if changed:
        output = max(changed, key=lambda p: p.stat().st_mtime_ns)
        destination = next_output_path()
        output.rename(destination)
        print(f"生成画像: {destination}")
        subprocess.run(["open", str(destination)], check=False)
    else:
        print("生成画像が見つかりません。MFLUXの出力先を確認してください。", file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())