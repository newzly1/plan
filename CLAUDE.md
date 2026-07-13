# CLAUDE.md

印尼（巴厘岛及周边）6 人旅行选点投票项目。核心产物是网页 `webpage/dist/index.html`（外壳）+ `webpage/dist/images/*.webp`（图片，二者需同目录部署），供 6 人在浏览器里投票参考（纯 `localStorage`，无后端）。

## 项目结构
- `webpage/` — 网页源码与构建/部署管线，按功能分目录（**详见 `webpage/README.md`**）：
  - `src/` — 手改的构建源：`content.py`（内容源头）`style.css` `app.js` `tally.js` `identity.js` `build.py`
  - `data/` — 构建读取的 JSON：`media.json` `videos.json` `credits.json` `font.json`
  - `tools/` — 抓图/字体/验收流水线脚本
  - `assets/` — 保留的原始素材：`raw/` `vraw/` `review/` `image_sourcing/` `candidates.json`
  - `dist/` — 部署产物：`index.html` `images/` `cloudbase.js`（前两者由 build 生成，后者 vendored；勿整目录删）
  - `test/` — 单测
- `docs/` — 设计说明（`superpowers/specs`·`plans`）、`research/`（调研）、`archive/`（历史文档）
- ⚠️ **内容事实源头是 `webpage/src/content.py`**（不是 `docs/archive/印尼旅行项目投票清单.md`——那份已冻结于 2026-07-09、与现网页严重错位，仅存作早期背景）。

## 构建与部署
- 重新构建（改内容/样式/交互后）：`cd webpage && python3 src/build.py` → 生成 `dist/index.html` + `dist/images/*.webp`（只用 Python 标准库）
- 改哪个文件：内容 → `src/content.py`；样式 → `src/style.css`；投票/交互 → `src/app.js`；换图 → 见 `webpage/README.md`「重新抓取媒体」
- 部署到线上（国内可直连，链接不变），按改动范围挑：
  - `cd webpage && tcb hosting deploy dist/images images -e plan-d0gstt7r6507aa319`（图片变化时）
  - `cd webpage && tcb hosting deploy dist/index.html index.html -e plan-d0gstt7r6507aa319`（文字/样式/交互变化时）
  - 换同一景点 key 下的单张图，只需重部署那一个文件，无需碰 `index.html`：`tcb hosting deploy dist/images/<key>.webp images/<key>.webp -e plan-d0gstt7r6507aa319`
  - `cd webpage && tcb hosting deploy dist/cloudbase.js cloudbase.js -e plan-d0gstt7r6507aa319`（vendored SDK 变更时才需要，一般首次一次即可）
- 正式访问链接（发给 6 人、国内无需梯子）：https://plan-d0gstt7r6507aa319-1451599494.tcloudbaseapp.com
- ⚠️ CloudBase 免费体验环境 **2027-01-08 到期**，到期前须在 [控制台](https://console.cloud.tencent.com/tcb) 手动续 6 个月，否则环境销毁、链接失效（不支持自动续费）。
- 投票已接入 CloudBase 云数据库实时汇总（集合 `votes`，匿名登录，安全规则 `{ "read": true, "write": "auth.uid != null" }`——人人可读、已登录即可写）：改汇总算法看 `webpage/src/tally.js`，改同步/渲染看 `webpage/src/app.js` 里的 `cloud` 模块与 `renderTally`/`refreshTally`；详细数据流与控制台配置见 `webpage/README.md`「投票实时汇总（CloudBase 云数据库）」一节。⚠️ SDK 必须用 **v2.31.0（`dist/cloudbase.js`，全局 `cloudbase`）**、登录用 `auth.signInAnonymously()`；本环境已停用 v1.x 旧匿名登录（会报 `ACCESS_TOKEN_DISABLED`）。规则勿用 `doc._openid == auth.openid`（匿名用户无 openid，会全拒）。
- 单测：`node --test webpage/test/tally.test.js`（零依赖，Node 内置）。

## 环境与注意事项
- **npm 会卡**：本机默认源 `registry.npmjs.org` 联网卡住；装包一律加 `--registry=https://registry.npmmirror.com`（国内镜像）。同理 `urllib` 也卡，脚本联网抓取用 `curl`（走本地代理）。
- **CloudBase CLI**：`@cloudbase/cli`（命令 `tcb`）已全局安装；登录用 `tcb login --flow device`（设备码，浏览器/手机扫码授权，不需交任何密钥）。
- **Git**：远端为 GitHub `git@github.com:newzly1/plan.git`（SSH）；本机未配全局身份，提交作者沿用 `zly1 <10994824+zly21@user.noreply.gitee.com>`（仓库局部配置）；提交信息用中文。
