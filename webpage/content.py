# -*- coding: utf-8 -*-
"""Single source of truth for the Bali trip voting page.
Transcribed faithfully from 印尼旅行项目投票清单.md.
Each subspot has an English Commons search query `q`; each item a `video_q`.
Media (image data URIs, youtube ids) are resolved by fetch_media.py into media.json.
"""

META = {
    "title": "巴厘岛及周边 · 选点手册",
    "subtitle": "看图看视频，选出你想去的地方",
    "window": "10/2 落地 → 10/11 返程 · 约 9–10 天 · 首站巴厘岛(DPS)",
    "howto": "每个景点看图/看视频了解它长什么样，点「必去 / 可去」标记，底部「我的清单」实时看大家的汇总。",
    "rate": "价格为人均活动费(不含机票住宿)，1 万印尼盾 ≈ ¥4.5，旺季粗估，仅供参考。",
}

LEGEND = ["海岛/海滩", "火山", "徒步", "潜水/浮潜", "文化/寺庙", "网红打卡"]

REGIONS = [
    {"id": "A", "name": "巴厘岛本岛 (Bali)", "tag": "首站 交通枢纽", "days": "建议 3–8 天",
     "budget": "人均约 ¥700–1400",
     "desc": "落地机场所在、向外辐射的枢纽；内部靠包车/摩托，跨区约 1–2 小时车程。节奏参考：时间紧凑 2–3 天（乌布核心 + 南巴厘断崖日落）；只逛精华 3–4 天（乌布深度 + 南巴厘全部 + 海神庙）；舒适加一个方向 5–6 天（精华 + 东或北任选其一）；四片区全覆盖 7–8 天。9–10 天的行程主要时间都在这里。"},
    {"id": "B", "name": "佩尼达三岛 (Nusa Penida/Lembongan/Ceningan)", "tag": "无缝衔接 · 几乎必玩", "days": "建议 1–2 天",
     "budget": "人均约 ¥300–800",
     "desc": "从巴厘 Sanur 港快艇 30–45 分钟，与南巴厘紧密相连。可一日跟团或住岛 1–2 晚。"},
    {"id": "C", "name": "科莫多 / 纳闽巴霍 (Komodo · Labuan Bajo)", "tag": "海岛风光天花板 · 首选项", "days": "建议 2–3 天",
     "budget": "人均约 ¥1000–2100（船宿更高）",
     "desc": "从巴厘 DPS 飞纳闽巴霍约 1–1.5 小时，含往返航班占 2–3 天，与龙目/吉利二选一。"},
    {"id": "D", "name": "东爪哇 · 布罗莫火山 (Bromo)", "tag": "月球表面日出 · 世界级火山", "days": "建议 2 天（含往返飞行+包车）",
     "budget": "人均约 ¥700–1200（含往返机票+包车+住宿+吉普团）",
     "desc": "从巴厘 DPS 飞泗水(SUB)约 1 小时，再包车 3–4 小时上布罗莫。凌晨乘吉普车登 Penanjakan 观景台看月球表面般的日出——被全球旅行者誉为印尼最震撼的火山景观。可与宜珍串联为东爪哇火山走廊（需 3–4 天）。"},
    {"id": "E", "name": "东爪哇火山群 · 宜珍 (Ijen)", "tag": "蓝火奇观 · 可串联布罗莫", "days": "建议 2 天（单独）/ 3–4 天（+布罗莫）",
     "budget": "人均约 ¥500–900（加布罗莫 +¥700–1200）",
     "desc": "离巴厘最近的火山：巴厘西端 Gilimanuk 渡轮过海到 Banyuwangi 即达。可与布罗莫串联为东爪哇火山走廊（布罗莫→宜珍→巴厘）。"},
    {"id": "F", "name": "龙目岛 + 吉利三岛 (Lombok + Gili)", "tag": "跨岛可行圈 · 备选", "days": "建议 2–3 天",
     "budget": "人均约 ¥500–1000（加林贾尼更高）",
     "desc": "从巴厘快艇约 1.5–2 小时，属可行圈，但会占掉一整段，与其他跨岛项目二选一。"},
]

