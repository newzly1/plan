# -*- coding: utf-8 -*-
"""Single source of truth for the Bali trip voting page.
Transcribed faithfully from 印尼旅行项目投票清单.md.
Each subspot has an English Commons search query `q`; each item a `video_q`.
Media (image data URIs, youtube ids) are resolved by fetch_media.py into media.json.
"""

META = {
    "title": "巴厘岛及周边 · 6 人投票参考",
    "subtitle": "看图看视频，选出你想去的地方",
    "window": "10/2 落地 → 10/11 返程 · 约 9–10 天 · 基地巴厘岛(DPS)",
    "howto": "每个景点看图/看视频了解它长什么样，点「必去 / 可去」标记，底部一键复制你的选择发到群里。",
    "rate": "价格为人均活动费(不含机票住宿)，1 万印尼盾 ≈ ¥4.5，旺季粗估，仅供参考。",
}

LEGEND = ["海岛/海滩", "火山", "徒步", "潜水/浮潜", "文化/寺庙", "网红打卡"]

REGIONS = [
    {"id": "A", "name": "巴厘岛本岛 (Bali)", "tag": "大本营 · 枢纽", "days": "建议 5–7 天",
     "budget": "人均约 ¥700–1400",
     "desc": "落地机场所在、向外辐射的枢纽；内部靠包车/摩托，跨区约 1–2 小时车程。9–10 天的行程主体一定落在这里。"},
    {"id": "B", "name": "佩尼达三岛 (Nusa Penida/Lembongan/Ceningan)", "tag": "紧耦合 · 几乎必玩", "days": "建议 1–2 天",
     "budget": "人均约 ¥300–800",
     "desc": "从巴厘 Sanur 港快艇 30–45 分钟，与南巴厘紧耦合。可一日跟团或住岛 1–2 晚。"},
    {"id": "C", "name": "龙目岛 + 吉利三岛 (Lombok + Gili)", "tag": "跨岛可行圈", "days": "建议 2–3 天",
     "budget": "人均约 ¥500–1000（加林贾尼更高）",
     "desc": "从巴厘快艇约 1.5–2 小时，属可行圈，但会占掉一整段，与其他跨岛项目二选一。"},
    {"id": "D", "name": "科莫多 / 纳闽巴霍 (Komodo · Labuan Bajo)", "tag": "海岛风光天花板", "days": "建议 2–3 天",
     "budget": "人均约 ¥1000–2100（船宿更高）",
     "desc": "从巴厘 DPS 飞纳闽巴霍约 1–1.5 小时，含往返航班占 2–3 天，与龙目/吉利二选一。"},
    {"id": "E", "name": "东爪哇 · 宜珍火山 (Ijen)", "tag": "最近的世界级火山", "days": "建议 2 天",
     "budget": "人均约 ¥500–900",
     "desc": "离巴厘最近的火山：巴厘西端 Gilimanuk 渡轮过海到 Banyuwangi 即达，可陆路联游。"},
]

