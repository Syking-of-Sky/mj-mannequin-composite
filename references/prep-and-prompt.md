# 定角色、配色与提示词

## 一、定角色和配色

### 1. 查角色资料，把设定翻译成画面元素

身份、爱好、属性、武器、经典台词，都能变成画面里的东西。以维琳娜为例：

- 爱办茶会 → 漂浮的茶具、点心架
- 风属性 → 被气旋卷起来的茶叶、桌布、裙摆
- 武器是白色大折扇 → 人偶手里拿扇子

**分清“设定里有的”和“自己发挥的”。** 维琳娜的茶会、风、白扇都有出处；镜子是从“双面魔女”联想出来的，原设定里没有。自己发挥可以，但心里要有数，别人问起来要说得清楚，交付时也要标注。

### 2. 看立绘取配色，别凭印象

一开始以为维琳娜是“白、银、淡紫”，下载立绘一看，主色其实是**深钴蓝**。凭印象写，整组配色都会跑偏。

做法：打开立绘，取 2–3 个面积最大的颜色，记下色相和明度；不要用“淡雅”“高级”这类词代替具体颜色。

### 3. 背景配色要避开衣服的主色

人穿钴蓝衣服，背景也大面积用钴蓝，人就融进背景里跳不出来。

正确做法：

- 背景用对比色或中性色，比如暖象牙色 + 香槟金；
- 角色主色只在小道具上点一点，比如青花瓷茶杯；
- 如果角色主色必须出现在背景里，降低它的饱和度和面积，别让它成为第二主体。

### 4. 提示词里不写角色名、游戏名

写了 MJ 可能直接把角色画出来，画风也会被拉向游戏动漫风。用外观描述代替名字：

- 不写“维琳娜” → 写 `a tall slim adult female` + 发型、服装颜色、扇子
- 不写“白虎娘” → 写 `a white tiger` + 场景与互动

## 二、提示词骨架

按这个顺序往下写，越靠前的东西 MJ 越照顾：

```text
焦段 + 机位 + 景别 + 构图 → 人偶 + 动作 → 动物 / 互动 → 环境 → 光线 → 颜色 → 画风 → 参数
```

一条 prompt 只承担一个镜头。不要把三个场景塞进一条 prompt，MJ 会平均分配注意力，每个都画不好。

### 人偶标准句（直接复制）

```text
a slim adult female faceless matte grey artist mannequin with smooth jointed limbs
```

高挑版本：

```text
a tall slim adult female faceless matte grey artist mannequin with smooth jointed limbs
```

- **为什么用灰色不用白色**：白人偶贴着白老虎，后期抠图边缘会糊在一起。灰色人偶相当于一张灰卡，光线的方向和颜色看得最清楚。
- **体型写成年**：要做优雅、性感的姿态，人偶必须写成年体型（`slim adult female`、`tall slim adult female`）。写 `girl` 会得到幼态比例，后期真人对不上。
- **性感姿态的写法**：用 `graceful S-curve pose`、`alluring pose`、`hip cocked`、`slight arch in her back`。**别写 `sexy`**，MJ 审核容易直接拦下来。
- **手要有事做**：拿伞、扶虎背、提裙摆、端茶杯。手空着容易画成僵硬下垂。

### 动物只写名字，不写大小

只写 `a white tiger` 就够了。写 `giant`、`huge`，MJ 会画成巨兽；写“1.5 倍大”，MJ 根本理解不了倍数。不写大小，它会按正常老虎画。

如果老虎还是太小，不要加“大”，改成：

```text
a full grown adult white tiger with a muscular body
```

并把它放到 prompt 更靠前的位置，再加 `centered composition, space on both sides`。

### 每样东西都写清楚颜色

人偶是灰的，MJ 很容易把整个场景都画成灰白的“白模”。解决办法：

- 每个物件都写具体颜色：`cobalt blue and white porcelain teacup with a gold rim`
- 加这句：`only the mannequin is matte grey, the rest of the scene in full rich color`

