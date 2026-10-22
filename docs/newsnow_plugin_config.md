# News source configuration for get_news_from_newsnow

## Overview

Configure each agent's news sources in the management console without editing plugin code.

## Configuration

### 1. Web console (recommended)

Sign in, open **Role Configuration**, select an agent, and click **Edit Functions**. In the right-hand parameters, find **NewsNow News Aggregation**. Enter semicolon-separated Chinese source names in **News Source Configuration**.

### 2. Configuration file

Set these values in `config.yaml`:

```yaml
plugins:
  get_news_from_newsnow:
    url: "https://newsnow.busiyi.world/api/s?id="
    news_sources: "澎湃新闻;百度热搜;财联社;微博;抖音"
```

## Source name format

Use Chinese names separated by ASCII semicolons:

```
中文名称1;中文名称2;中文名称3
```

The placeholder format means “Chinese name 1;Chinese name 2;Chinese name 3”. Example:

```
澎湃新闻;百度热搜;财联社;微博;抖音;知乎;36氪
```

## Supported sources

The exact Chinese names below are compatibility values from `CHANNEL_MAP`, not prose to translate in configuration. English labels explain each value:

- `澎湃新闻`: The Paper
- `百度热搜`: Baidu trending searches
- `财联社`: Cailian Press
- `微博`: Weibo
- `抖音`: Douyin
- `知乎`: Zhihu
- `36氪`: 36Kr
- `华尔街见闻`: Wallstreetcn
- `IT之家`: IT Home
- `今日头条`: Toutiao
- `虎扑`: Hupu
- `哔哩哔哩`: Bilibili
- `快手`: Kuaishou
- `雪球`: Xueqiu
- `格隆汇`: Gelonghui
- `法布财经`: Fabu Finance
- `金十数据`: Jin10 Data
- `牛客`: Nowcoder
- `少数派`: Sspai
- `稀土掘金`: Juejin
- `凤凰网`: iFeng
- `虫部落`: Chongbuluo
- `联合早报`: Lianhe Zaobao
- `酷安`: Coolapk
- `远景论坛`: PCbeta forum
- `参考消息`: Reference News
- `卫星通讯社`: Sputnik
- `百度贴吧`: Baidu Tieba
- `靠谱新闻`: Kaopu News

The plugin supports additional sources defined in its map.

## Default configuration

If you do not configure sources, the plugin uses The Paper, Baidu trending searches, and Cailian Press:

```
澎湃新闻;百度热搜;财联社
```

## Usage

1. Configure the Chinese source names in the console or file, separated with semicolons.
2. Ask for news. Chinese speech fixtures `播报新闻` and `获取新闻` mean “read the news” and “get news”.
3. Name a source: `播报澎湃新闻` means “read The Paper news”; `获取百度热搜` means “get Baidu trending searches”.
4. Ask for details: `详细介绍这条新闻` means “explain this news item in detail”.

## How it works

The plugin accepts a Chinese name such as `澎湃新闻`, maps it to its API ID such as `thepaper`, calls the API with that ID, and returns the news.

## Notes

Names must match `CHANNEL_MAP` exactly. Restart the service or reload configuration after changes. Invalid sources fall back to the defaults. Use ASCII `;`, not the full-width Chinese semicolon `；`; the latter remains here as an invalid-input example.