# Each item: id, region, names, tags, time, price, feature/caution/coupling (亮点/注意/串联),
# subspots [{id,zh,en,q}], video_q. `highlight` marks items that also appear in 精华速览.
# Sorted: Bali hotspots → Penida → Komodo (liveaboard first) → Volcanoes → Fallback
ITEMS = [
    # ===== 巴厘岛本岛（落地首站，热门优先） =====
    {
        "id": "A1", "region": "A", "zh": "乌布 · 丛林与梯田", "en": "Ubud", "highlight": True,
        "tags": ["文化", "梯田", "瀑布"], "time": "2–3 天",
        "price": "门票各 ¥25–100；漂流约 ¥250–350；SPA ¥150+",
        "feature": "德格拉朗梯田、圣猴森林、Tirta Empul 圣泉庙、丛林秋千、多条瀑布(Tegenungan/Tibumana)、Ayung 河漂流、ATV 四驱越野、瑜伽与 SPA、手工艺村。文艺慢节奏核心。",
        "caution": "猴子会抢眼镜/手机/食物；梯田与秋千为收费网红点、人多需早去；进庙须围纱笼(sarong)。",
        "coupling": "地处中部，是前往东部/北部火山瀑布的最佳中转位置。",
        "video_q": "Ubud Bali Tegallalang rice terrace 4k",
        "subspots": [
            {"id": "A1a", "zh": "德格拉朗梯田", "en": "Tegallalang Rice Terrace", "q": "Tegallalang rice terrace Bali", "desc": "顺山势层叠的稻田，田埂有秋千和咖啡亭可歇脚。为收费网红点、人多，建议早去光线好也少排队。"},
            {"id": "A1b", "zh": "圣猴森林", "en": "Sacred Monkey Forest", "q": "Sacred Monkey Forest Ubud Bali", "desc": "雨林里自由行走的猴群与古老石庙，互动感强。猴子会抢手机眼镜食物，随身物品收好、别对视挑逗。"},
            {"id": "A1c", "zh": "Tirta Empul 圣泉庙", "en": "Tirta Empul Temple", "q": "Tirta Empul temple Bali", "desc": "圣泉涌出的浴池，信徒排队浸浴祈福。进庙须围纱笼，想参与浸浴需带替换衣物，留意队列秩序。"},
            {"id": "A1d", "zh": "丛林秋千", "en": "Bali Swing", "q": "Bali swing Tegallalang jungle", "desc": "悬于峡谷上的大秋千与鸟巢打卡点，出片轻松。项目收费、排队久，恐高者量力，注意扣好安全带。"},
            {"id": "A1e", "zh": "Tegenungan 瀑布", "en": "Tegenungan Waterfall", "q": "Tegenungan waterfall Bali", "desc": "市区近郊的宽幅瀑布，可走到水潭边戏水。步道湿滑、午后易人多，早去更清静，下水留意脚下石头。"},
        ],
    },
    {
        "id": "A2", "region": "A", "zh": "南巴厘海岸线", "en": "South Bali Coast",
        "tags": ["海滩", "寺庙", "日落"], "time": "2–3 天",
        "price": "海滩免费；乌鲁瓦图庙 ¥25 + Kecak 火舞 ¥60–80；金巴兰海鲜人均 ¥100–200；海滩俱乐部低消 ¥150+",
        "feature": "库塔/水明漾/Canggu 冲浪与海滩俱乐部、情人崖(乌鲁瓦图庙) + Kecak 火祭舞日落、金巴兰沙滩海鲜烧烤、努沙杜瓦度假区。夜生活最热闹。",
        "caution": "部分海滩有离岸流/暗涌，按能力选冲浪点；海滩俱乐部消费高、需提前订位；旱季浪大适合冲浪但不适合亲子戏水。",
        "coupling": "离机场最近，首尾住这里最省事；紧邻佩尼达出发港 Sanur。",
        "video_q": "Uluwatu temple Kecak fire dance sunset Bali",
        "subspots": [
            {"id": "A2a", "zh": "情人崖 (乌鲁瓦图庙)", "en": "Uluwatu Temple", "q": "Uluwatu Temple Bali cliff", "desc": "矗立海蚀断崖上的海神庙，又称情人崖，黄昏可顺道看 Kecak 火舞。崖边风大且无护栏，靠近观景台时注意脚下安全。"},
            {"id": "A2b", "zh": "Kecak 火祭舞", "en": "Kecak Fire Dance", "q": "Kecak dance Uluwatu Bali", "desc": "黄昏在断崖剧场以人声合唱伴演史诗，配海上落日。露天无空调，建议提前占座并带驱蚊液。"},
            {"id": "A2c", "zh": "金巴兰海鲜沙滩", "en": "Jimbaran Bay", "q": "Jimbaran Bay beach Bali sunset", "desc": "沙滩上现烤海鲜的露天排档，边吃边看海上日落。想踏浪宜查潮时，傍晚稍早到占位更从容。"},
            {"id": "A2d", "zh": "水明漾/库塔海滩", "en": "Seminyak / Kuta Beach", "q": "Seminyak beach Bali sunset", "desc": "巴厘最热闹的冲浪与日落海滩，沿线多俱乐部餐厅。部分岸段有离岸流，按能力选冲浪点，亲子留意浪况。"},
        ],
    },
    {
        "id": "A3", "region": "A", "zh": "塔那罗海神庙", "en": "Tanah Lot",
        "tags": ["海庙", "日落"], "time": "半天", "price": "门票约 ¥30",
        "feature": "立于海中岩石上的神庙，巴厘的日落名片。",
        "caution": "涨潮时无法走到庙底；日落时段人极多，宜提前到。",
        "coupling": "位于西南沿海，可与 Canggu / 乌布顺路安排。",
        "video_q": "Tanah Lot temple sunset Bali 4k",
        "subspots": [
            {"id": "A3a", "zh": "海神庙日落", "en": "Tanah Lot Sunset", "q": "Tanah Lot temple sunset Bali", "desc": "海中岩庙配橘色落日的巴厘名片。日落时段人极多，宜提前到占位；退潮露出礁石可走近庙底，涨潮时通道淹没，出发前查好潮时、注意湿滑。"},
        ],
    },
    {
        "id": "A4", "region": "A", "zh": "东巴厘 · 巴图尔火山", "en": "East Bali · Mt Batur",
        "tags": ["火山", "徒步", "潜水", "天堂之门"], "time": "2–3 天",
        "price": "火山日出徒步人均约 ¥200–350（含天堂之门门票与包车）",
        "feature": "巴图尔火山(Batur)日出徒步、Lempuyang 天堂之门、Tirta Gangga 与 Taman Ujung 水宫、Besakih 母庙、阿贡圣山远眺、Sidemen 梯田谷、Amed 黑沙渔村与 Tulamben 的 USS Liberty 沉船浮潜、Karangasem 白沙滩(Virgin Beach)。",
        "caution": "火山徒步需向导、凌晨约 2 点出发；『天堂之门倒影』是排队 + 镜面道具拍出来的；沉船潜点需一定水性。",
        "coupling": "凌晨出发的火山团常与乌布联住；推荐分 2–3 天走东部环线：一天巴图尔日出 + Besakih，一天 Lempuyang + Tirta Gangga + Tulamben 沉船浮潜。",
        "video_q": "Mount Batur sunrise trekking Bali 4k",
        "subspots": [
            {"id": "A4a", "zh": "巴图尔火山日出", "en": "Mt Batur Sunrise", "q": "Mount Batur sunrise summit Bali", "desc": "凌晨爬山看云海日出的活火山，山顶视野开阔。需向导、约两点出发，穿保暖防风衣物、带头灯与小食。"},
            {"id": "A4b", "zh": "Lempuyang 天堂之门", "en": "Gates of Heaven", "q": "Lempuyang temple gates of heaven Bali", "desc": "山门框住阿贡火山的对景，经典对称构图。倒影靠镜面道具拍出、需排队，建议一早到以减少等待。"},
            {"id": "A4c", "zh": "Tirta Gangga 水宫", "en": "Tirta Gangga", "q": "Tirta Gangga water palace Bali", "desc": "昔日王宫的层层水池与石雕，鱼池可赤脚走。园区不大、节奏慢，正午晒，带遮阳用具与换洗衣物。"},
            {"id": "A4d", "zh": "Besakih 母庙", "en": "Besakih Temple", "q": "Besakih temple Bali", "desc": "阿贡火山坡上的母庙建筑群，规模最宏。进庙须围纱笼，山路长，随向导走主轴线即可。"},
            {"id": "A4e", "zh": "USS Liberty 沉船", "en": "USS Liberty Wreck", "q": "USS Liberty wreck Tulamben diving", "desc": "近岸的二战货轮沉船，浮潜即可见鱼群与船体。需一定水性、可能有流，新手跟船听教练、勿触碰。"},
            {"id": "A4f", "zh": "Sidemen 梯田谷", "en": "Sidemen Valley", "q": "Sidemen valley rice terrace Bali Agung", "desc": "阿贡火山脚下静谧的梯田河谷，被称作'没有游客的乌布'，适合放慢脚步住一晚、看云开见峰。山路弯多易晕车，雨后田埂湿滑，清晨光线最好。"},
            {"id": "A4g", "zh": "Amed 潜水渔村", "en": "Amed", "q": "Amed Bali jukung boats black sand", "desc": "东岸黑沙渔村，成排传统 jukung 独木舟停靠滩上，清晨以阿贡火山为背景，也是自由潜与浮潜看珊瑚、沉船的好去处。日出前最美，下海留意海流。"},
            {"id": "A4h", "zh": "白沙滩 (Virgin Beach)", "en": "White Sand Beach", "q": "White Sand Beach Virgin Beach Karangasem Bali", "desc": "Karangasem 的白沙湾（俗称处女海滩），碧水白沙、比南部安静。设施简单，只有海鲜排档，自备现金与防晒，注意涨落潮与礁石。"},
            {"id": "A4i", "zh": "Taman Ujung 水上宫殿", "en": "Taman Ujung", "q": "Taman Ujung water palace Bali", "desc": "末代王朝的水上宫殿，大片水池、连廊与拱桥倒映远山，比 Tirta Gangga 更开阔大气。园区大遮荫少、正午晒，带遮阳、错峰避团。"},
            {"id": "A4j", "zh": "阿贡火山 (Agung)", "en": "Mount Agung", "q": "Mount Agung Bali volcano", "desc": "巴厘最高的圣火山(3031m)，锥形山体是东部天际线的主角，从 Lempuyang、Sidemen、Amed 皆可远眺。清晨云雾少最易见顶；登顶需向导、凌晨出发、体力要求高。"},
        ],
    },
    {
        "id": "A5", "region": "A", "zh": "北巴厘 & 中部高地", "en": "North Bali & Highlands",
        "tags": ["瀑布", "湖庙", "打卡"], "time": "2 天（1 天仅能走高地方向）",
        "price": "包车分摊人均约 ¥60–90/天；湖庙 ¥35、Handara 门 ¥15、Sekumpul 瀑布 ¥45",
        "feature": "水神庙(Ulun Danu Beratan，50000 印尼盾纸币图案)、Handara 网红门、Munduk 山区与双子湖、Sekumpul/Banyumala 瀑布、Lovina 看海豚（可选，最北端需清晨出发）。凉爽清幽。",
        "caution": "山路弯多易晕车；Sekumpul 需下切徒步、雨后湿滑较累；Lovina 为野生海豚且位于最北端，不保证能看到，需提前一晚住 Lovina 赶清晨出发。仅 1 天建议走高地方向（水神庙 + Handara + Munduk + Banyumala），放弃 Lovina 和 Sekumpul。",
        "coupling": "若预留 4–5 天，可与东部火山串成中北部大环线；时间有限时建议东线/北线二选一。",
        "video_q": "Ulun Danu Beratan temple Sekumpul waterfall north Bali",
        "subspots": [
            {"id": "A5a", "zh": "水神庙 (Ulun Danu Beratan)", "en": "Ulun Danu Beratan", "q": "Ulun Danu Beratan temple lake Bali", "desc": "湖心轻雾中的水上庙，纸币同款图案。清晨湖面平静倒影好，山区凉，带件薄外套。"},
            {"id": "A5b", "zh": "Sekumpul 瀑布", "en": "Sekumpul Waterfall", "q": "Sekumpul waterfall Bali", "desc": "北巴厘最壮观的多股瀑布群，需下切山谷步行到达。雨后台阶湿滑较累，穿防滑鞋、留足体力。"},
            {"id": "A5c", "zh": "Handara 网红门", "en": "Handara Gate", "q": "Handara gate Bali", "desc": "巨型石柱拱门框住绿意山道，对称构图好拍。景点小、排队拍人像，早去省时，旁山路弯多易晕车。"},
            {"id": "A5d", "zh": "Munduk 双子湖", "en": "Munduk Twin Lakes", "q": "Buyan Tamblingan twin lake Bali viewpoint", "desc": "山间两汪毗邻湖泊，配咖啡园与凉雾。观景点停车即看、不累，山路弯多慢行，适合顺路歇脚。"},
            {"id": "A5e", "zh": "Banyumala 瀑布", "en": "Banyumala Waterfall", "q": "Banyumala twin waterfall Bali", "desc": "幽谷里的双流瀑布汇成碧潭，可游泳。需走一段下坡石径，雨后湿滑，带换洗衣物与防滑鞋。"},
        ],
    },

    # ===== 佩尼达三岛（快艇衔接，从南巴厘出发） =====
    {
        "id": "B1", "region": "B", "zh": "佩尼达悬崖海岸", "en": "Nusa Penida Coast", "highlight": True,
        "tags": ["海岛", "悬崖打卡", "浮潜"], "time": "1–2 天",
        "price": "一日跳岛团人均约 ¥250–450（含往返快艇）",
        "feature": "精灵坠崖(Kelingking)、破碎沙滩(Broken Beach)、天使浴池(Angel's Billabong)、钻石沙滩(Diamond Beach)、水晶湾(Crystal Bay) 浮潜。巴厘最壮观的悬崖海景。",
        "caution": "岛内道路极差、坡陡，建议包车 + 司机而非自驾摩托；景点悬崖台阶陡、排队久；备晕船药。",
        "coupling": "与南巴厘同一港区，最易衔接；可与蝠鲼共游同日安排。",
        "video_q": "Nusa Penida Kelingking beach Bali drone 4k",
        "subspots": [
            {"id": "B1a", "zh": "精灵坠崖 (Kelingking)", "en": "Kelingking Beach", "q": "Kelingking Beach Nusa Penida", "desc": "经典悬崖海湾，俯瞰如精灵坠入大海的白色沙滩，巴厘最标志性的悬崖景观。下到沙滩台阶极陡且晒，体力一般者崖顶观景即可。"},
            {"id": "B1b", "zh": "破碎沙滩 (Broken Beach)", "en": "Broken Beach", "q": "Broken Beach Nusa Penida", "desc": "海浪穿出山体形成的天然拱洞与圆形泻湖。沿崖边步道走一圈即看，无护栏，靠近边缘注意风浪与脚下。"},
            {"id": "B1c", "zh": "天使浴池 (Angel's Billabong)", "en": "Angel's Billabong", "q": "Angel's Billabong Nusa Penida", "desc": "礁石环抱的天然潮池，水清可泡。涨潮浪会漫入、易滑，下池前看浪情，留意被浪卷走风险。"},
            {"id": "B1d", "zh": "钻石沙滩 (Diamond Beach)", "en": "Diamond Beach", "q": "Diamond Beach Nusa Penida", "desc": "银白沙滩嵌在陡峭崖壁间，需下木梯到达。崖壁无遮挡、阶梯晒，下到底戏水再爬回较耗体力。"},
            {"id": "B1e", "zh": "水晶湾 (Crystal Bay)", "en": "Crystal Bay", "q": "Crystal Bay Nusa Penida beach", "desc": "弧形海湾，浮潜看珊瑚、可能遇海龟。旱季透明度高，岸边有休憩摊，备浮潜装备与防晒。"},
        ],
    },
    {
        "id": "B2", "region": "B", "zh": "佩尼达 · 蝠鲼&海龟浮潜点", "en": "Manta & Turtle Snorkel",
        "tags": ["浮潜", "海洋"], "time": "半天", "price": "浮潜团人均约 ¥200–400",
        "feature": "Manta Point 蝠鲼浮潜、Crystal Bay/Gamat Bay 海龟与珊瑚浮潜。旱季海水透明度高。",
        "caution": "Manta Point 有涌浪、需跟船听教练；晕船者提前服药；防晒用珊瑚友好型。",
        "coupling": "常与佩尼达陆地打卡拼成一日跳岛团。",
        "video_q": "snorkeling manta ray Nusa Penida Manta Point",
        "subspots": [
            {"id": "B2a", "zh": "蝠鲼浮潜点 (Manta Point)", "en": "Manta Point", "q": "Manta ray snorkeling Nusa Penida", "desc": "跟船到 Manta Point 与大型蝠鲼同游，旱季概率高。有涌浪、需跟船听教练，晕船者提前服药。"},
            {"id": "B2b", "zh": "海龟浮潜", "en": "Sea Turtle", "q": "green sea turtle snorkeling Indonesia reef", "desc": "Crystal Bay/Gamat Bay 珊瑚区浮潜常遇海龟。水况看天气，防晒用珊瑚友好型，保持距离勿追摸。"},
        ],
    },
    {
        "id": "B3", "region": "B", "zh": "蓝梦岛 Lembongan/Ceningan", "en": "Nusa Lembongan/Ceningan",
        "tags": ["海岛", "跳水", "黄桥"], "time": "1–2 天",
        "price": "往返快艇约 ¥120–200/人 + 岛上包车/活动人均 ¥100–200",
        "feature": "红树林划船、恶魔的眼泪(Devil's Tear)巨浪、Ceningan 黄桥与蓝湖跳水、慢生活小岛氛围。比佩尼达更悠闲。",
        "caution": "恶魔的眼泪浪大，勿靠太近岩边；蓝湖跳水需评估自身能力与潮位。",
        "coupling": "与佩尼达仅隔一条水道，可两岛连住。",
        "video_q": "Nusa Lembongan Ceningan devil's tear yellow bridge",
        "subspots": [
            {"id": "B3a", "zh": "恶魔的眼泪", "en": "Devil's Tear", "q": "Devil's Tear Nusa Lembongan", "desc": "海浪砸向岩缝激起的巨大水爆，气势足。浪大切勿靠太近岩边，被浪卷下危险，外围稳妥观看。"},
            {"id": "B3b", "zh": "Ceningan 黄桥", "en": "Yellow Bridge", "q": "Yellow Bridge Nusa Ceningan Lembongan", "desc": "连接两岛的黄色小桥，步行或骑车跨过即到对岛。桥窄仅容单线，骑车慢行礼让，日落顺路看。"},
            {"id": "B3c", "zh": "梦幻海滩", "en": "Dream Beach Lembongan", "q": "Dream Beach Nusa Lembongan", "desc": "白沙海湾配崖景，人少安静。浪偏大不宜贸然下水，岸边有泳池与餐厅，适合躺平发呆。"},
        ],
    },

    # ===== 科莫多（你的首选，船宿优先） =====
    {
        "id": "C1", "region": "C", "zh": "船宿/跳岛", "en": "Komodo Liveaboard & Island Hopping", "highlight": True,
        "tags": ["潜水", "海上过夜", "日出", "海岛", "Padar 观景", "浮潜"], "time": "2–4 天",
        "price": "往返机票人均约 ¥600–1200 + 跳岛团 ¥300–1200（1 日/2 日 1 夜）；2 天船宿人均约 ¥1500–3000+ / 3 天约 ¥2500–5000+",
        "feature": "住在船上巡游科莫多海域，避开日间人潮，清晨独占 Padar 观景与无人海滩，潜水条件世界级。跳岛则覆盖科莫多巨蜥(野生)、Padar 岛三色海湾、粉色沙滩、Manta Point 蝠鲼浮潜、Taka Makassar 新月沙洲、Gili Lawa 草原观景、Kalong 蝙蝠岛日落。印尼海岛风光天花板之一。",
        "caution": "10 月仍为旺季，船位需提前预订；晕船者慎选或备药；确认船只安全与卫生口碑。上岛看龙必须跟园区向导——巨蜥能奔跑与游泳、具攻击性；部分海域有流，浮潜跟船。",
        "coupling": "将科莫多所有精华点一次打包，船宿体验感最强，跳岛灵活度高。",
        "video_q": "Komodo liveaboard phinisi boat Padar pink beach",
        "subspots": [
            {"id": "C1c", "zh": "Padar 岛三色海湾", "en": "Padar Island", "q": "Padar island viewpoint Komodo", "desc": "科莫多群岛最经典的俯瞰视角，三处海湾呈现不同深浅的蓝绿，旱季草坡金黄。需爬一段曝晒山坡，早去可避开炎热与人潮，带足水。"},
            {"id": "C1l", "zh": "科莫多粉色沙滩", "en": "Pink Beach", "q": "Pink Beach Komodo island", "desc": "珊瑚碎屑形成的淡粉沙滩，浮潜看珊瑚。正午晒、人潮随船到，早去更清静，防晒补水。"},
            {"id": "C1n", "zh": "蝠鲼浮潜点 (Manta Point)", "en": "Manta Point", "q": "Manta Point Komodo manta ray snorkeling", "desc": "科莫多 Manta Point 常年聚集巨型蝠鲼，浮潜即可看它们贴着水面滑翔掠食。海流较强，务必跟船听教练指挥、保持距离勿追逐触碰，晕船者提前备药。"},
            {"id": "C1h", "zh": "海龟浮潜", "en": "Sea Turtle Encounter", "q": "Komodo snorkeling sea turtle coral", "desc": "浮潜时与海龟并肩游过珊瑚礁，动作放缓、保持距离，勿追逐触碰。"},
            {"id": "C1k", "zh": "科莫多巨蜥", "en": "Komodo Dragon", "q": "Komodo dragon Komodo national park", "desc": "野生巨蜥在岛上漫步，体型大具攻击性。上岛必须跟园区向导、保持距离，勿掉队与投喂。"},
            {"id": "C1o", "zh": "Taka Makassar 新月沙洲", "en": "Taka Makassar", "q": "Taka Makassar sandbar Komodo aerial", "desc": "退潮时浮出海面的新月形白沙洲，四周是渐层松石色浅滩与珊瑚礁，跳岛必拍的梦幻一景。仅退潮可登、无遮荫极晒，注意防晒补水、勿踩踏珊瑚。"},
            {"id": "C1m", "zh": "Kanawa/Kelor 浮潜", "en": "Kelor Island", "q": "Kelor island Komodo viewpoint", "desc": "小岛周边清澈珊瑚礁，浮潜轻松看鱼。部分海域有流，跟船浮潜、勿远离，带珊瑚友好防晒。"},
            {"id": "C1i", "zh": "山顶俯瞰海湾", "en": "Summit Bay View", "q": "Komodo island hilltop bay view", "desc": "登上无人小岛的高坡，俯瞰停泊的船只与曲折海湾，是跳岛行程中隐秘的观景位。"},
            {"id": "C1p", "zh": "Gili Lawa 草原观景", "en": "Gili Lawa", "q": "Gili Lawa island Komodo viewpoint", "desc": "登上无人小岛的草坡俯瞰科莫多群岛与湛蓝海湾，旱季金黄、雨季翠绿，日落尤其壮阔。需徒步爬一段裸坡、无遮荫，穿防滑鞋带足水，清晨或傍晚上山避晒。"},
            {"id": "C1d", "zh": "海湾与 Phinisi 帆船", "en": "Bay with Phinisi", "q": "Phinisi boat Komodo bay", "desc": "传统 Phinisi 帆船停泊在翡翠海湾，是船宿与跳岛之间转换航线的日常美景。"},
            {"id": "C1f", "zh": "帆船甲板巡游", "en": "Deck Cruising", "q": "Komodo liveaboard deck sailing", "desc": "在 Phinisi 木甲板上巡游群岛，海风、蓝天与远处火山轮廓，是船宿最松弛的时光。"},
            {"id": "C1g", "zh": "船头静享时光", "en": "Bow Serenity", "q": "Komodo boat bow ocean sunrise", "desc": "盘坐船头看海天一色，船行时水花声与开阔视野，船宿独有的冥想时刻。"},
            {"id": "C1e", "zh": "Kalong 蝙蝠岛日落", "en": "Kalong Island", "q": "Kalong island Komodo flying fox sunset", "desc": "黄昏在船宿甲板上等待成千上万只果蝠从红树林小岛飞出，漫天剪影与晚霞交织，是船宿夜泊前的经典画面。在船上观赏即可，备长焦与外套，日落后海上转凉。"},
            {"id": "C1j", "zh": "科莫多岛掠影", "en": "Komodo Montage", "q": "Komodo island pink beach deer sunset", "desc": "山径、粉色沙滩上的鹿、日落蝙蝠群——科莫多跳岛与船宿的精华切片集合。"},
        ],
    },

    # ===== 东爪哇火山群（延伸选择） =====
    {
        "id": "D1", "region": "D", "zh": "布罗莫火山 · 月球表面日出", "en": "Mt Bromo Sunrise", "highlight": True,
        "tags": ["火山", "日出", "吉普车"], "time": "2 天（含往返飞行+包车）",
        "price": "巴厘(DPS)⇆泗水(SUB)往返机票人均约 ¥400–800 + 布罗莫吉普日出团 ¥150–250/人 + 住宿 ¥100–200",
        "feature": "凌晨乘吉普车登 Penanjakan 观景台俯瞰布罗莫火山口与腾格尔沙海的日出——被全球旅行者誉为'地球上最像月球表面的地方'，布罗莫火山口、巴托克火山锥与远方塞梅鲁火山同框。日出后穿越'沙海'步行登火山口边缘看冒烟的活火山腹地。南麓还有酷似《天线宝宝》的翠绿草原山丘，凌晨暗夜光害极低可仰望银河。",
        "caution": "凌晨 3 点吉普出发上山，火山口海拔 2329m 但观景台可达性高；山顶极冷（5–10°C），务必带防风保暖外套；火山灰大，需口罩或头巾；上下山多弯易晕车。",
        "coupling": "与宜珍(E1)可串联为东爪哇 3–4 天火山走廊（布罗莫→宜珍→巴厘渡轮回）；单独走布罗莫则从巴厘飞泗水往返，最少预留 2 天。",
        "video_q": "Mount Bromo sunrise Penanjakan viewpoint East Java 4k",
        "subspots": [
            {"id": "D1f", "zh": "火山群云海日出", "en": "Bromo Sunrise Sea of Clouds", "q": "Mount Bromo sunrise sea of clouds panorama", "desc": "日出后云海尚未散去时，布罗莫、巴托克与塞梅鲁火山锥浮于云海之上，壮阔全景。"},
            {"id": "D1e", "zh": "火山公路视角", "en": "Volcano Road View", "q": "Bromo volcano road view Indonesia", "desc": "从山脚村庄公路远眺火山，日常村落与宏伟火山同框，是布罗莫行程中常被忽略的地道视角。"},
            {"id": "D1a", "zh": "Penanjakan 日出观景台", "en": "Penanjakan Sunrise", "q": "Mount Bromo sunrise Penanjakan viewpoint Indonesia", "desc": "月球表面经典视角：布罗莫火山口、巴托克火山锥与远处塞梅鲁火山同框的日出云海。凌晨 3 点吉普出发，观景台冷务必穿保暖外套，占好机位等日出。"},
            {"id": "D1c", "zh": "特勒图比草原山丘", "en": "Teletubbies Hill", "q": "Bromo Teletubbies savanna green hills", "desc": "布罗莫火山南麓连绵起伏的翠绿草丘，因酷似《天线宝宝》草原得名，与灰黑沙海形成强烈反差。雨季后最绿，随吉普团顺访，草坡无遮荫注意防晒。"},
            {"id": "D1d", "zh": "布罗莫银河星空", "en": "Bromo Milky Way", "q": "Bromo milky way night stars", "desc": "凌晨吉普出发前的高原光害极低，火山与沙海上方常见清晰银河。需三脚架长曝、夜里严寒务必保暖，留意脚下火山灰与陡坡安全。"},
        ],
    },
    {
        "id": "E1", "region": "E", "zh": "宜珍火山 · 蓝色火焰", "en": "Ijen Blue Fire",
        "tags": ["火山", "夜徒步", "蓝火"], "time": "2 天（含夜间徒步）",
        "price": "含往返渡轮的 2 天团人均约 ¥500–900",
        "feature": "Ijen——全球罕见的蓝色火焰(Blue Fire)、翠绿硫磺酸湖、扛硫磺的矿工。凌晨下火山口的独特体验，破晓时整座火山口全景尤为壮观。",
        "caution": "凌晨 1–2 点出发下火山口；有硫磺毒气，必须戴防毒面具、跟向导行动；夜间寒冷，需备保暖衣物。",
        "coupling": "可从巴厘陆路 + 渡轮当地联游。强烈推荐与布罗莫(D1)串联为东爪哇 3–4 天火山走廊（布罗莫→宜珍→巴厘渡轮回），一程看两座世界级火山。",
        "video_q": "Ijen blue fire crater sulfur East Java night",
        "subspots": [
            {"id": "E1a", "zh": "蓝色火焰", "en": "Blue Fire", "q": "Ijen blue fire crater night", "desc": "火山口裂缝夜间的蓝色火焰，全球罕见。凌晨下火山口、有硫毒气，必须戴防毒面具跟向导，夜间寒冷，注意保暖。"},
            {"id": "E1b", "zh": "翠绿硫磺酸湖", "en": "Sulfur Crater Lake", "q": "Ijen crater acid lake sulfur", "desc": "火山口翠绿酸湖与扛硫矿工，工业感独特。气味刺鼻、边缘松软，沿向导路线走、勿靠近湖岸。"},
            {"id": "E1c", "zh": "硫磺矿工", "en": "Sulfur Miner", "q": "Ijen sulfur miner carrying baskets", "desc": "矿工徒手将上百斤明黄硫磺从火山口背出，是这座火山最震撼的人文一幕。近距离拍摄请礼貌征得同意、让出通道，毒气区务必戴面具跟向导。"},
            {"id": "E1d", "zh": "破晓火山口全景", "en": "Ijen Crater at Dawn", "q": "Kawah Ijen crater sunrise panorama", "desc": "天光渐亮、蓝焰隐去后，整座火山口显露出翠绿酸湖、明黄硫磺与缭绕烟雾的全景。沿火山口边缘观景，边缘松软有落石，随向导路线勿越界。"},
        ],
    },

    # ===== 龙目/吉利（备选线路） =====
    {
        "id": "F1", "region": "F", "zh": "吉利三岛 Gili", "en": "Gili Islands",
        "tags": ["海岛", "浮潜看海龟", "沙滩秋千"], "time": "2–3 天",
        "price": "往返快艇人均约 ¥350–600 + 浮潜团 ¥150–300",
        "feature": "Trawangan(派对)/Air(适中)/Meno(安静)三岛任选；岛上无机动车，只有自行车与马车；浮潜近距离看海龟、海底秋千与雕塑。",
        "caution": "岛上无警察、ATM 少、医疗有限，现金多备；浮潜留意水母与海流；跨海快艇遇风浪较颠。",
        "coupling": "与龙目岛同一线；三岛之间跳岛船 15–30 分钟。",
        "video_q": "Gili Islands Trawangan Lombok beach 4k",
        "subspots": [
            {"id": "F1a", "zh": "吉利岛海滩秋千", "en": "Gili Beach Swing", "q": "Gili Trawangan beach swing sunset", "desc": "海中木秋千，荡出去即是无边海景。岛上无机动车、骑车或马车可达，排队拍人像早去更好。"},
            {"id": "F1b", "zh": "海底雕塑/秋千", "en": "Underwater Statues", "q": "Gili Meno underwater statues Nest", "desc": "水下的人像雕塑与秋千，浮潜即可看。水母季留意蛰刺，跟船浮潜更安全，岛上现金多备。"},
        ],
    },
    {
        "id": "F2", "region": "F", "zh": "龙目岛南岸", "en": "South Lombok",
        "tags": ["海滩", "粉沙", "瀑布"], "time": "2–3 天",
        "price": "龙目包车分摊人均约 ¥80–130/天 + 粉色沙滩船程约 ¥50–100/人",
        "feature": "Kuta Lombok 冲浪、Tanjung Aan 粉沙海湾、Merese Hill 观景、Tiu Kelep/Sendang Gile 瀑布、东南部粉色沙滩。比巴厘更原始，游客也更少。",
        "caution": "景点分散、路况一般，需包车；粉色沙滩较偏远，含船程；防晒防中暑。",
        "coupling": "与吉利、林贾尼同属龙目一线，可组合安排。",
        "video_q": "South Lombok Tanjung Aan Merese Hill beach 4k",
        "subspots": [
            {"id": "F2a", "zh": "Tanjung Aan 粉沙海湾", "en": "Tanjung Aan Beach", "q": "Tanjung Aan beach Lombok", "desc": "细软粉沙与渐变蓝海的小海湾，比巴厘安静。景点分散需包车，正午晒，带遮阳与水。"},
            {"id": "F2b", "zh": "Tiu Kelep 瀑布", "en": "Tiu Kelep Waterfall", "q": "Tiu Kelep waterfall Lombok", "desc": "林中多层瀑布汇流，可走到水帘后。需走一段丛林步道，雨后湿滑，带换洗衣物与防滑鞋。"},
            {"id": "F2c", "zh": "龙目粉色沙滩 (Tangsi)", "en": "Pink Beach Lombok", "q": "Pink Beach Lombok Tangsi", "desc": "偏远海湾的淡粉沙，需乘船方可到达。路况一般、路远，防晒防中暑，退潮粉色更明显。"},
        ],
    },
    {
        "id": "F3", "region": "F", "zh": "林贾尼火山徒步", "en": "Mt Rinjani Trek",
        "tags": ["火山", "重装徒步"], "time": "2–3 天", "price": "2 天 1 夜团人均约 ¥800–1500",
        "feature": "Rinjani(3726m)火山口湖 + 温泉，印尼最经典的多日重装徒步之一，登顶日出云海十分震撼。",
        "caution": "难度高、需体力与向导；10 月仍为开放旺季且天气好，雨季关闭；夜间极冷，需备保暖装备。对 9–10 天行程来说偏重。",
        "coupling": "独立硬核项目，适合体力好的队员；结束后可下山前往吉利三岛放松。",
        "video_q": "Mount Rinjani trekking crater lake Lombok",
        "subspots": [
            {"id": "F3a", "zh": "火山口湖 Segara Anak", "en": "Segara Anak Lake", "q": "Mount Rinjani Segara Anak crater lake", "desc": "火山口内的翠蓝湖，旁有温泉可泡。位于多日重装徒步中段，需体力与向导，夜间寒冷，备好保暖装备。"},
            {"id": "F3b", "zh": "登顶日出云海", "en": "Summit Sunrise", "q": "Mount Rinjani summit sunrise Lombok", "desc": "登 3726m 顶看日出云海，视野开阔。难度高、夜行冷，需体能与向导，对 9–10 天行程来说偏重。"},
        ],
    },
]