# Each item: id, region, names, tags, time, price, feature/caution/coupling (from source doc),
# subspots [{id,zh,en,q}], video_q. `highlight` marks items that also appear in 精华速览.
ITEMS = [
    {
        "id": "A1", "region": "A", "zh": "南巴厘海岸线", "en": "South Bali Coast",
        "tags": ["海滩", "寺庙", "日落"], "time": "2–3 天",
        "price": "海滩免费；乌鲁瓦图庙 ¥25 + Kecak 火舞 ¥60–80；金巴兰海鲜人均 ¥100–200；海滩俱乐部低消 ¥150+",
        "feature": "库塔/水明漾/Canggu 冲浪与海滩俱乐部、乌鲁瓦图断崖庙 + Kecak 火祭舞日落、金巴兰沙滩海鲜烧烤、努沙杜瓦度假区。夜生活最热闹。",
        "caution": "部分海滩有离岸流/暗涌，按能力选冲浪点；海滩俱乐部消费高、需提前订位；旱季浪大适合冲浪但不适合亲子戏水。",
        "coupling": "离机场最近，首尾住这里最省事；紧邻佩尼达出发港 Sanur。",
        "video_q": "Uluwatu temple Kecak fire dance sunset Bali",
        "subspots": [
            {"id": "A1a", "zh": "乌鲁瓦图断崖庙", "en": "Uluwatu Temple", "q": "Uluwatu Temple Bali cliff"},
            {"id": "A1b", "zh": "Kecak 火祭舞", "en": "Kecak Fire Dance", "q": "Kecak dance Uluwatu Bali"},
            {"id": "A1c", "zh": "金巴兰海鲜沙滩", "en": "Jimbaran Bay", "q": "Jimbaran Bay beach Bali sunset"},
            {"id": "A1d", "zh": "水明漾/库塔海滩", "en": "Seminyak / Kuta Beach", "q": "Seminyak beach Bali sunset"},
        ],
    },
    {
        "id": "A2", "region": "A", "zh": "乌布文化区", "en": "Ubud", "highlight": True,
        "tags": ["文化", "梯田", "瀑布"], "time": "2–3 天",
        "price": "门票各 ¥25–100；漂流约 ¥250–400；SPA ¥150+",
        "feature": "德格拉朗梯田、圣猴森林、Tirta Empul 圣泉庙、丛林秋千、多条瀑布(Tegenungan/Tibumana)、Ayung 河漂流、瑜伽与 SPA、手工艺村。文艺慢节奏核心。",
        "caution": "猴子会抢眼镜/手机/食物；梯田与秋千为收费网红点、人多需早去；进庙须围纱笼(sarong)。",
        "coupling": "地处中部，是前往东部/北部火山瀑布的最佳中转基地。",
        "video_q": "Ubud Bali Tegallalang rice terrace 4k",
        "subspots": [
            {"id": "A2a", "zh": "德格拉朗梯田", "en": "Tegallalang Rice Terrace", "q": "Tegallalang rice terrace Bali"},
            {"id": "A2b", "zh": "圣猴森林", "en": "Sacred Monkey Forest", "q": "Sacred Monkey Forest Ubud Bali"},
            {"id": "A2c", "zh": "Tirta Empul 圣泉庙", "en": "Tirta Empul Temple", "q": "Tirta Empul temple Bali"},
            {"id": "A2d", "zh": "丛林秋千", "en": "Bali Swing", "q": "Bali swing Tegallalang jungle"},
            {"id": "A2e", "zh": "Tegenungan 瀑布", "en": "Tegenungan Waterfall", "q": "Tegenungan waterfall Bali"},
        ],
    },
    {
        "id": "A3", "region": "A", "zh": "东巴厘 · 巴图尔火山", "en": "East Bali · Mt Batur", "highlight": True,
        "tags": ["火山", "徒步", "潜水", "天堂之门"], "time": "2–3 天",
        "price": "火山日出徒步人均约 ¥200–350（含天堂之门门票与包车）",
        "feature": "巴图尔火山(Batur)日出徒步、Lempuyang 天堂之门、Tirta Gangga 水宫、Besakih 母庙、Tulamben/Amed 的 USS Liberty 沉船浮潜潜水。",
        "caution": "火山徒步需向导、凌晨约 2 点出发；『天堂之门倒影』是排队 + 镜面道具拍出来的；沉船潜点需一定水性。",
        "coupling": "凌晨出发的火山团常与乌布联住，串东部一日环线。",
        "video_q": "Mount Batur sunrise trekking Bali 4k",
        "subspots": [
            {"id": "A3a", "zh": "巴图尔火山日出", "en": "Mt Batur Sunrise", "q": "Mount Batur sunrise summit Bali"},
            {"id": "A3b", "zh": "Lempuyang 天堂之门", "en": "Gates of Heaven", "q": "Lempuyang temple gates of heaven Bali"},
            {"id": "A3c", "zh": "Tirta Gangga 水宫", "en": "Tirta Gangga", "q": "Tirta Gangga water palace Bali"},
            {"id": "A3d", "zh": "Besakih 母庙", "en": "Besakih Temple", "q": "Besakih temple Bali"},
            {"id": "A3e", "zh": "USS Liberty 沉船", "en": "USS Liberty Wreck", "q": "USS Liberty wreck Tulamben diving"},
        ],
    },
    {
        "id": "A4", "region": "A", "zh": "北巴厘 & 中部高地", "en": "North Bali & Highlands",
        "tags": ["瀑布", "湖庙", "打卡"], "time": "1–2 天",
        "price": "包车分摊人均约 ¥60–90/天；湖庙 ¥35、Handara 门 ¥15、Sekumpul 瀑布 ¥45",
        "feature": "Sekumpul/Banyumala 瀑布、Munduk 山区与双子湖、Ulun Danu Beratan 湖庙(50000 卢比纸币图案)、Handara 网红门、Lovina 看海豚。凉爽清幽。",
        "caution": "山路弯多易晕车；Sekumpul 需下切徒步、雨后湿滑较累；Lovina 为野生海豚不保证遇见。",
        "coupling": "可与东部火山、乌布串成中北部环线一并玩。",
        "video_q": "Ulun Danu Beratan temple Sekumpul waterfall north Bali",
        "subspots": [
            {"id": "A4a", "zh": "Ulun Danu Beratan 湖庙", "en": "Ulun Danu Beratan", "q": "Ulun Danu Beratan temple lake Bali"},
            {"id": "A4b", "zh": "Sekumpul 瀑布", "en": "Sekumpul Waterfall", "q": "Sekumpul waterfall Bali"},
            {"id": "A4c", "zh": "Handara 网红门", "en": "Handara Gate", "q": "Handara gate Bali"},
            {"id": "A4d", "zh": "Munduk 双子湖", "en": "Munduk Twin Lakes", "q": "Buyan Tamblingan twin lake Bali viewpoint"},
            {"id": "A4e", "zh": "Banyumala 瀑布", "en": "Banyumala Waterfall", "q": "Banyumala twin waterfall Bali"},
        ],
    },
    {
        "id": "A5", "region": "A", "zh": "塔那罗海神庙", "en": "Tanah Lot", "highlight": True,
        "tags": ["海庙", "日落"], "time": "半天", "price": "门票约 ¥30",
        "feature": "立于海中岩石上的神庙，巴厘的日落名片。",
        "caution": "涨潮时无法走到庙底；日落时段人极多，宜提前到。",
        "coupling": "位于西南沿海，可与 Canggu / 乌布顺路安排。",
        "video_q": "Tanah Lot temple sunset Bali 4k",
        "subspots": [
            {"id": "A5a", "zh": "海神庙日落", "en": "Tanah Lot Sunset", "q": "Tanah Lot temple sunset Bali"},
            {"id": "A5b", "zh": "海中神庙", "en": "Sea Temple", "q": "Tanah Lot temple rock Bali"},
        ],
    },
    {
        "id": "B1", "region": "B", "zh": "佩尼达网红海岸", "en": "Nusa Penida Coast", "highlight": True,
        "tags": ["海岛", "悬崖打卡", "浮潜"], "time": "1–2 天",
        "price": "一日跳岛团人均约 ¥250–450（含往返快艇）",
        "feature": "Kelingking 霸王龙海滩、Broken Beach、Angel's Billabong、Diamond Beach、Crystal Bay 浮潜。巴厘最出片的悬崖海景。",
        "caution": "岛内道路极差、坡陡，建议包车 + 司机而非自驾摩托；网红点悬崖台阶陡、排队久；备晕船药。",
        "coupling": "与南巴厘同一港区，最易衔接；可与蝠鲼共游同日安排。",
        "video_q": "Nusa Penida Kelingking beach Bali drone 4k",
        "subspots": [
            {"id": "B1a", "zh": "Kelingking 霸王龙海滩", "en": "Kelingking Beach", "q": "Kelingking Beach Nusa Penida"},
            {"id": "B1b", "zh": "Broken Beach", "en": "Broken Beach", "q": "Broken Beach Nusa Penida"},
            {"id": "B1c", "zh": "Angel's Billabong", "en": "Angel's Billabong", "q": "Angel's Billabong Nusa Penida"},
            {"id": "B1d", "zh": "Diamond Beach", "en": "Diamond Beach", "q": "Diamond Beach Nusa Penida"},
            {"id": "B1e", "zh": "Crystal Bay", "en": "Crystal Bay", "q": "Crystal Bay Nusa Penida beach"},
        ],
    },
    {
        "id": "B2", "region": "B", "zh": "蝠鲼 & 海龟共游", "en": "Manta & Turtle Snorkel", "highlight": True,
        "tags": ["浮潜", "海洋"], "time": "半天", "price": "浮潜团人均约 ¥200–400",
        "feature": "Manta Point 与蝠鲼(魔鬼鱼)同游、Crystal Bay/Gamat Bay 浮潜看海龟与珊瑚。旱季海况透明度高。",
        "caution": "Manta Point 有涌浪、需跟船听教练；晕船者提前服药；防晒用珊瑚友好型。",
        "coupling": "常与佩尼达陆地打卡拼成一日跳岛团。",
        "video_q": "snorkeling manta ray Nusa Penida Manta Point",
        "subspots": [
            {"id": "B2a", "zh": "蝠鲼(魔鬼鱼)同游", "en": "Manta Ray", "q": "Manta ray snorkeling Nusa Penida"},
            {"id": "B2b", "zh": "海龟浮潜", "en": "Sea Turtle", "q": "green sea turtle snorkeling Indonesia reef"},
        ],
    },
    {
        "id": "B3", "region": "B", "zh": "蓝梦岛 Lembongan/Ceningan", "en": "Nusa Lembongan/Ceningan",
        "tags": ["海岛", "跳水", "黄桥"], "time": "1–2 天",
        "price": "往返快艇约 ¥120–200/人 + 岛上包车/活动人均 ¥100–200",
        "feature": "红树林划船、恶魔的眼泪(Devil's Tear)浪爆、Ceningan 黄桥与蓝湖跳水、慢生活小岛氛围。比佩尼达更悠闲。",
        "caution": "恶魔的眼泪浪大勿靠太近岩边；蓝湖跳水需评估自身能力与潮位。",
        "coupling": "与佩尼达仅隔一条水道，可两岛连住。",
        "video_q": "Nusa Lembongan Ceningan devil's tear yellow bridge",
        "subspots": [
            {"id": "B3a", "zh": "恶魔的眼泪", "en": "Devil's Tear", "q": "Devil's Tear Nusa Lembongan"},
            {"id": "B3b", "zh": "Ceningan 黄桥", "en": "Yellow Bridge", "q": "Yellow Bridge Nusa Ceningan Lembongan"},
            {"id": "B3c", "zh": "梦幻海滩", "en": "Dream Beach Lembongan", "q": "Dream Beach Nusa Lembongan"},
        ],
    },
    {
        "id": "C1", "region": "C", "zh": "吉利三岛 Gili", "en": "Gili Islands",
        "tags": ["海岛", "浮潜看海龟", "沙滩秋千"], "time": "2–3 天",
        "price": "往返快艇人均约 ¥350–600 + 浮潜团 ¥150–300",
        "feature": "Trawangan(派对)/Air(适中)/Meno(安静)三岛任选；岛上无机动车，只有自行车与马车；浮潜近距离看海龟、海底秋千与雕塑。",
        "caution": "岛上无警察、ATM 少、医疗有限，现金多备；浮潜留意水母与海流；跨海快艇遇风浪较颠。",
        "coupling": "与龙目岛同一线；三岛之间跳岛船 15–30 分钟。",
        "video_q": "Gili Islands Trawangan Lombok beach 4k",
        "subspots": [
            {"id": "C1a", "zh": "吉利岛海滩秋千", "en": "Gili Beach Swing", "q": "Gili Trawangan beach swing sunset"},
            {"id": "C1b", "zh": "海底雕塑/秋千", "en": "Underwater Statues", "q": "Gili Meno underwater statues Nest"},
        ],
    },
    {
        "id": "C2", "region": "C", "zh": "林贾尼火山徒步", "en": "Mt Rinjani Trek",
        "tags": ["火山", "重装徒步"], "time": "2–3 天", "price": "2 天 1 夜团人均约 ¥800–1500",
        "feature": "Rinjani(3726m)火山口湖 + 温泉，印尼最经典的多日重装徒步之一，登顶看日出云海震撼。",
        "caution": "难度高、需体力与向导；10 月仍为开放旺季且天气好，雨季关闭；夜间极冷需保暖装备。对 9–10 天行程偏重。",
        "coupling": "独立硬核项目，适合体力好的分队；玩完可下山接吉利放松。",
        "video_q": "Mount Rinjani trekking crater lake Lombok",
        "subspots": [
            {"id": "C2a", "zh": "火山口湖 Segara Anak", "en": "Segara Anak Lake", "q": "Mount Rinjani Segara Anak crater lake"},
            {"id": "C2b", "zh": "登顶日出云海", "en": "Summit Sunrise", "q": "Mount Rinjani summit sunrise Lombok"},
        ],
    },
    {
        "id": "C3", "region": "C", "zh": "龙目岛南岸", "en": "South Lombok",
        "tags": ["海滩", "粉沙", "瀑布"], "time": "2–3 天",
        "price": "龙目包车分摊人均约 ¥80–130/天 + 粉色沙滩船程约 ¥50–100/人",
        "feature": "Kuta Lombok 冲浪、Tanjung Aan 粉沙海湾、Merese Hill 观景、Tiu Kelep/Sendang Gile 瀑布、东南部粉色沙滩。比巴厘更原始少人。",
        "caution": "景点分散、路况一般，需包车；粉色沙滩较偏远，含船程；防晒防中暑。",
        "coupling": "与吉利、林贾尼同属龙目一线，可组合安排。",
        "video_q": "South Lombok Tanjung Aan Merese Hill beach 4k",
        "subspots": [
            {"id": "C3a", "zh": "Tanjung Aan 粉沙海湾", "en": "Tanjung Aan Beach", "q": "Tanjung Aan beach Lombok"},
            {"id": "C3b", "zh": "Tiu Kelep 瀑布", "en": "Tiu Kelep Waterfall", "q": "Tiu Kelep waterfall Lombok"},
            {"id": "C3c", "zh": "粉色沙滩", "en": "Pink Beach Lombok", "q": "Pink Beach Lombok Tangsi"},
        ],
    },
    {
        "id": "D1", "region": "D", "zh": "科莫多跳岛", "en": "Komodo Island Hopping",
        "tags": ["海岛", "Padar 观景", "浮潜"], "time": "2–3 天",
        "price": "往返机票人均约 ¥600–1200 + 跳岛团 ¥400–900",
        "feature": "科莫多巨蜥(野生)、Padar 岛三色海湾观景、粉色沙滩、Manta Point 蝠鲼、Kanawa/Kelor 浮潜、蝙蝠岛日落。印尼海岛风光天花板之一。",
        "caution": "上岛看龙必须跟园区向导——巨蜥能奔跑与游泳、具攻击性；部分海域有流，浮潜跟船。",
        "coupling": "相对独立(需飞机)；玩法内部紧凑，一次跳岛全包。",
        "video_q": "Komodo island Padar viewpoint pink beach drone 4k",
        "subspots": [
            {"id": "D1a", "zh": "Padar 岛三色海湾", "en": "Padar Island", "q": "Padar island viewpoint Komodo"},
            {"id": "D1b", "zh": "科莫多巨蜥", "en": "Komodo Dragon", "q": "Komodo dragon Komodo national park"},
            {"id": "D1c", "zh": "粉色沙滩", "en": "Pink Beach", "q": "Pink Beach Komodo island"},
            {"id": "D1d", "zh": "Kanawa/Kelor 浮潜", "en": "Kelor Island", "q": "Kelor island Komodo viewpoint"},
        ],
    },
    {
        "id": "D2", "region": "D", "zh": "船宿 Liveaboard", "en": "Komodo Liveaboard",
        "tags": ["潜水", "海上过夜", "日出"], "time": "2–4 天",
        "price": "2 天船宿人均约 ¥1500–3000+（另含机票）",
        "feature": "住在船上巡游科莫多海域，避开日间人潮，清晨独占 Padar 观景与无人海滩，潜水条件世界级。体验感最强。",
        "caution": "10 月仍为旺季，船位需提前预订；晕船者慎选或备药；确认船只安全与卫生口碑。",
        "coupling": "把科莫多所有点一次打包，替代散拼跳岛。",
        "video_q": "Komodo liveaboard phinisi boat sailing sunrise",
        "subspots": [
            {"id": "D2a", "zh": "Phinisi 帆船船宿", "en": "Phinisi Liveaboard", "q": "phinisi boat Komodo Labuan Bajo"},
            {"id": "D2b", "zh": "清晨 Padar", "en": "Padar Sunrise", "q": "Padar island sunrise Komodo"},
        ],
    },
    {
        "id": "E1", "region": "E", "zh": "宜珍火山 · 蓝色火焰", "en": "Ijen Blue Fire",
        "tags": ["火山", "夜徒步", "蓝火"], "time": "2 天（含夜间徒步）",
        "price": "含往返渡轮的 2 天团人均约 ¥500–900",
        "feature": "Ijen——全球罕见的蓝色火焰(Blue Fire)、翠绿硫磺酸湖、扛硫磺的矿工。凌晨下火山口的独特体验。",
        "caution": "凌晨 1–2 点出发下火山口；有硫磺毒气，必须戴防毒面具、跟向导行动；夜间冷需保暖。",
        "coupling": "可从巴厘陆路 + 渡轮当地联游。可选延伸：再花 1–2 天西行接布罗莫(Bromo)日出。",
        "video_q": "Ijen blue fire crater sulfur East Java night",
        "subspots": [
            {"id": "E1a", "zh": "蓝色火焰", "en": "Blue Fire", "q": "Ijen blue fire crater night"},
            {"id": "E1b", "zh": "翠绿硫磺酸湖", "en": "Sulfur Crater Lake", "q": "Ijen crater acid lake sulfur"},
        ],
    },
]