### `--no` 标准配置

```text
--no real human, clothing, hair, text, watermark, monochrome, grayscale, clay render, white model, desaturated
```

- `real human`：防止人偶被画成真人
- `clothing, hair`：防止人偶自己穿上衣服、长出头发
- 后面五个：防止画面发灰、变成白模

按场景追加：

- 江南 / 中式场景：`palace`
- 怕出猫：`cat, kitten`
- 要拍全身：`cropped hands, cropped feet`
- 不想出现芭蕉/棕榈：`banana tree, palm tree`

### 参数怎么选

| 用途 | 参数 |
|---|---|
| 刷灵感，多看几种构图 | `--c 25 --s 200` |
| 定稿精修，要听话 | `--style raw --s 100`（不加 `--c`） |
| 要颜色更饱满 | 去掉 `--style raw`，`--s 200` |

画幅：人像 4:5，叙事/横构图 3:2，手机竖屏 9:16。画幅在 brief 的 `aspect` 字段里给，不要和 prompt 里的 `--ar` 重复写。

### 全身与裁切

要拍满全身又怕裁掉手脚：

- 动作收紧：并膝、抱膝、蜷身，别让四肢伸到画面外；
- 加 `her entire body including hands and feet inside the frame`；
- 加 `--no cropped hands, cropped feet`；
- 景别不要太松，`full body shot` 比 `wide shot` 更稳。

## 三、两条完整示例

### 白虎 · 雨巷居中（解决“老虎像猫”）

```text
85mm, eye-level full body shot, centered composition, a full grown adult white tiger with a muscular body standing on all four paws in the middle of a narrow Jiangnan stone alley, a slim adult female faceless matte grey artist mannequin with smooth jointed limbs standing beside its shoulder holding an oil-paper umbrella over herself, hip cocked to one side, one hand resting on the tiger's back, glancing back over her shoulder, graceful S-curve pose, both in the center of the frame with space on both sides, white walls and black tiles on either side, wet flagstones reflecting the light, soft overcast rain light, photorealistic, cinematic --ar 3:2 --style raw --s 100 --no real human, palace, cat, kitten, text, watermark
```

### 维琳娜 · 茶会主视觉（解决“整张图发灰”）

```text
85mm, eye-level, centered composition, a tall slim adult female faceless matte grey artist mannequin with smooth jointed limbs sitting elegantly on a floating ivory and gold Rococo armchair, holding a cobalt blue and white porcelain teacup with a gold rim, a large white folding fan with gold ribs and blue edges in her other hand, a floating teapot, saucers and a tiered gold cake stand drifting around her, a spiral of amber tea swirling in the wind, warm ivory European hall with champagne gold moldings and tall arched windows, soft warm daylight, only the mannequin is matte grey, the rest of the scene in full rich color, photorealistic, cinematic --ar 4:5 --s 200 --no real human, clothing, hair, anime, monochrome, grayscale, clay render, white model, desaturated, text, watermark
```

注意第二条没有 `--style raw`，因为要颜色更饱满；同时显式加了 `anime` 到 `--no`，防止茶会场景被拉成二次元。

## 四、写 prompt 前的自检

- [ ] 顺序是“焦段→机位→景别→构图→人偶→动物/互动→环境→光线→颜色→画风→参数”吗？
- [ ] 人偶句是标准句吗？体型是成年吗？
- [ ] 动物只写了物种名，没有大小词吗？
- [ ] 每个物件都有具体颜色吗？有“只有人偶是灰的”那句吗？
- [ ] `--no` 含 `real human, clothing, hair` 和五个防发灰词吗？
- [ ] 场景相关的追加词（`palace`、`cat, kitten`、`cropped hands, cropped feet`）加了吗？
- [ ] prompt 里没有角色名、游戏名、`sexy` 吗？
- [ ] 只改了一个变量吗？