# 第一章「最热门景点」成员 item id，按展示顺序。
# （原「精华速览」横滑卡已下线；此列表现仅用于判定第一章成员 + ★星标。）
HIGHLIGHTS = ["A1", "B1", "C1", "D1"]

COMBOS = [
    # ===== 9–10 天全程主线（10/2–10/11 完整窗口）=====
    {"no": "①", "name": "纯巴厘 + 佩尼达 9–10 天（最轻松）", "content": "A + B", "cross": "仅快艇 30–45 分",
     "days": "共 8–10 天（巴厘 7–8 + 佩尼达 1–2）", "budget": "¥1000–1800",
     "note": "零跨岛航班、节奏最舒服，适合想放松、不折腾的分队。"},
    {"no": "②", "name": "巴厘 + 佩尼达 + 科莫多 9–10 天（海岛天花板 🔥）", "content": "A + B + C", "cross": "飞机 1–1.5h",
     "days": "共 8–10 天（巴厘 4–5 + 佩尼达 1–2 + 科莫多 2–3）", "budget": "¥2500–4500",
     "note": "科莫多巨蜥 + Padar 三色海湾 + 粉色沙滩一次打包。科莫多船宿不建议选 4 天方案。推荐行程：Day1 落地巴厘→Day2–4 科莫多→Day5–6 佩尼达→Day7–9 乌布+南巴厘→Day10 返程。"},
    {"no": "③", "name": "巴厘 + 佩尼达 + 布罗莫 9–10 天（月球表面版）", "content": "A + B + D", "cross": "飞机 1h + 包车 3–4h",
     "days": "共 8–10 天（巴厘 5–6 + 佩尼达 1–2 + 布罗莫 2）", "budget": "¥2000–3500",
     "note": "用布罗莫替代科莫多：一座世界级火山 + 巴厘海岛，差异化体验拉满。推荐将布罗莫放在行程中段，前后留足休息。布罗莫需凌晨 3 点出发。"},
    {"no": "④", "name": "科莫多 + 佩尼达 + 乌布 + 布罗莫 9–10 天（终极全景 🔥 推荐）", "content": "A + B + C + D", "cross": "两段航班 + 包车",
     "days": "共 9–10 天（科莫多 2–3 + 佩尼达 1–2 + 巴厘 2–3 + 布罗莫 2）", "budget": "¥3500–6000",
     "note": "完整覆盖四大核心愿望！推荐行程：Day1 落地巴厘(DPS)→Day2 飞科莫多(LBJ)→Day3–4 科莫多跳岛→Day5 飞回巴厘→Day6 佩尼达一日→Day7–8 乌布+海神庙→Day9 飞泗水(SUB)转布罗莫→Day10 布罗莫日出→飞回巴厘→返程。全程 3 段航班、节奏紧凑但精心排布可从容走完。"},
    # ===== 6 天精简版（仅能走 6 天的队员，均含佩尼达一日游）=====
    {"no": "⑤", "name": "巴厘 + 佩尼达 6 天（最从容）", "content": "A + B", "cross": "仅快艇 30–45 分",
     "days": "共 6 天（巴厘 5 + 佩尼达 1）", "budget": "¥1000–1800",
     "note": "6 天玩巴厘精华 + 佩尼达一日跳岛，零航班不折腾。推荐行程：Day1 落地住南巴厘→Day2 佩尼达一日跳岛(精灵坠崖/破碎沙滩/浮潜)→Day3–4 乌布(梯田/猴林/圣泉庙)→Day5 南巴厘(情人崖/Kecak 火舞/金巴兰日落)+海神庙→Day6 返程。"},
    {"no": "⑥", "name": "巴厘 + 佩尼达 + 科莫多 6 天（海岛天花板）", "content": "A + B + C", "cross": "飞机 1–1.5h",
     "days": "共 6 天（巴厘 3 + 佩尼达 1 + 科莫多 2）", "budget": "¥2000–3800",
     "note": "6 天也能玩科莫多！巴厘留 3 天精华 + 佩尼达一日，飞纳闽巴霍 2 天跳岛看巨蜥 + 粉色沙滩 + Padar。推荐行程：Day1 落地巴厘→Day2 佩尼达一日跳岛→Day3 飞科莫多(LBJ)→Day4–5 科莫多跳岛→Day6 飞回巴厘返程。节奏紧凑但海岛天花板一次拿下。"},
    {"no": "⑦", "name": "巴厘 + 佩尼达 + 布罗莫 6 天（火山打卡）", "content": "A + B + D", "cross": "飞机 1h + 包车 3–4h",
     "days": "共 6 天（巴厘 3 + 佩尼达 1 + 布罗莫 2）", "budget": "¥1500–3000",
     "note": "6 天打卡世界级火山 + 佩尼达一日！巴厘留 3 天精华，飞泗水往返布罗莫看月球表面日出。推荐行程：Day1 落地巴厘→Day2 佩尼达一日跳岛→Day3 飞泗水(SUB)转布罗莫→Day4 布罗莫日出→飞回巴厘→Day5 乌布/南巴厘→Day6 返程。布罗莫需凌晨 3 点出发。"},
]

