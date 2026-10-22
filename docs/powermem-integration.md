# PowerMem memory integration

## Introduction

[PowerMem](https://www.powermem.ai/) is an open-source agent memory component from OceanBase. It uses an LLM to summarize/extract memories and semantic retrieval to manage them.

PowerMem itself is free/open-source; costs depend on your LLM, embedding service, and database. The original guide describes SQLite with a free LLM such as Zhipu glm-4-flash as a free option. Cloud LLM/database providers apply their own charges; confirm embedding costs too.

The original guide recommends OceanBase for performance and SQLite when resources are limited.

- [GitHub](https://github.com/oceanbase/powermem)
- [Website](https://www.powermem.ai/)
- [Examples](https://github.com/oceanbase/powermem/tree/main/examples)

## Features

- Local memory summarization/extraction through an LLM.
- `UserMemory` profiles that extract names, occupations, interests, and other user information and update it across conversations.
- Forgetting of stale/noisy information based on an Ebbinghaus-style forgetting curve.
- OceanBase (recommended), SeekDB (recommended for integrated AI storage), PostgreSQL, and lightweight SQLite backends.
- Qwen, Zhipu (including glm-4-flash), OpenAI, and other LLMs.
- Vector-based semantic retrieval, private/local deployment, and asynchronous memory operations.

## Installation

PowerMem is included in the project dependencies. To install it manually:

```bash
pip install powermem
```

## Configuration

### Basic configuration

In `config.yaml`:

```yaml
selected_module:
  Memory: powermem

Memory:
  powermem:
    type: powermem
    # Enable user profiles
    # User profiles support oceanbase, seekdb, sqlite (powermem 0.3.0+)
    enable_user_profile: true
    
    # ========== LLM configuration ==========
    llm:
      provider: openai  # Options include qwen, openai, zhipu
      config:
        api_key: 你的LLM API密钥
        model: qwen-plus
        # openai_base_url: https://api.openai.com/v1  # Optional custom service URL
    
    # ========== Embedding configuration ==========
    embedder:
      provider: openai  # Options include qwen, openai
      config:
        api_key: 你的嵌入模型API密钥
        model: text-embedding-v4
        openai_base_url: https://dashscope.aliyuncs.com/compatible-mode/v1
        # embedding_dims: 1024  # Set vector dimensions if different from 1536
    
    # ========== Database configuration ==========
    vector_store:
      provider: sqlite  # Options: oceanbase (recommended), seekdb (recommended), postgres, sqlite (lightweight)
      config: {}  # SQLite needs no additional configuration
```

The exact original placeholders `你的LLM API密钥` and `你的嵌入模型API密钥` mean “your LLM API key” and “your embedding-model API key”. Replace them with the corresponding keys.

### Parameter reference

| Setting | Meaning | Values |
| --- | --- | --- |
| `llm.provider` | LLM provider | qwen, openai, zhipu, etc. |
| `llm.config.api_key` | LLM API key | Provider key |
| `llm.config.model` | LLM model name | Provider-dependent |
| `llm.config.openai_base_url` | Optional custom service URL | URL |
| `embedder.provider` | Embedding provider | qwen, openai, etc. |
| `embedder.config.api_key` | Embedding API key | Provider key |
| `embedder.config.model` | Embedding model name | Provider-dependent |
| `embedder.config.openai_base_url` | Optional custom embedding URL | URL |
| `vector_store.provider` | Database backend | oceanbase / seekdb (recommended), postgres, sqlite (lightweight) |
| `vector_store.config` | Connection settings | Backend-dependent |

### Memory modes

| Mode | Setting | Behavior | Storage |
| --- | --- | --- | --- |
| Standard memory | `enable_user_profile: false` | Store/retrieve conversation memory | All supported databases |
| User profiles | `enable_user_profile: true` | Memory plus extracted user profiles | oceanbase, seekdb, sqlite |

PowerMem 0.3.0+ supports user profiles with OceanBase, SeekDB, and SQLite.

### Qwen (recommended in the original guide)

Register at [Alibaba Bailian](https://bailian.console.aliyun.com/), obtain a key in [API Key Management](https://bailian.console.aliyun.com/?apiKey=1#/api-key), and configure:

```yaml
Memory:
  powermem:
    type: powermem
    enable_user_profile: true
    llm:
      provider: qwen
      config:
        api_key: sk-xxxxxxxxxxxxxxxx
        model: qwen-plus
    embedder:
      provider: openai
      config:
        api_key: sk-xxxxxxxxxxxxxxxx
        model: text-embedding-v4
        openai_base_url: https://dashscope.aliyuncs.com/compatible-mode/v1
    vector_store:
      provider: sqlite
      config: {}
```

### Zhipu free-LLM configuration

Register at [Zhipu AI](https://bigmodel.cn/), obtain a key from [API Keys](https://bigmodel.cn/usercenter/proj-mgmt/apikeys), and use the original glm-4-flash/SQLite example below. The original guide calls this fully free; provider pricing and embedding availability remain outside this project's control.

```yaml
Memory:
  powermem:
    type: powermem
    enable_user_profile: true
    llm:
      provider: openai  # Use OpenAI-compatible mode
      config:
        api_key: xxxxxxxxxxxxxxxx.xxxxxxxxxxxxxxxx
        model: glm-4-flash
        openai_base_url: https://open.bigmodel.cn/api/paas/v4/
    embedder:
      provider: openai
      config:
        api_key: xxxxxxxxxxxxxxxx.xxxxxxxxxxxxxxxx
        model: embedding-3
        openai_base_url: https://open.bigmodel.cn/api/paas/v4/
    vector_store:
      provider: sqlite
      config: {}
```

### OpenAI

```yaml
Memory:
  powermem:
    type: powermem
    enable_user_profile: true
    llm:
      provider: openai
      config:
        api_key: sk-xxxxxxxxxxxxxxxx
        model: gpt-4o-mini
        openai_base_url: https://api.openai.com/v1
    embedder:
      provider: openai
      config:
        api_key: sk-xxxxxxxxxxxxxxxx
        model: text-embedding-3-small
        openai_base_url: https://api.openai.com/v1
    vector_store:
      provider: sqlite
      config: {}
```

### OceanBase (performance-oriented configuration)

Deploy [open-source OceanBase](https://github.com/oceanbase/oceanbase) or use its [cloud service](https://www.oceanbase.com/), then configure:

```yaml
Memory:
  powermem:
    type: powermem
    enable_user_profile: true
    llm:
      provider: qwen
      config:
        api_key: sk-xxxxxxxxxxxxxxxx
        model: qwen-plus
    embedder:
      provider: openai
      config:
        api_key: sk-xxxxxxxxxxxxxxxx
        model: text-embedding-v4
        openai_base_url: https://dashscope.aliyuncs.com/compatible-mode/v1
    vector_store:
      provider: oceanbase
      config:
        host: 127.0.0.1
        port: 2881
        user: root@test
        password: your_password
        db_name: powermem
        collection_name: memories  # Default value
        embedding_model_dims: 1536  # Embedding vector dimensions (required)
```

## Device memory isolation

PowerMem uses `device_id` as `user_id`. Each device has its own memory space, and conversations on the same device share memory context.

## UserMemory profiles

The `UserMemory` class extracts user profiles from conversations. With PowerMem 0.3.0+, use OceanBase, SeekDB, or SQLite.

### Enable profiles

Set `enable_user_profile: true`:

```yaml
Memory:
  powermem:
    type: powermem
    enable_user_profile: true  # Enable user profiles
    llm:
      provider: qwen
      config:
        api_key: sk-xxxxxxxxxxxxxxxx
        model: qwen-plus
    embedder:
      provider: openai
      config:
        api_key: sk-xxxxxxxxxxxxxxxx
        model: text-embedding-v4
        openai_base_url: https://dashscope.aliyuncs.com/compatible-mode/v1
    vector_store:
      provider: sqlite  # User profiles support oceanbase, seekdb, sqlite
      config: {}
```

### Profile behavior

| Capability | Description |
| --- | --- |
| Extraction | Extract names, ages, occupations, interests, etc. from conversations |
| Updates | Refine the profile as conversations continue |
| Retrieval | Combine profile information with memory search for relevance |
| Forgetting | Reduce the weight of stale information using the forgetting curve |

When querying memory with profiles enabled, Xiaozhi receives the user's basic information/interests and relevant historical memories.

## Comparison with other memory components

| Feature | PowerMem | mem0ai | mem_local_short |
| --- | --- | --- | --- |
| Operation | Local summarization | Cloud API | Local summarization |
| Storage | Local/cloud database | Cloud | Local YAML |
| Cost | Depends on LLM/database | Original allowance: 1,000 requests/month | Free |
| Retrieval | Vector search | Vector search | Returns all memories |
| User profiles | UserMemory | No | No |
| Forgetting | Forgetting curve | No | No |
| Private deployment | Supported | Cloud only | Supported |
| Databases | OceanBase (recommended), SeekDB, PostgreSQL, SQLite | Not applicable | YAML files |

## Troubleshooting

### 1. API key errors

For `API key is required`, check that `llm_api_key` and `embedding_api_key` are populated and valid. These are the option names used in the original troubleshooting notes; compare them with the nested configuration above for your installed version.

### 2. Model not found

Check `llm_model` and `embedding_model` names and confirm the provider has enabled the corresponding services.

### 3. Connection timeouts

Check network connectivity. For proxy/custom routing, configure `llm_base_url` and `embedding_base_url` as appropriate for your installed integration.

## Import checks

In the virtual environment:

```bash
# Activate the virtual environment
source .venv/bin/activate

# Test the PowerMem import
python -c "from powermem import AsyncMemory; print('PowerMem imported successfully')"

# Test the UserMemory import (user profiles)
python -c "from powermem import UserMemory; print('UserMemory imported successfully')"
```

## Resources

- [PowerMem documentation](https://www.powermem.ai/)
- [PowerMem repository](https://github.com/oceanbase/powermem)
- [PowerMem examples](https://github.com/oceanbase/powermem/tree/main/examples)
- [OceanBase website](https://www.oceanbase.com/)
- [OceanBase repository](https://github.com/oceanbase/oceanbase)
- [SeekDB repository](https://github.com/oceanbase/seekdb), an AI-native search database
- [Alibaba Bailian](https://bailian.console.aliyun.com/)

