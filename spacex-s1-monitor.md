# # SpaceX S-1 监控系统
"请按迭代方式实现：先只实现 SEC EDGAR API 监控 + Telegram 推送 + SQLite 去重，能跑通就算 V1。新闻源和心跳机制等 V2 再加。"
## 项目目标

当 SpaceX 向 SEC 公开提交 S-1 注册声明（或后续修订版本）时，
在 5 分钟内通过 Telegram 向我推送通知。

此信号是我交易 RKLB（Rocket Lab）的关键触发点——SpaceX 
public S-1 发布后，proxy trade 会达到峰值，我会在此信号
触发时开始卖 RKLB Covered Call。

## 背景信息

- SpaceX 已于 2026-04-01 提交 confidential S-1（仅 SEC 内部可见）
- 根据 SEC 规则，公司必须在路演前至少 15 天公开 S-1
- 市场预期路演 2026 年 6 月初，上市 6-7 月
- 因此 public S-1 预计在 2026 年 5 月中旬前后发布
- **关键信号是 public S-1，不是 confidential S-1**

## 数据源（按优先级）

### 1. SEC EDGAR Full-Text Search API（主要）
- 端点：https://efts.sec.gov/LATEST/search-index?q=%22SpaceX%22&forms=S-1
- 备用查询：q=%22Space+Exploration+Technologies%22&forms=S-1
- 轮询频率：
  - 交易日 9:00 AM - 6:00 PM ET：每 5 分钟
  - 非交易时段和周末：每 30 分钟
- SpaceX 法人注册名可能为以下之一，全部监控：
  - "SpaceX"
  - "Space Exploration Technologies Corp"
  - "Space Exploration Technologies"

### 2. SEC EDGAR Company Filings RSS（备用 1）
- 一旦 SpaceX 出现在 EDGAR 公司数据库，获取其 CIK
- 订阅 CIK 的 RSS feed：
  https://www.sec.gov/cgi-bin/browse-edgar?action=getcompany&CIK={CIK}&type=S-1&dateb=&owner=include&count=40&output=atom
- 监控 form types：S-1, S-1/A, 424B1, 424B2, 424B3, 424B4, 424B5

### 3. 新闻源（备用 2）
- Google News RSS: 
  https://news.google.com/rss/search?q=%22SpaceX%22+%22S-1%22+IPO
- NewsAPI.org（如有 API key）
- 关键词组合：("SpaceX" OR "Space Exploration Technologies") 
  AND ("S-1" OR "IPO filing" OR "registration statement" OR "public filing")
- 排除关键词："satellite", "Starship test", "rocket launch"
  （避免无关新闻）
- 来源优先级（白名单）：
  - reuters.com
  - bloomberg.com
  - wsj.com
  - ft.com
  - cnbc.com
  - sec.gov
  - techcrunch.com

## 推送通道

### 主要通道：Telegram Bot
- 创建一个 Telegram Bot（通过 @BotFather）
- 获取 BOT_TOKEN 和我的 CHAT_ID
- 使用 sendMessage API 推送
- 支持 Markdown 格式

### 备用通道（可选）
- 邮件（SMTP，Gmail）
- iOS Push（通过 ntfy.sh 或 Pushover）

一次事件触发所有已配置的通道。

## 推送内容模板
🚨 SPACEX S-1 ALERT 🚨
Time: {timestamp ET}Source: {SEC EDGAR / News source name}Filing Type: {S-1 / S-1/A / 424B* / News article}URL: {direct link}
Excerpt (first 300 chars):{filing description or article lead}
---
Action items:
1. 立即查看 SEC EDGAR 确认真实性
2. 观察 RKLB 盘中反应
3. 按计划启动第一批 Call 卖出

```
## 去重逻辑 - 使用 SQLite 存储已通知的事件 - 表结构： ```sql CREATE TABLE notifications ( id INTEGER PRIMARY KEY, source TEXT, identifier TEXT UNIQUE, -- filing accession number 或 news URL title TEXT, notified_at TIMESTAMP, content TEXT ); ``` - SEC filings 用 accession number 去重 - 新闻用 URL 去重（URL 清洗后：去除 utm 参数等） - 去重窗口：永久（不重复推送同一事件） ## 系统健康监控 ### 心跳机制 - 每周日 UTC 10:00 发送一次心跳消息 - 内容：
```

✅ SpaceX S-1 Monitor - Weekly Heartbeat
系统运行正常本周轮询次数：{count}最新检查时间：{last_check_time}去重数据库条目数：{db_rows}
SpaceX 状态：未发现 public S-1
下次心跳：{next_sunday}

