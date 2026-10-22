# Enable voiceprint recognition

This guide covers deploying the voiceprint service and configuring full-module or server-only installations.

# 1. Deploy the voiceprint service

## Step 1: Download the source

Open [voiceprint-api](https://github.com/xinnan-tech/voiceprint-api), select **Code > Download ZIP**, extract it, and rename `voiceprint-api-main` to `voiceprint-api`.

## Step 2: Check database reachability

The service needs MySQL. You can share the MySQL instance from an existing management-console installation. Test port `3306` from the host:

```
telnet 127.0.0.1 3306
```

If it responds, continue to step 3. Otherwise check how MySQL was installed and fix network isolation first. For a database installed with this project's `docker-compose_all.yml`, the original guide changes this fragment:

```
  xiaozhi-esp32-server-db:
    ...
    networks:
      - default
    expose:
      - "3306:3306"
```

to:

```
  xiaozhi-esp32-server-db:
    ...
    networks:
      - default
    ports:
      - "3306:3306"
```

That is, change `expose` to `ports` under `xiaozhi-esp32-server-db`, then restart. Original commands:

```
# Enter the directory containing docker-compose_all.yml, e.g. xiaozhi-server
cd xiaozhi-server
docker compose -f docker-compose_all.yml down
docker compose -f docker-compose.yml up -d
```

The original restart excerpt uses `docker-compose_all.yml` for shutdown but `docker-compose.yml` for startup. Verify the appropriate Compose file for your deployment; this translation leaves the command semantics unchanged.

Retest:

```
telnet 127.0.0.1 3306
```

## Step 3: Create the database and table

Once the host can reach MySQL, create `voiceprint_db` and `voiceprints`:

```
CREATE DATABASE voiceprint_db CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;

USE voiceprint_db;

CREATE TABLE voiceprints (
    id INT AUTO_INCREMENT PRIMARY KEY,
    speaker_id VARCHAR(255) NOT NULL UNIQUE,
    feature_vector LONGBLOB NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    INDEX idx_speaker_id (speaker_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
```

## Step 4: Configure the database connection

In `voiceprint-api`, create `data`. Copy the root `voiceprint.yaml` into it and rename it to `.voiceprint.yaml`. Configure MySQL there:

```
mysql:
  host: "127.0.0.1"
  port: 3306
  user: "root"
  password: "your_password"
  database: "voiceprint_db"
```

For a Docker voiceprint deployment, use the LAN IP of the MySQL machine as `host`, rather than the container's loopback address.

## Step 5: Start the service

Use Docker as below, or follow the project's [source deployment instructions](https://github.com/xinnan-tech/voiceprint-api/blob/main/README.md).

```
# Enter the project root
cd voiceprint-api

# Remove old containers and image
docker compose -f docker-compose.yml down
docker stop voiceprint-api
docker rm voiceprint-api
docker rmi ghcr.nju.edu.cn/xinnan-tech/voiceprint-api:latest

# Start the Docker container
docker compose -f docker-compose.yml up -d
# Read logs
docker logs -f voiceprint-api
```

The original historical log reports Uvicorn startup on `0.0.0.0:8005` and prints the voiceprint health URL:

```
250711 INFO-🚀 开始: 生产环境服务启动（Uvicorn），监听地址: 0.0.0.0:8005
250711 INFO-============================================================
250711 INFO-声纹接口地址: http://127.0.0.1:8005/voiceprint/health?key=abcd
250711 INFO-============================================================
```

Copy the URL, but replace Docker/loopback addresses with your host's reachable LAN IP. Change:

```
http://127.0.0.1:8005/voiceprint/health?key=abcd

```

to:

```
http://192.168.1.25:8005/voiceprint/health?key=abcd
```

Open that URL in a browser. A successful response looks like:

```
{"total_voiceprints":0,"status":"healthy"}
```

Keep the corrected secret-bearing URL for configuration.

# 2. Full-module configuration

## Step 1: Configure the endpoint

Open **Parameters and Dictionaries > System Feature Configuration**, enable **Voiceprint Recognition**, and save. New agent cards should show a voiceprint button.

As administrator, open **Parameters and Dictionaries > Parameter Management**, find `server.voice_print` (initially `null`), click **Edit**, paste the health URL into **Parameter Value**, and save. A save failure often means the console cannot reach the service; check the firewall and LAN IP.

## Step 2: Set agent memory and reporting

In the agent's role configuration, select **Local Short-Term Memory** and enable **Report Text + Audio**.

## Step 3: Talk to the agent

Power on the device and speak at a normal speed and pitch.

## Step 4: Enroll a voiceprint

In **Agent Management**, click **Voiceprint Recognition** on the agent card, then **Add** at the bottom. Register a speaker from their recorded speech. Fill **Description** with useful information such as occupation, personality, or interests so the agent can understand who is speaking.

## Step 5: Test recognition

Ask the agent whether it knows who you are. A correct identification indicates that recognition works.

# 3. Server-only configuration

## Step 1: Configure the endpoint

Create or edit `xiaozhi-server/data/.config.yaml`:

```
# Voiceprint recognition configuration
voiceprint:
  # Voiceprint endpoint URL
  url: 你的声纹接口地址
  # Speaker entries: speaker_id,name,description
  speakers:
    - "test1,张三,张三是一个程序员"
    - "test2,李四,李四是一个产品经理"
    - "test3,王五,王五是一个设计师"
```

Replace `你的声纹接口地址` (“your voiceprint endpoint URL”) with the health URL and save. Add `speakers` as needed; retain each `speaker_id` for enrollment.

The original Chinese speaker entries are multilingual identity fixtures: `test1` is Zhang San, a programmer; `test2` is Li Si, a product manager; `test3` is Wang Wu, a designer. Keep the comma-separated format.

## Step 2: Enroll a voiceprint

With the voiceprint service running, open `http://localhost:8005/voiceprint/docs` for API documentation.

POST to `http://localhost:8005/voiceprint/register`. Send a Bearer token from the health URL's `?key=` value. For `http://127.0.0.1:8005/voiceprint/health?key=abcd`, the token is `abcd`.

The multipart body contains `speaker_id` and a WAV audio `file`:

```
curl -X POST \
  -H "Authorization: Bearer YOUR_ACCESS_TOKEN" \
  -F "speaker_id=your_speaker_id_here" \
  -F "file=@/path/to/your/file" \
  http://localhost:8005/voiceprint/register
```

Use the same `speaker_id` as the configuration. For the original Zhang San example, send `test1` with that person's speech sample.

## Step 3: Start both services

Run the Xiaozhi server and voiceprint service to use recognition.
