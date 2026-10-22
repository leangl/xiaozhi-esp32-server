# Digital-human development module

This is a development guide. For server deployment, see the [project README](../../README.md).

For an x86 all-in-one installation, full-screen kiosk startup and operating-system setup, see the [all-in-one deployment guide](../../docs/all-in-one-digital-human-setup.md).

For wake-word model downloads, runtime settings and detailed usage, see the [wake-word guide](../../docs/digital-human-wakeword.md).

## Overview

The independent digital-human test module provides a local test page, browser interaction assets, a wake-word runtime and an event bridge for end-to-end integration testing.

## Quick start

Install dependencies:

```bash
pip install -r wakeword_runtime/requirements.txt
```

Start the module:

```bash
python start.py
```

## Local endpoints

After startup:

- Test page: http://127.0.0.1:8006/index.html
- Event bridge: ws://127.0.0.1:8006/wakeword-ws
- Health check: http://127.0.0.1:8006/health

## Directory layout

- `start.py`: module entry point.
- `index.html`: digital-human test page.
- `wakeword_runtime`: local wake-word runtime and configuration.
- `js`, `css`: browser scripts and styles.
- `images`, `resources`: page assets.

## Related guides

- [All-in-one deployment](../../docs/all-in-one-digital-human-setup.md): x86 installation, kiosk display and automatic startup.
- [Wake-word guide](../../docs/digital-human-wakeword.md): model downloads, runtime settings and local debugging.