```
### 异常告警 - 连续 3 次 API 请求失败：立即推送"系统异常" - 数据库连接失败：立即推送 - 任何未捕获异常：立即推送 + stack trace ## 部署方案 ### 推荐：GitHub Actions（免费，无需服务器） workflow 文件 `.github/workflows/monitor.yml`： ```yaml name: SpaceX S-1 Monitor on: schedule: # 交易时段每 5 分钟（美东 9am-6pm = UTC 13:00-22:00） - cron: '*/5 13-22 * * 1-5' # 其他时段每 30 分钟 - cron: '*/30 0-12,23 * * *' - cron: '*/30 * * * 0,6' workflow_dispatch: # 支持手动触发 jobs: monitor: runs-on: ubuntu-latest steps: - uses: actions/checkout@v4 - uses: actions/setup-python@v5 with: python-version: '3.11' - run: pip install -r requirements.txt - env: TELEGRAM_BOT_TOKEN: ${{ secrets.TELEGRAM_BOT_TOKEN }} TELEGRAM_CHAT_ID: ${{ secrets.TELEGRAM_CHAT_ID }} run: python monitor.py - name: Commit DB changes run: | git config user.name github-actions git config user.email github-actions@github.com git add notifications.db git diff --staged --quiet || git commit -m "Update DB" git push ``` ### 备选部署方案 - **Cloudflare Workers**：免费层 100k requests/day 足够 - **个人 VPS**：用 cron 定期执行 - **Vercel Cron**：免费层够用 **不要用本地电脑跑**——电脑关机就错过信号。 ## 环境变量（GitHub Secrets） 在 GitHub repo Settings → Secrets 添加： - `TELEGRAM_BOT_TOKEN` - `TELEGRAM_CHAT_ID` - `NEWSAPI_KEY`（可选） - `PUSHOVER_TOKEN`（可选） ## 技术栈 - Python 3.11+ - `requests` - HTTP 请求 - `feedparser` - RSS 解析 - `python-telegram-bot` 或直接用 requests - `sqlite3` - 内置，去重存储 - `beautifulsoup4` - 解析 EDGAR HTML（如需要） ## 文件结构
```

spacex-monitor/├── monitor.py              # 主脚本入口├── sources/│   ├── **init**.py│   ├── sec_edgar.py        # SEC EDGAR API│   ├── sec_rss.py          # SEC RSS feed│   └── news.py             # News sources├── notifiers/│   ├── **init**.py│   └── telegram.py         # Telegram 推送├── db.py                   # SQLite 去重逻辑├── config.py               # 配置常量├── requirements.txt├── notifications.db        # SQLite 数据库（自动生成）└── .github/└── workflows/└── monitor.yml
```
## 代码质量要求 - 每个 source 是独立模块，失败不影响其他 source - 所有 HTTP 请求必须设置 timeout（默认 10 秒） - 日志用 Python logging 模块，级别默认 INFO - 异常必须捕获并推送告警，不能让 GitHub Action 静默失败 - 每次运行时间 < 2 分钟（GitHub Actions 免费层限制） ## 测试计划 1. **单元测试**：每个 source 用 mock 数据测试解析 2. **端到端测试**： - 添加"Apple"作为测试关键词 - 运行系统，应触发推送 - 确认 Telegram 收到消息 - 移除测试关键词 3. **去重测试**：连续运行两次，第二次不应推送 4. **异常测试**：人为让 API 超时，应收到"系统异常"通知 ## 后续扩展（V2 规划） 此 V1 完成后，后续会添加： - RKLB IV30 和 IV Rank 监控 - RKLB 股价和成交量异常检测 - Weekly 综合周报（整合以上所有信号） V1 代码架构要为 V2 预留扩展点： - 通知模块解耦（将来可被 IV 监控复用） - 数据库表结构支持多种事件类型 - GitHub Actions workflow 支持多个监控任务 ## 交付时我需要什么 1. 完整可运行的代码 2. README.md 包含： - 创建 Telegram Bot 的步骤 - 获取 CHAT_ID 的步骤 - GitHub Secrets 配置步骤 - 手动触发测试的步骤 3. 一次手动运行的 demo（展示日志和预期输出） ## 关键提醒（务必不要遗漏） - 监控的是 **public S-1**，不是 confidential S-1 - Confidential filing 在 EDGAR 对外不可见，无法监控 - 真正的触发信号是 SpaceX 把 confidential 转为 public - 如果 SpaceX 最终以 Form DRS（草案注册声明）方式公开，也要识别 - 所有时间戳必须是美东时间（ET），便于对照市场反应
```