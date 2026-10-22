# RAGFlow integration

This guide covers deploying RAGFlow and connecting it to the management console. If you already run RAGFlow, skip to part 2. Part 1 shares MySQL and Redis with `xiaozhi-esp32-server` to reduce resource use.

# Part 1: Deploy RAGFlow

The Compose examples below are illustrative fragments. Their `...` markers mean omitted settings; apply each change to the full existing file rather than parsing the fragment as standalone YAML.

## Step 1: Check MySQL and Redis

You can reuse the services from a management-console deployment. Test host access:

``` shell
telnet 127.0.0.1 3306

telnet 127.0.0.1 6379
```

If ports 3306 and 6379 are reachable, continue to step 2. Otherwise, check network isolation. For services installed through `docker-compose_all.yml`, change the original fragment:

``` yaml
  xiaozhi-esp32-server-db:
    ...
    networks:
      - default
    expose:
      - "3306:3306"
  xiaozhi-esp32-server-redis:
    ...
    expose:
      - 6379
```

to:

``` yaml
  xiaozhi-esp32-server-db:
    ...
    networks:
      - default
    ports:
      - "3306:3306"
  xiaozhi-esp32-server-redis:
    ...
    ports:
      - "6379:6379"
```

This replaces `expose` with `ports` for both services. The original restart commands are:

``` shell
# Enter the directory containing docker-compose_all.yml, e.g. xiaozhi-server
cd xiaozhi-server
docker compose -f docker-compose_all.yml down
docker compose -f docker-compose.yml up -d
```

The original example shuts down with `docker-compose_all.yml` but starts with `docker-compose.yml`; verify which file your deployment needs. This translation preserves the commands rather than changing deployment behavior.

Retest:

``` shell
telnet 127.0.0.1 3306

telnet 127.0.0.1 6379
```

## Step 2: Create the database and user

Create database/user `rag_flow` with the original example password `infini_rag_flow`:

``` sql
-- Create the database
CREATE DATABASE IF NOT EXISTS rag_flow CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

-- Create the user and grant access
CREATE USER IF NOT EXISTS 'rag_flow'@'%' IDENTIFIED BY 'infini_rag_flow';
GRANT ALL PRIVILEGES ON rag_flow.* TO 'rag_flow'@'%';

-- Refresh privileges
FLUSH PRIVILEGES;
```

## Step 3: Download RAGFlow

Choose a parent directory, such as `/home/system/xiaozhi`. This guide uses `v0.22.0`:

```
git clone https://ghfast.top/https://github.com/infiniflow/ragflow.git
cd ragflow
git checkout v0.22.0
```

Enter its Docker directory:

``` shell
cd docker
```

In `ragflow/docker/docker-compose.yml`, remove `depends_on` from `ragflow-cpu` and `ragflow-gpu` to decouple them from the bundled MySQL.

Before:

``` yaml
  ragflow-cpu:
    depends_on:
      mysql:
        condition: service_healthy
    profiles:
      - cpu
  ...
  ragflow-gpu:
    depends_on:
      mysql:
        condition: service_healthy
    profiles:
      - gpu
```

After:

``` yaml
  ragflow-cpu:
    profiles:
      - cpu
  ...
  ragflow-gpu:
    profiles:
      - gpu
```

In `ragflow/docker/docker-compose-base.yml`, remove the bundled `mysql` and `redis` services.

Before:

``` yaml
services:
  minio:
    image: quay.io/minio/minio:RELEASE.2025-06-13T11-33-47Z
    ...
  mysql:
    image: mysql:8.0
    ...
  redis:
    image: redis:6.2-alpine
    ...
```

After:

``` yaml
services:
  minio:
    image: quay.io/minio/minio:RELEASE.2025-06-13T11-33-47Z
    ...
```

## Step 4: Configure environment variables

Edit `ragflow/docker/.env`. Find and change each setting below. **Add `MYSQL_USER` if absent**; missing it can prevent startup.

