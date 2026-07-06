from __future__ import annotations

import argparse
import json
import math
import shutil
import zipfile
from pathlib import Path

from PIL import Image


CELL_W = 192
CELL_H = 208
CANVAS = 512
PADDING = 34
QQ_CANVAS = 240
QQ_PADDING = 14
FRAME_DURATION_MS = 120


STATE_LABELS = {
    "idle": "待机",
    "running-right": "向右跑",
    "running-left": "向左跑",
    "waving": "挥手",
    "jumping": "跳跃",
    "failed": "失败",
    "waiting": "等待",
    "running": "工作中",
    "review": "审阅",
}


def alpha_bbox(image: Image.Image) -> tuple[int, int, int, int] | None:
    return image.getchannel("A").getbbox()


def crop_used_cells(spritesheet: Image.Image, validation: dict) -> dict[str, list[Image.Image]]:
    states: dict[str, list[tuple[int, Image.Image]]] = {}
    for cell in validation["cells"]:
        if not cell.get("used"):
            continue
        state = cell["state"]
        row = int(cell["row"])
        col = int(cell["column"])
        crop = spritesheet.crop((col * CELL_W, row * CELL_H, (col + 1) * CELL_W, (row + 1) * CELL_H))
        if alpha_bbox(crop):
            states.setdefault(state, []).append((col, crop))
    return {state: [frame for _, frame in sorted(frames)] for state, frames in states.items()}


def global_content_box(frames_by_state: dict[str, list[Image.Image]]) -> tuple[int, int, int, int]:
    min_x = CELL_W
    min_y = CELL_H
    max_x = 0
    max_y = 0
    for frames in frames_by_state.values():
        for frame in frames:
            box = alpha_bbox(frame)
            if not box:
                continue
            min_x = min(min_x, box[0])
            min_y = min(min_y, box[1])
            max_x = max(max_x, box[2])
            max_y = max(max_y, box[3])
    if max_x <= min_x or max_y <= min_y:
        raise RuntimeError("No visible pixels found in spritesheet.")
    return min_x, min_y, max_x, max_y


def sticker_frame(frame: Image.Image, content_box: tuple[int, int, int, int]) -> Image.Image:
    content_w = content_box[2] - content_box[0]
    content_h = content_box[3] - content_box[1]
    scale = min((CANVAS - PADDING * 2) / content_w, (CANVAS - PADDING * 2) / content_h)
    scaled_cell_w = max(1, int(round(CELL_W * scale)))
    scaled_cell_h = max(1, int(round(CELL_H * scale)))
    scaled = frame.resize((scaled_cell_w, scaled_cell_h), Image.Resampling.LANCZOS)
    canvas = Image.new("RGBA", (CANVAS, CANVAS), (0, 0, 0, 0))
    x = (CANVAS - scaled_cell_w) // 2
    y = (CANVAS - scaled_cell_h) // 2
    canvas.alpha_composite(scaled, (x, y))
    return canvas


def fitted_frame(
    frame: Image.Image,
    content_box: tuple[int, int, int, int],
    canvas_size: int,
    padding: int,
) -> Image.Image:
    content_w = content_box[2] - content_box[0]
    content_h = content_box[3] - content_box[1]
    scale = min((canvas_size - padding * 2) / content_w, (canvas_size - padding * 2) / content_h)
    scaled_cell_w = max(1, int(round(CELL_W * scale)))
    scaled_cell_h = max(1, int(round(CELL_H * scale)))
    scaled = frame.resize((scaled_cell_w, scaled_cell_h), Image.Resampling.LANCZOS)
    canvas = Image.new("RGBA", (canvas_size, canvas_size), (0, 0, 0, 0))
    x = (canvas_size - scaled_cell_w) // 2
    y = (canvas_size - scaled_cell_h) // 2
    canvas.alpha_composite(scaled, (x, y))
    return canvas


def save_animation(frames: list[Image.Image], gif_path: Path, webp_path: Path) -> None:
    first, rest = frames[0], frames[1:]
    first.save(
        gif_path,
        save_all=True,
        append_images=rest,
        duration=FRAME_DURATION_MS,
        loop=0,
        disposal=2,
        transparency=0,
    )
    first.save(
        webp_path,
        save_all=True,
        append_images=rest,
        duration=FRAME_DURATION_MS,
        loop=0,
        lossless=False,
        quality=86,
        method=0,
    )


def save_gif_only(frames: list[Image.Image], gif_path: Path) -> None:
    first, rest = frames[0], frames[1:]
    first.save(
        gif_path,
        save_all=True,
        append_images=rest,
        duration=FRAME_DURATION_MS,
        loop=0,
        disposal=2,
        transparency=0,
        optimize=True,
    )


