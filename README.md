# Yukie Head Pet

这是一个以虚拟主播雪绘 Yukie 形象为参考的 Codex 自定义桌宠项目，包含 9 种应用状态动画、互动展示页和 QQ 表情包导出。

## 本次升级

- 修复展示页中文乱码与损坏标签。
- 新增可拖动、单击问候、双击跳跃和键盘移动。
- 新增自由巡游、陪伴工作、等待输入、动作选择与场景切换。
- 新增一键同步脚本，便于通过 Codex 宠物界面的“更新”按钮加载最新版本。
- 继续复用已通过透明度与图集尺寸校验的 9 状态雪绘动画素材。

## 使用方式

更新 Codex 桌宠：

```powershell
powershell -ExecutionPolicy Bypass -File outputs\update-yukie-head-pet.ps1
```

脚本完成后，回到 Codex 宠物界面点击“更新”。

启动互动展示页：

```powershell
powershell -ExecutionPolicy Bypass -File outputs\start-yukie-head-demo.ps1
```

## 项目内容

- `outputs/yukie-head/`：Codex v2 宠物包（`pet.json` 与 `spritesheet.webp`）。
- `outputs/yukie-head-v2-codex-pet.zip`：v2 可分享宠物包。
- `outputs/yukie-head-demo.html`：互动桌宠展示页。
- `outputs/yukie-head-codex-pet.zip`：可分享的 Codex 宠物包。
- `outputs/yukie-head-stickers/`：9 种状态导出的 GIF、PNG 与 WebP 表情。
- `tools/export_sticker_pack.py`：重新导出表情包的工具。

## 动画状态

待机、向右移动、向左移动、打招呼、跳跃、失败、等待输入、处理中、检查结果。

## 素材与校验

v2 图集为 1536×2288 WebP，每格 192×208，采用 8×11 布局并包含 16 个视线方向，透明背景；修复版 v2 专用校验无错误或警告。
