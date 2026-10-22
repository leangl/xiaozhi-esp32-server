# Retained language data

The test page's instructions and diagnostics are English. These deliberate
Chinese examples remain unchanged so the existing language tests and runtime
fallbacks still work:

- `js/config/manager.js` and `wakeword_runtime/config/config_loader.py` contain
  the default Chinese wake-word list. These are spoken phrases matched by the
  wake-word model, not developer instructions.
- `index.html` shows two Chinese wake-word examples and the original localized
  character names alongside the Hiyori and Natori model names.
- `js/core/network/websocket.js` sends the original greeting (meaning "Hey,
  hello") in the `listen detect` message. It recognizes both the Chinese word
  meaning "bind" and English `bind` in server messages. Changing that match
  would change binding detection.
- `js/app.js` and `js/core/mcp/tools.js` retain the Chinese photo-analysis prompt,
  meaning "Describe the objects you see", as language-specific default input.
- `js/core/network/wakeword-bridge.js` and `js/ui/controller.js` retain the
  fallback Chinese phrase meaning "wake word".
- `js/config/default-mcp-tools.json` retains mock response examples meaning
  "Volume has been set to ${volume}" and "Brightness has been set to
  ${brightness}". Placeholder names and tool schemas are unchanged.

The bundled Live2D JSON display/physics metadata and original legal notices are
vendor assets, not maintained application prose. See
[English vendor reading notes](resources/README-en.md); model files are not
rewritten or rebuilt as part of this translation.