# 精华速览 (references a subspot image + one-liner). order = display order.
HIGHLIGHTS = [
    {"item": "A2", "img": "A2a", "title": "乌布文化区", "blurb": "梯田 / 圣猴森林 / 瀑布，巴厘的灵魂与文艺慢生活"},
    {"item": "B1", "img": "B1a", "title": "佩尼达 · 霸王龙海滩", "blurb": "全巴厘最出片的悬崖海景"},
    {"item": "A1", "img": "A1a", "title": "乌鲁瓦图断崖庙 + 火舞", "blurb": "悬崖上的日落 + Kecak 火祭舞"},
    {"item": "A3", "img": "A3b", "title": "天堂之门 + 东巴厘火山", "blurb": "网红打卡 + 火山日出徒步"},
    {"item": "B2", "img": "B2a", "title": "蝠鲼 / 海龟浮潜", "blurb": "近距离与海龟、魔鬼鱼同游"},
    {"item": "A5", "img": "A5a", "title": "塔那罗海神庙日落", "blurb": "巴厘的日落名片"},
    {"item": "A1", "img": "A1c", "title": "金巴兰海鲜 + 海滩", "blurb": "沙滩烧烤、海滩俱乐部，度假放松"},
]

COMBOS = [
    {"no": "①", "name": "纯巴厘 + 佩尼达（最轻松）", "content": "A + B", "cross": "仅快艇 30–45 分",
     "days": "巴厘 7–8 + 佩尼达 1–2", "budget": "¥1000–1800",
     "note": "零跨岛航班、节奏最舒服，适合想放松、不折腾的分队。"},
    {"no": "②", "name": "巴厘 + 吉利/龙目", "content": "A + B + C", "cross": "快艇 1.5–2h",
     "days": "巴厘 5–6 + 龙目 2–3", "budget": "¥1800–3000",
     "note": "在巴厘基础上加一段海岛(吉利放空)，跨岛一次到位。"},
    {"no": "③", "name": "巴厘 + 科莫多", "content": "A + B + D", "cross": "飞机 1–1.5h",
     "days": "巴厘 6 + 科莫多 2–3", "budget": "¥2500–4500",
     "note": "科莫多封神，海岛风光天花板，跨岛一次到位。"},
    {"no": "④", "name": "巴厘 + 宜珍火山", "content": "A + B + E", "cross": "陆路 + 渡轮",
     "days": "巴厘 7 + 宜珍 2", "budget": "¥1600–2800",
     "note": "用最短代价加一座世界级火山，体验差异化。"},
]

