# MJ 素体人偶合成后期

用 Midjourney 的**素体人偶法**做 Cosplay / 人像合成后期：先让 MJ 画一个灰色素体人偶站在场景里，一张图同时得到**背景、分镜和布光图**；再用脚本批量出图、排故事线、擦除人偶得到干净背景板，最后照着图棚拍并合成真人。

这是一个 ZCode / Claude 兼容的 Skill，也是一个可直接在终端跑的 mjweb 自动化脚本。

## 为什么用人偶

直接让 MJ 出“没有人的空场景”会翻车：画面里没有尺度参照，MJ 不知道东西该多大、镜头该多高，后期把人放进去就是“贴上去的”。

让 MJ 画一个**灰色素体人偶**站在场景里，摆好动作、和动物或道具互动，同一张图三用：

- **背景**：后期擦掉人偶，就是干净空景
- **分镜**：模特照人偶的姿势、朝向、画面占比摆
- **布光图**：人偶哪里亮、哪里暗、偏什么色，棚里照着打

人偶是一把尺子，不是多余的东西。

## 包含什么

- **SKILL.md**：完整六步流水线、提示词铁律、擦除与合成边界
- **references/**：角色配色与提示词骨架、翻车对照表、故事线排布、棚拍与合成验收
- **scripts/mj_autopost.py**：走 mjweb 原生异步 API 的自动化脚本
  - `lint`：检查提示词是否踩了已知翻车规则（不耗额度）
  - `gen`：单镜头出图
  - `batch`：批量提交 + 轮询 + 下载，已完成的镜头自动跳过
  - `erase`：V8.2 垫图编辑擦除人偶，生成干净背景板
  - `sheet`：生成联系表，方便挑图
- **scripts/example-brief.json**：白虎雨巷 / 庭院 / 漏窗 / 雪地 + 维琳娜茶会五个镜头示例

## 安装

把整个目录放到 ZCode 的技能目录：

```bash
cp -R mj-mannequin-composite ~/.agents/skills/
```

ZCode 会自动发现 `~/.agents/skills/<name>/SKILL.md`。Claude Code 用户可放到 `~/.claude/skills/` 或项目的 `.claude/skills/`。

## 配置 mjweb

脚本默认连接 `http://127.0.0.1:8087`（mjweb 的本地端口）。远程部署用环境变量或本地配置文件：

```bash
export MJ_API_BASE="https://your-mjweb-host/mjapi"
export MJ_API_KEY="your-key"
```

也可以写文件（权限建议 600，且不要提交到 Git）：

```bash
mkdir -p ~/.config/mjweb
printf '%s\n' 'https://your-mjweb-host/mjapi' > ~/.config/mjweb/base
printf '%s\n' 'your-key' > ~/.config/mjweb/api_key
chmod 600 ~/.config/mjweb/api_key
```

- Key 在 mjweb 后台创建；owner 主 Key 在服务器 `/home/admin/mjweb/api_key`。
- 如果 Python 报 `CERTIFICATE_VERIFY_FAILED`：先 `pip install certifi`；自建服务证书链不完整时可加 `--insecure`（仅限你自己的服务器）。
- 一次 MJ 任务固定出 4 张图；Basic 计划约 200 张/月，跑批前先确认额度。
- Basic 不支持 private 模式，示例 brief 里 `private: false`。

## 快速开始

```bash
cd ~/.agents/skills/mj-mannequin-composite

# 1. 检查服务和 Key
python3 scripts/mj_autopost.py health

# 2. 只检查提示词，不花额度
python3 scripts/mj_autopost.py lint --brief scripts/example-brief.json

# 3. 看单镜头最终提示词，不提交
python3 scripts/mj_autopost.py gen --brief scripts/example-brief.json --shot 01-rain-alley --dry-run

# 4. 批量出图
python3 scripts/mj_autopost.py batch --brief scripts/example-brief.json --out runs/white-tiger

# 5. 挑一张，擦掉人偶
python3 scripts/mj_autopost.py erase --image runs/white-tiger/01-rain-alley/01.png

# 6. 生成联系表
python3 scripts/mj_autopost.py sheet --dir runs/white-tiger
```

只跑部分镜头：

```bash
python3 scripts/mj_autopost.py batch --brief scripts/example-brief.json \
  --only 01-rain-alley,02-courtyard-noon --out runs/white-tiger
```

强制重跑已完成的镜头：

```bash
python3 scripts/mj_autopost.py batch --brief scripts/example-brief.json --force
```

## brief 格式

```json
{
  "project": "white-tiger",
  "output": "runs/white-tiger",
  "defaults": {
    "version": "8.2",
    "mode": "fast",
    "private": false,
    "style": "photorealistic, cinematic",
    "negative": ["real human", "clothing", "hair", "text", "watermark",
                  "monochrome", "grayscale", "clay render", "white model", "desaturated"],
    "forbidden_terms": ["角色名", "游戏名"]
  },
  "shots": [
    {
      "id": "01-rain-alley",
      "aspect": "3:2",
      "focal": "85mm",
      "camera": "eye-level",
      "framing": "full body shot",
      "composition": "centered composition, space on both sides",
      "mannequin": {
        "size": "slim adult female",
        "pose": "standing beside the tiger's shoulder, holding an oil-paper umbrella, hip cocked, graceful S-curve pose"
      },
      "animal": "a full grown adult white tiger with a muscular body",
      "interaction": "the two in the center of the frame, her entire body including hands and feet inside the frame",
      "scene": "a narrow Jiangnan stone alley, white walls and black tiles, wet flagstones",
      "light": "soft overcast rain light",
      "color": "white plaster walls, black tile roofs, dark wet stone",
      "params": "--style raw --s 100",
      "negative_extra": ["palace", "cat", "kitten"],
      "tags": ["雨巷", "上午"]
    }
  ]
}
```

字段说明：

| 字段 | 说明 |
|---|---|
| `id` | 镜头 id，同时作为输出子目录名 |
| `aspect` | 画幅，如 `3:2`、`4:5`、`9:16`；脚本会自动补 `--ar` |
| `focal` / `camera` / `framing` / `composition` | 焦段、机位、景别、构图，按骨架顺序拼 |
| `mannequin` | `true` / 姿势字符串 / `{size, pose, extra}`；`false` 表示不画人偶 |
| `animal` / `interaction` / `scene` / `light` / `color` | 动物、互动、环境、光线、颜色 |
| `params` | MJ 参数，如 `--style raw --s 100` |
| `negative` / `negative_extra` | `--no` 列表；`negative` 覆盖默认，`negative_extra` 追加 |
| `prompt` | 直接给完整提示词，跳过骨架拼装（仍会 lint） |
| `version` / `mode` / `private` | 可覆盖 defaults |

## 输出结构

```text
runs/white-tiger/
├── 01-rain-alley/
│   ├── prompt.txt          # 实际拼出的提示词
│   ├── lint.json           # 错误/提醒
│   ├── task.json           # task_id、提交时间、实际提交词
│   ├── meta.json           # 状态、图片路径、MJ 任务完整返回
│   └── 01.png ... 04.png   # 一次任务固定 4 张
├── clean/
│   ├── clean-01.png ... 04.png
│   └── erase-meta.json
└── sheet.jpg
```

## 自动化的边界

- `erase` 走的是 **V8.2 垫图编辑（reference edit）**，不是遮罩 inpainting。它会整图重绘，复杂遮挡、镜面倒影、手部交叠容易留痕或改构图。
- 脚本返回 `SUCCESS` 只代表 MJ 出图成功，**不代表擦干净了**。必须逐张目检：残肢、灰影、倒影、构图漂移、接触点。
- 擦不干净就转 MJ 网页 Editor 的遮罩擦除或 Photoshop 生成式填充。这条流程不承诺“全自动擦除”。
- 擦除提示词只描述空场景，不要写 `person` / `girl` / `human`；脚本会拦截这些词。
- 服务端可能开启提示词整理，实际提交词看 `task.json` 或任务 meta 的 `plan.normalized_prompt`。

## 来源

流程来自“白虎娘”和“维琳娜茶会”两组实战：素体人偶、灰色不用白色、动物不写大小、颜色锚点、`--no` 标准配置、翻车对照、故事线补镜头、棚拍与合成验收。

## 免责声明

- 仅用于本人拍摄或已获授权的素材；不要用未授权的真人照片、他人拍摄图做合成。
- 角色二创遵守原作方的二创指引；AI 生成图按发布平台要求标注。
- 不要把 API Key、Cookie、服务器凭据提交到仓库或写进 brief。

## License

MIT