``` env
# Port settings
SVR_WEB_HTTP_PORT=8008           # HTTP port
SVR_WEB_HTTPS_PORT=8009          # HTTPS port
# MySQL configuration: use your local MySQL settings
MYSQL_HOST=host.docker.internal  # Let containers access host services through host.docker.internal
MYSQL_PORT=3306                  # Local MySQL port
MYSQL_USER=rag_flow              # User created above; add this setting if absent
MYSQL_PASSWORD=infini_rag_flow   # Password set above
MYSQL_DBNAME=rag_flow            # Database name

# Redis configuration: use your local Redis settings
REDIS_HOST=host.docker.internal  # Let containers access host services through host.docker.internal
REDIS_PORT=6379                  # Local Redis port
REDIS_PASSWORD=                  # Leave empty for passwordless Redis; otherwise enter its password
```

If your Redis has no password, also edit `ragflow/docker/service_conf.yaml.template` to remove the `infini_rag_flow` password fallback.

Before:

``` shell
redis:
  db: 1
  password: '${REDIS_PASSWORD:-infini_rag_flow}'
  host: '${REDIS_HOST:-redis}:6379'
```

After:

``` shell
redis:
  db: 1
  password: '${REDIS_PASSWORD:-}'
  host: '${REDIS_HOST:-redis}:6379'
```

## Step 5: Start RAGFlow

``` shell
docker-compose -f docker-compose.yml up -d
```

Check `docker logs -n 20 -f docker-ragflow-cpu-1` for startup errors.

# Step 5: Register an account

Open `http://127.0.0.1:8008`, click **Sign Up**, create an account, then **Sign In**. To disable further registrations, set this in `ragflow/docker/.env`:

``` dotenv
REGISTER_ENABLED=0
```

Restart after changing it:

``` shell
docker-compose -f docker-compose.yml down
docker-compose -f docker-compose.yml up -d
```

# Step 6: Configure RAGFlow models

Sign in at `http://127.0.0.1:8008` and open settings through the avatar at the upper right. Select **Model Providers** in the left navigation. Under **Available Models**, select **LLM**, choose your provider, click **Add**, and enter its API key.

Repeat for **TEXT EMBEDDING**. Refresh the page, then choose the LLM and embedding model under **Set Default Models**. Ensure the key has access to each model; some providers require a purchased resource package for embeddings.

# Part 2: Connect RAGFlow to Xiaozhi

# Step 1: Create a RAGFlow API key

Sign in at `http://127.0.0.1:8008`, open settings through the avatar, select **API**, and click **API Key**. In the dialog, click **Create new Key** and copy the result.

# Step 2: Configure the console

Use console `0.8.7` or later and sign in as super administrator.

Enable **Knowledge Base** under **Parameters and Dictionaries > System Feature Configuration**, then save. The navigation should now show **Knowledge Base**.

Open **Model Configuration > Knowledge Base**, find `RAG_RAGFlow`, and click **Edit**. Set **Service Address** to your reachable RAGFlow URL. The original placeholder `http://你的ragflow服务的局域网IP:8008` means “http://your RAGFlow service's LAN IP:8008”; for `192.168.1.100`, enter `http://192.168.1.100:8008`. Enter the copied key in **API Key** and save.

# Step 2: Create a knowledge base

As super administrator, open **Knowledge Base**, click **Add** at the lower left, enter a name and description, and save. Use meaningful text so the LLM can choose and retrieve the right knowledge. For example, name it “Company Introduction” and describe its contents: company information, services, phone number, and address.

Click **View** for the new knowledge base. In its detail page, click **Add** to upload documents. Click **Parse** for each uploaded document. After parsing, inspect the chunks and use **Retrieval Test** to test recall/search.

# Step 3: Enable it for the agent

Open **Agents**, choose the agent, and click **Configure Role**. Click **Edit Functions** beside intent recognition, select the knowledge base in the dialog, and save.