def write_index(output_dir: Path, manifest: dict) -> None:
    cards = []
    for item in manifest["stickers"]:
        cards.append(
            f"""
      <article class="card">
        <img src="{item['gif']}" alt="{item['state']}">
        <h2>{item['label']} <code>{item['state']}</code></h2>
        <p>{item['frames']} frames · PNG/GIF/WEBP</p>
      </article>"""
        )
    html = f"""<!doctype html>
<html lang="zh-CN">
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{manifest['display_name']} 表情包</title>
<style>
  body {{ margin: 0; font-family: system-ui, sans-serif; background: #111; color: #f7f7f7; }}
  main {{ max-width: 1180px; margin: 0 auto; padding: 28px; }}
  h1 {{ margin: 0 0 8px; }}
  .grid {{ display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 18px; }}
  .card {{ background: #1d1d1d; border: 1px solid #333; border-radius: 18px; padding: 16px; }}
  img {{ width: 100%; image-rendering: auto; background: repeating-conic-gradient(#252525 0 25%, #202020 0 50%) 50% / 24px 24px; border-radius: 14px; }}
  h2 {{ font-size: 16px; margin: 12px 0 4px; }}
  p {{ color: #bdbdbd; margin: 0; }}
  code {{ color: #9ad; font-size: 12px; }}
</style>
<main>
  <h1>{manifest['display_name']} 表情包</h1>
  <p>统一 512×512 透明画布，从 9 形态动画图集导出。</p>
  <section class="grid">{''.join(cards)}
  </section>
</main>
</html>
"""
    (output_dir / "index.html").write_text(html, encoding="utf-8")


def write_preview_sheet(output_dir: Path, stickers: list[dict]) -> None:
    tile = 220
    gap = 22
    margin = 28
    sheet_w = margin * 2 + tile * 3 + gap * 2
    sheet_h = margin * 2 + tile * 3 + gap * 2
    sheet = Image.new("RGBA", (sheet_w, sheet_h), (24, 24, 24, 255))
    for idx, item in enumerate(stickers):
        row, col = divmod(idx, 3)
        x = margin + col * (tile + gap)
        y = margin + row * (tile + gap)
        frame = Image.open(output_dir / item["png"]).convert("RGBA").resize((tile, tile), Image.Resampling.LANCZOS)
        sheet.alpha_composite(frame, (x, y))
    sheet.save(output_dir / "preview-sheet.png")


def write_qq_readme(output_dir: Path) -> None:
    text = """# QQ 表情包导入说明

推荐导入 `qq-gif` 目录里的 9 个 `.gif` 文件。

文件命名已经按顺序和中文状态整理：

1. 01-待机-idle.gif
2. 02-向右跑-running-right.gif
3. 03-向左跑-running-left.gif
4. 04-挥手-waving.gif
5. 05-跳跃-jumping.gif
6. 06-失败-failed.gif
7. 07-等待-waiting.gif
8. 08-工作中-running.gif
9. 09-审阅-review.gif

如果 QQ 当前客户端不接受动态 GIF，可改导入 `qq-png` 目录里的静态 PNG 版本。
"""
    (output_dir / "README-QQ.md").write_text(text, encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--spritesheet", required=True, type=Path)
    parser.add_argument("--validation", required=True, type=Path)
    parser.add_argument("--pet-json", required=True, type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    args = parser.parse_args()

    output_dir = args.output_dir
    if output_dir.exists():
        shutil.rmtree(output_dir)
    (output_dir / "png").mkdir(parents=True)
    (output_dir / "gif").mkdir(parents=True)
    (output_dir / "webp").mkdir(parents=True)
    (output_dir / "qq-gif").mkdir(parents=True)
    (output_dir / "qq-png").mkdir(parents=True)

    spritesheet = Image.open(args.spritesheet).convert("RGBA")
    validation = json.loads(args.validation.read_text(encoding="utf-8"))
    pet = json.loads(args.pet_json.read_text(encoding="utf-8-sig"))

    frames_by_state = crop_used_cells(spritesheet, validation)
    box = global_content_box(frames_by_state)

    stickers = []
    for index, state in enumerate(STATE_LABELS, start=1):
        if state not in frames_by_state:
            continue
        frames = [sticker_frame(frame, box) for frame in frames_by_state[state]]
        png_name = f"{state}.png"
        gif_name = f"{state}.gif"
        webp_name = f"{state}.webp"
        frames[0].save(output_dir / "png" / png_name)
        save_animation(frames, output_dir / "gif" / gif_name, output_dir / "webp" / webp_name)
        qq_frames = [fitted_frame(frame, box, QQ_CANVAS, QQ_PADDING) for frame in frames_by_state[state]]
        qq_name = f"{index:02d}-{STATE_LABELS[state]}-{state}"
        qq_frames[0].save(output_dir / "qq-png" / f"{qq_name}.png")
        save_gif_only(qq_frames, output_dir / "qq-gif" / f"{qq_name}.gif")
        stickers.append(
            {
                "state": state,
                "label": STATE_LABELS[state],
                "frames": len(frames),
                "png": f"png/{png_name}",
                "gif": f"gif/{gif_name}",
                "webp": f"webp/{webp_name}",
            }
        )

    manifest = {
        "id": pet.get("id", "pet"),
        "display_name": pet.get("displayName", pet.get("id", "Pet")),
        "canvas": [CANVAS, CANVAS],
        "padding": PADDING,
        "duration_ms": FRAME_DURATION_MS,
        "source_spritesheet": str(args.spritesheet),
        "stickers": stickers,
    }
    (output_dir / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    write_preview_sheet(output_dir, stickers)
    write_qq_readme(output_dir)
    write_index(output_dir, manifest)

    zip_path = output_dir.with_suffix(".zip")
    if zip_path.exists():
        zip_path.unlink()
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for path in sorted(output_dir.rglob("*")):
            if path.is_file():
                zf.write(path, path.relative_to(output_dir.parent))
    print(f"stickers={len(stickers)}")
    print(f"output_dir={output_dir}")
    print(f"zip={zip_path}")


if __name__ == "__main__":
    main()