COMBO_HINT = "9–10 天的现实：巴厘本岛 + 佩尼达为主轴，最多再加 1 个跨岛项目。不建议同时塞两个跨岛项目(如吉利+科莫多)，交通太赶。"

PRICES = [
    ("巴厘门票 & 活动 (人均)", [
        ("德格拉朗梯田", "¥12（秋千另 ¥90–230）"), ("圣猴森林", "¥40"),
        ("Tirta Empul 圣泉庙", "¥35"), ("Tegenungan/Tibumana 瀑布", "¥10–12"),
        ("Ayung 河漂流", "¥250–350"), ("ATV 四驱越野", "¥250–400"),
        ("巴图尔火山日出徒步", "¥160–230"), ("Lempuyang 天堂之门", "¥25–50"),
        ("Besakih 母庙", "¥30–70"), ("Ulun Danu Beratan 湖庙", "¥35"),
        ("Handara Gate 拍照", "¥15"), ("Sekumpul 瀑布(含向导)", "¥45"),
        ("塔那罗海神庙", "¥30"), ("乌鲁瓦图庙", "¥25"), ("Kecak 火祭舞", "¥60–80"),
        ("金巴兰沙滩海鲜", "¥100–200"), ("Tirta Gangga 水宫", "¥25"),
        ("USS Liberty 沉船 浮潜/潜水", "¥100–150 / ¥350–500"),
    ]),
    ("包车 & 市内交通", [
        ("巴厘包车+司机(约10h)", "¥350–500/车/天（6人分摊≈¥60–90/人）"),
        ("机场接送", "¥100–150/车"), ("Grab/Gojek 市区", "¥15–40/程"),
    ]),
    ("跨岛交通 (人均往返)", [
        ("Sanur ⇆ 佩尼达 快艇", "¥120–200"), ("巴厘 ⇆ 吉利/龙目 快艇", "¥350–600"),
        ("巴厘(DPS) ⇆ 纳闽巴霍(LBJ) 机票", "¥600–1200"), ("巴厘 ⇆ Banyuwangi 渡轮(宜珍)", "多含在宜珍团内"),
    ]),
    ("跟团 / 一日游 / 多日 (人均)", [
        ("佩尼达一日跳岛团(含快艇)", "¥250–450"), ("佩尼达蝠鲼/海龟浮潜", "¥200–400"),
        ("吉利浮潜团", "¥150–300"), ("林贾尼 2 天 1 夜徒步", "¥800–1500"),
        ("科莫多跳岛 1 日/2 日 1 夜", "¥300–500 / ¥600–1200"),
        ("科莫多船宿 2 天", "¥1500–3000+"), ("宜珍蓝火 2 天团", "¥500–900"),
    ]),
]

NOTES = [
    ("签证", "约 9–10 天在落地签(VOA)30 天免签范围内，落地办 VOA 即可(备返程票与住宿信息)。"),
    ("货币", "印尼盾(IDR)，小岛与村镇 ATM 少，多备现金、认准正规换汇点；大城市多数商户可刷卡。"),
    ("交通", "市区用 Grab/Gojek；巴厘常见『包车+司机』(6 人分摊很划算)；跨岛靠快艇或航班，旺季务必提前订票。"),
    ("网络", "落地即买电话卡，Telkomsel 信号覆盖最好。"),
    ("健康", "防『巴厘肚』——只喝瓶装水、慎吃生冷；强防晒且用珊瑚友好防晒霜；常备晕船药与肠胃药。"),
    ("安全", "海滩看旗帜、防离岸流；火山务必听向导、备保暖与防毒面具；摩托事故高发，租车需国际驾照并确认保险。"),
    ("礼仪", "进寺庙须围纱笼、遮肩盖膝；宗教场合与传统仪式保持尊重。"),
    ("季节", "10 月为旱季尾/肩季，天气仍佳、宜海岛与火山，仍属旺季——热门船宿/徒步/潜水越早订越好。"),
]