COMBO_HINT = "终极推荐 ④ 号线路：四大核心愿望一站满足，10 天走完科莫多+佩尼达+乌布+布罗莫。分段备选：如果布罗莫太赶改选 ②（科莫多+巴厘），如果不想跑科莫多改选 ③（布罗莫+巴厘），如果只想轻松度假改选 ①（纯巴厘+佩尼达）。只有 6 天的队员看 ⑤–⑦ 精简版：⑤ 巴厘+佩尼达最从容，⑥ 加科莫多，⑦ 加布罗莫。所有线路均含佩尼达一日跳岛。跨岛交通含门到门实际耗时约半天到 1 天，请将游玩天数相应压缩。"

PRICES = [
    ("巴厘门票 & 活动 (人均)", [
        ("德格拉朗梯田", "¥12（秋千另 ¥90–230）"), ("圣猴森林", "¥40"),
        ("Tirta Empul 圣泉庙", "¥35"), ("Tegenungan/Tibumana 瀑布", "¥10–12"),
        ("Ayung 河漂流", "¥250–350"), ("ATV 四驱越野", "¥250–400"),
        ("巴图尔火山日出徒步", "¥160–230"), ("Lempuyang 天堂之门", "¥25–50"),
        ("Besakih 母庙", "¥30–70"), ("水神庙 (Ulun Danu Beratan)", "¥35"),
        ("Handara Gate 拍照", "¥15"), ("Sekumpul 瀑布(含向导)", "¥45"),
        ("塔那罗海神庙", "¥30"), ("乌鲁瓦图庙", "¥25"), ("Kecak 火祭舞", "¥60–80"),
        ("金巴兰沙滩海鲜", "¥100–200"), ("Tirta Gangga 水宫", "¥25"),
        ("USS Liberty 沉船 浮潜/潜水", "¥100–150 / ¥350–500"),
    ]),
    ("包车 & 市内交通", [
        ("巴厘包车+司机(约10h)", "¥350–500/车/天（同行分摊≈¥60–90/人）"),
        ("机场接送", "¥100–150/车"), ("Grab/Gojek 市区", "¥15–40/程"),
    ]),
    ("跨岛交通 (人均往返)", [
        ("Sanur ⇆ 佩尼达 快艇", "¥120–200"), ("巴厘 ⇆ 吉利/龙目 快艇", "¥350–600"),
        ("巴厘(DPS) ⇆ 纳闽巴霍(LBJ) 机票", "¥600–1200"), ("巴厘(DPS) ⇆ 泗水(SUB) 机票", "¥400–800"),
        ("巴厘 ⇆ Banyuwangi 渡轮(宜珍)", "多含在宜珍团内"),
    ]),
    ("跟团 / 一日游 / 多日 (人均)", [
        ("佩尼达一日跳岛团(含快艇)", "¥250–450"), ("佩尼达蝠鲼/海龟浮潜", "¥200–400"),
        ("吉利浮潜团", "¥150–300"), ("林贾尼 2 天 1 夜徒步", "¥800–1500"),
        ("科莫多跳岛 1 日/2 日 1 夜", "¥300–500 / ¥600–1200"),
        ("科莫多船宿 2 天", "¥1500–3000+"), ("宜珍蓝火 2 天团", "¥500–900"),
        ("布罗莫吉普日出团", "¥150–250"),
    ]),
]

NOTES = [
    ("签证", "印尼对中国公民实行落地签(VOA)，停留期 30 天，9–10 天行程完全在范围内。抵达后办理即可，建议备好返程票与住宿信息。"),
    ("货币", "印尼盾(IDR)，小岛与村镇 ATM 少，多备现金、认准正规换汇点；大城市多数商户可刷卡。"),
    ("交通", "市区用 Grab/Gojek；巴厘常见『包车+司机』(几人同行分摊更划算)；跨岛靠快艇或航班，旺季务必提前订票。"),
    ("网络", "落地即买电话卡，Telkomsel 信号覆盖最好。"),
    ("健康", "防『巴厘肚』——只喝瓶装水、慎吃生冷；强防晒且用珊瑚友好防晒霜；常备晕船药与肠胃药。"),
    ("安全", "海滩看旗帜、防离岸流；火山务必听向导、备保暖与防毒面具；摩托事故高发，租车需国际驾照并确认保险。"),
    ("礼仪", "进寺庙须围纱笼、遮肩盖膝；宗教场合与传统仪式保持尊重。"),
    ("季节", "10 月为旱季尾/肩季，天气仍佳、宜海岛与火山，仍属旺季——热门船宿/徒步/潜水越早订越好。"),
]
