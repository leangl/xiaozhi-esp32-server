# Web search plugin guide

## Features

The `web_search` plugin searches online during a conversation and returns results. Choose one of three providers: Metaso, Tavily, or Serply.

The original provider descriptions list 1,000 free Tavily requests per month, strong China-focused sources for Metaso, and a 2,500-request signup allowance for Serply, which returns Google results and charges after the allowance. These are provider-controlled allowances, not guarantees from this project.

## Obtain an API key

### Metaso

Register and sign in at [Metaso Search API](https://metaso.cn/search-api/api-keys). In API key management, select **Create New Key** and copy the key, which starts with `mk-`.

### Tavily

Register and sign in at the [Tavily console](https://app.tavily.com/home). Create an API key and copy it; it starts with `tvly-`.

### Serply

Register and sign in at [Serply](https://serply.io), create an API key in the console, and copy it. See the [Serply documentation](https://serply.io/docs) for its API.

## Configuration

### Method 1: Management console (recommended)

Sign in, open **Configure Role**, and select an agent. Select **Edit Functions**, find **Web Search** in the right-hand parameter area, and enable it. Set the provider to `metaso`, `tavily`, or `serply` and enter that provider's API key. Save the function configuration, then save the agent.

### Method 2: Server-only deployment

Set `provider` and `api_key` in `data/.config.yaml`. The original placeholder `你的API Key` means “your API key”; replace it with your key.

```yaml
plugins:
  web_search:
    provider: "metaso"
    api_key: "你的API Key"
```

To customize the number of results or the tool description, add `max_results` and `description`:

```yaml
plugins:
  web_search:
    provider: "metaso"
    description: "Web search tool. Use this tool when the user explicitly needs an online search."
    max_results: 5
    api_key: "你的API Key"
```

Ensure that `web_search` appears in the `functions` list:

```yaml
plugins:
  functions:
    - web_search
```

Restart the service after configuring it.
