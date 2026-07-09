# CLAUDE.md

印尼（巴厘岛及周边）6 人旅行选点投票项目。核心产物是网页 `webpage/index.html`（外壳）+ `webpage/images/*.webp`（图片，二者需同目录部署），供 6 人在浏览器里投票参考（纯 `localStorage`，无后端）。

## 项目结构
- `印尼旅行项目投票清单.md` — 内容源头，所有文字由此转写进 `webpage/content.py`
- `webpage/` — 网页源码与构建/部署管线，**详见 `webpage/README.md`**
- `docs/` — 设计说明

## 构建与部署
- 重新构建（改内容/样式/交互后）：`cd webpage && python3 build.py` → 生成 `index.html` + `images/*.webp`（只用 Python 标准库）
- 改哪个文件：内容 → `content.py`；样式 → `style.css`；投票/交互 → `app.js`；换图 → 见 `webpage/README.md`「重新抓取媒体」
- 部署到线上（国内可直连，链接不变），按改动范围挑：
  - `cd webpage && tcb hosting deploy images images -e plan-d0gstt7r6507aa319`（图片变化时）
  - `cd webpage && tcb hosting deploy index.html index.html -e plan-d0gstt7r6507aa319`（文字/样式/交互变化时）
  - 换同一景点 key 下的单张图，只需重部署那一个文件，无需碰 `index.html`：`tcb hosting deploy images/<key>.webp images/<key>.webp -e plan-d0gstt7r6507aa319`
- 正式访问链接（发给 6 人、国内无需梯子）：https://plan-d0gstt7r6507aa319-1451599494.tcloudbaseapp.com
- ⚠️ CloudBase 免费体验环境 **2027-01-08 到期**，到期前须在 [控制台](https://console.cloud.tencent.com/tcb) 手动续 6 个月，否则环境销毁、链接失效（不支持自动续费）。

## 环境与注意事项
- **npm 会卡**：本机默认源 `registry.npmjs.org` 联网卡住；装包一律加 `--registry=https://registry.npmmirror.com`（国内镜像）。同理 `urllib` 也卡，脚本联网抓取用 `curl`（走本地代理）。
- **CloudBase CLI**：`@cloudbase/cli`（命令 `tcb`）已全局安装；登录用 `tcb login --flow device`（设备码，浏览器/手机扫码授权，不需交任何密钥）。
- **Git**：远端为 GitHub `git@github.com:newzly1/plan.git`（SSH）；本机未配全局身份，提交作者沿用 `zly1 <10994824+zly21@user.noreply.gitee.com>`（仓库局部配置）；提交信息用中文。
