---
name: mj-mannequin-composite
description: "用 Midjourney 素体人偶法做 Cosplay/人像合成后期：让 MJ 画出带灰色人偶的场景，一次得到背景、分镜和布光图；支持 mjweb/OpenAI 兼容接口批量出图、翻车纠错、故事线排布、自动擦除人偶与真人合成验收。当用户提到 MJ 出背景、素体人偶、人偶工作流、空场景/干净背景板、擦人偶、cos 合成、拍摄预演、分镜补镜头、布光参考，或遇到白模发灰、老虎像猫、人偶穿衣服等 MJ 翻车时使用；用户要用 mjweb 批量跑 Midjourney 后期时也使用。"
---

# MJ 素体人偶合成后期

## 这个 Skill 解决什么

棚拍人像/Cos 最难的是背景：想要的场景没地方拍，动物更请不来。

直接让 MJ 出“没有人的空场景”会翻车——画面里没有尺度参照，MJ 不知道东西该多大、镜头该多高，后期把人放进去就是“贴上去的”。

解法：**让 MJ 画一个灰色素体人偶站在场景里**，摆好动作、和动物或道具互动。同一张图三用：

1. **背景**：后期擦掉人偶，就是干净空景。
2. **分镜**：模特照人偶的姿势、朝向、画面占比去摆。
3. **布光图**：人偶哪里亮、哪里暗、偏什么颜色，棚里照着打。

人偶不是多余的东西，它是一把尺子。

## 开始前定 5 件事

| 事项 | 为什么要定 | 缺省怎么办 |
|---|---|---|
| 角色与配色 | 配色错，整组都会跑偏 | 让用户提供立绘；没有就按文字设定取 2–3 个主色 |
| 互动对象 | 动物/道具决定构图与接触点 | 没有就做人景互动（伞、扇、茶具） |
| 场景与光线 | 光线就是故事的时间轴 | 按“上午→正午→黄昏→夜”选一个起点 |
| 画幅 `--ar` | 决定后期裁切与排版 | 人像 4:5，叙事 3:2，手机 9:16 |
| 棚拍条件 | 决定先拍还是先出图 | 未知就按白棚柔光给方案 |

信息不全时用保守默认并在交付里说明，不要反复追问。

## 六步流水线

0. **定角色和配色** → 读 [`references/prep-and-prompt.md`](references/prep-and-prompt.md) 前半
1. **写提示词** → 同一文件的提示词骨架、标准句、`--no`、参数与两条完整示例
2. **批量出图与纠错** → 用本文「自动化」节跑图；出问题查 [`references/failure-table.md`](references/failure-table.md)
3. **排故事线与补镜头** → [`references/storyline.md`](references/storyline.md)
4. **照着图棚拍** → [`references/studio-and-composite.md`](references/studio-and-composite.md) 前半
5. **擦人偶、换真人合成** → 同文件后半 + 脚本 `erase`

## 提示词铁律

写任何一条 prompt 前过一遍；脚本 `lint` 会自动检查其中大部分。

1. **顺序**：焦段 + 景别 + 机位 → 人偶 + 动作 → 动物/互动 → 环境 → 光线 → 颜色 → 画风 → 参数。越靠前 MJ 越照顾。
2. **人偶标准句**（固定，不要改写核心词）：
   `a slim adult female faceless matte grey artist mannequin with smooth jointed limbs`
   - 用灰不用白：白人偶贴着白老虎，后期抠图边缘会糊在一起；灰色还是天然灰卡，光位和色温一眼可见。
   - 要优雅或性感姿态，必须写成年体型：`slim adult female`、`tall slim adult female`。
3. **动物只写名字**：`a white tiger`。不写 `giant` / `huge` / 倍数。太小就写 `full grown adult white tiger with a muscular body` 并放到前面。
4. **每个物件写具体颜色**，再加一句：
   `only the mannequin is matte grey, the rest of the scene in full rich color`
   否则整张图会变成灰白的“白模”。
5. **`--no` 标准配置**：
   `--no real human, clothing, hair, text, watermark, monochrome, grayscale, clay render, white model, desaturated`
   按场景追加：江南加 `palace`，怕猫加 `cat, kitten`，全身加 `cropped hands, cropped feet`。
