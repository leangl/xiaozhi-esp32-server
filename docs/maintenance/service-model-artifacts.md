# Local model artifact boundary

Reviewed 2026-10-21. Local inference is separate from an external service
operator. The supported backend does not install Torch/FunASR/ModelScope, call
Torch Hub or download weights during startup. Missing approved AI configuration
or local VAD files produces an actionable readiness error.

## Silero VAD

The retained `core/providers/vad/silero.py` loads an explicit local ONNX file
with ONNX Runtime's CPU provider. It does not import the vendored project's
Torch helpers or their optional download function. The default configured path
is `models/silero_vad.onnx`; that path is deliberately not auto-populated.

The existing checkout contains a legacy fixture at
`main/xiaozhi-server/models/snakers4_silero-vad/src/silero_vad/data/silero_vad.onnx`:

- SHA-256: `2623a2953f6ff3d2c1e61740c6cdb7168133479b267dfef114a4a3cc5bdd788f`.
- [Upstream project](https://github.com/snakers4/silero-vad) and its
  [published MIT license](https://github.com/snakers4/silero-vad/blob/master/LICENSE)
  were checked. This identifies project licensing, not an exact source release
  or training-data provenance for the older vendored bytes.
- This fixture can support bounded synthetic offline tests when explicitly
  selected. It is not automatically approved as a production model by this hash
  record. Provision a reviewed release, exact artifact hash and required license
  notice before production distribution. No cloud service account is needed for
  the local inference itself.

## Former ASR assets

SenseVoice and other legacy assets are not required and are excluded from the
candidate Docker context. Their files/legal notices remain in source for
historical inspection; the removed SDKs and adapters cannot load them through
the supported factory. Existing evaluation mounts are not deleted or modified.
