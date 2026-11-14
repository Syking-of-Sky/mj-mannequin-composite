# MJ 翻车对照表

## 怎么用这张表

MJ 不听话时，先想它是**怎么误会你的**：

- 老虎为什么像猫？——提示词里出现了“两个都在伞下”，它把老虎缩小塞进伞里。
- 画面为什么发灰？——人偶的灰色串到了整个场景，或者白色物件写太多。
- 场景为什么像宫殿？——MJ 默认“中式 = 宫殿”。

找到误会的来源，再改一处。**一次只改一个地方**：景别、焦段、颜色一起改，就不知道是哪一处起了作用。

## 对照表

| 出了什么问题 | 原因 | 怎么改 |
|---|---|---|
| 老虎大得像巨兽 | 写了 `giant` / `huge` | 删掉所有大小词，只写 `a white tiger` |
| 老虎小得像只猫，还缩在墙边 | 写了“两个都在伞下”，MJ 把老虎缩小塞进伞里；“背靠”被理解成靠墙 | 伞只给人撑；老虎写 `full grown adult white tiger with a muscular body`，放到提示词最前面；加 `centered composition, space on both sides`；`--no cat, kitten` |
| 景别太松，环境太多 | 写的是 `medium shot` 或全身 | 往紧调一档：`medium shot` → `cowboy shot` → `medium close-up`，焦段同时加长 |
| 景别太紧 | 跳档跳太多了 | **一次只调一档**，焦段也只退一档 |
| 拍满了，手脚却被裁掉 | 只写了 `fill the frame` | 动作收紧（并膝、抱膝、蜷身）；加 `her entire body including hands and feet inside the frame`；`--no cropped hands, cropped feet` |
| 整张图都发灰，像白模 | 配色写成了“白银淡紫”，白色东西写太多；人偶的灰色串到了整个场景 | 每样东西写具体颜色；加“只有人偶是灰的”那句；`--no` 加防发灰的词 |
| 人偶穿了衣服、长了头发 | MJ 自作主张 | `--no clothing, hair` |
| 出现不对的植物（比如热带芭蕉） | MJ 把芭蕉画成了香蕉树 | 换成别的植物（梧桐、竹子、桂花），`--no banana tree, palm tree` |
| 场景太豪华，不像江南水乡 | MJ 默认中式等于宫殿 | 写“白墙黛瓦、石板巷、天井、乌篷船”，`--no palace` |
| 人和动物各干各的，像两张图拼的 | 只写了两个主体，没有写关系 | 用视线、手、道具连起来：`the two looking at each other`、`fingertips almost touching`、伞甩出的水珠和老虎抖出的水珠撞在一起 |

## 镜头想要“侵入感”时

普通平视容易像产品图。想要“镜头钻进场景里”的感觉，用这些写法：

- 镜头钻进伞下、船篷里：`camera inside the shadow of the umbrella`
- 隔着前景偷看：`shot through the blurred whiskers of a tiger in the foreground`、`voyeur view through a carved lattice window`
- 越过动物的肩膀看人：`over-the-shoulder shot from behind a white tiger`
- 人物看向镜头：`looking up into the lens`

侵入感不是把镜头拉近，而是**给画面加一个前景遮挡或一个“偷看的人”**。加前景时注意别挡住人偶的脸和手，否则后期分镜不好用。

## 二次检查顺序

一次出图后按这个顺序看，别一上来就重刷：

1. **尺度**：人偶是成年比例吗？动物是正常大小吗？两者比例对吗？
2. **景别**：构图松紧是否符合镜头意图？手脚在画面里吗？
3. **光影**：人偶身上的亮面/暗面方向一致吗？颜色偏暖还是偏冷？后期棚拍能复现吗？
4. **颜色**：画面发灰吗？背景和衣服主色撞了吗？
5. **多余物**：人偶穿衣服/长头发了吗？有文字、水印、奇怪的植物吗？
6. **可用性**：这张图能当背景吗（人偶边缘清楚、背景纹理连续）？能当分镜吗（姿势可复现）？能当布光图吗（明暗关系清楚）？

只有第 6 项也过了，才进入故事线和棚拍。