6. **不写角色名、游戏名**：会把角色直接画出来，画风也会被拉向游戏动漫。
7. **姿态词**：`graceful S-curve pose`、`alluring pose`、`hip cocked`、`slight arch in her back`。不写 `sexy`，容易触发审核。
8. **一次只改一个变量**：景别、焦段、颜色一起改，就不知道是哪一处起了作用。

## 自动化：mjweb 批量出图

脚本 `scripts/mj_autopost.py` 走 mjweb 原生异步接口（`/imagine` + `/task/{id}`），一次任务固定出 4 张图。

```bash
export MJ_API_BASE="https://<你的-mjweb-域名>/mjapi"   # 也可放 ~/.config/mjweb/base
export MJ_API_KEY="<你的 mjweb Key>"                    # 也可放 ~/.config/mjweb/api_key
python3 scripts/mj_autopost.py health
python3 scripts/mj_autopost.py lint  --brief scripts/example-brief.json
python3 scripts/mj_autopost.py gen   --brief scripts/example-brief.json --shot 01-rain-alley --dry-run
python3 scripts/mj_autopost.py batch --brief scripts/example-brief.json --out runs/white-tiger
python3 scripts/mj_autopost.py erase --image runs/white-tiger/01-rain-alley/01.png --out runs/white-tiger/clean
python3 scripts/mj_autopost.py sheet --dir runs/white-tiger --out runs/white-tiger/sheet.jpg
```

- `lint` 只抓已知翻车，**不替代看图**；每张图都要目检。
- `batch` 先全部提交再轮询；已成功的镜头自动跳过，`--force` 重跑。
- 一次任务 4 张，Basic 约 200 张/月；跑批前先确认额度。
- 服务端可能对提示词做“整理”。要严格按骨架执行：在 mjweb 后台关掉该 Key 的提示词整理，或用任务 meta 里的 `plan.normalized_prompt` 核对实际提交词。
- 创建任务成功不等于出图成功：必须轮询到 `SUCCESS`；`FAILURE` 读 `error`；额度不足先查 Key 的 quota。
- 不把 API Key、Cookie 写进 brief、README、日志或提交到 Git。

## 挑图与验收

单张看六点：人偶比例像成年女性、景别符合意图、手脚完整、透视与机位一致、画面不发灰、人偶没穿衣服/长头发。

组图看三件事：按“场景 + 光线”分组；按光线时间轴排序；对不上的组给它一个叙事理由（雪景 = 午睡时做的梦）。

交付时给：联系表 `sheet.jpg`、`shots.json`（每镜头状态与文件路径）、clean plates、合成验收表。

## 擦人偶（自动化的边界）

`erase` 走 V8.2 垫图编辑（reference edit）：

- 提示词**只描述人偶消失后的空场景**。可以提 `mannequin`，但不要写 `person`、`girl`、`human`——容易把人招回来。
- 一次出 4 张，挑最干净的一张；地上的影子、水面的倒影必须一起消失。
- 接触点（人搭在虎背上）要补毛发压痕和投影，否则人是浮着的。
- reference edit 会整图重绘：复杂遮挡、镜面倒影、手部交叠容易留痕或改构图。这种情况转 MJ 网页 Editor 的擦除（遮罩）或 Photoshop 生成式填充，不要硬吹自动化成功。
- 擦完逐项对齐原图：构图、纹理、光线方向、色温、噪点；检查残肢、灰影、重复物件。

## 合成真人

机位高度和焦段跟图一致；光位照人偶打；悬浮/坐/躺要有透明亚克力凳或白箱撑着；和动物接触的位置垫到同高；有镜子的画面补拍背面和侧面。后期调色往背景靠，接触点补毛发压痕与投影。完整验收清单在 [`references/studio-and-composite.md`](references/studio-and-composite.md)。

## 输出与边界

- 交付要具体：镜头 id、文件路径、通过/待重跑、用了多少额度、下一步。
- 不虚构原作设定；自己发挥的元素（比如给角色加一面镜子）要标注清楚。
- 不把角色名写进 MJ 提示词；不把未授权的真人素材或他人拍摄图用于合成；AI 生成图按发布平台要求标注。
