# Attribution

Original project code, fictional invoice fixtures, tests, and report: Copyright (c) 2026 Ehsan Cheraghi, MIT License. No real invoice or customer data is bundled.

Optional model: [Qwen/Qwen3-0.6B-GGUF](https://huggingface.co/Qwen/Qwen3-0.6B-GGUF), Apache-2.0, revision `23749fefcc72300e3a2ad315e1317431b06b590a`, Q8_0 quantization. Model files are downloaded separately and retain their own license.

Optional inference engine: [llama.cpp b11617](https://github.com/ggml-org/llama.cpp/releases/tag/b11617), MIT License. Runtime binaries are downloaded separately. The adapter uses its [OpenAI-compatible server interface](https://github.com/ggml-org/llama.cpp/blob/master/tools/server/README.md).

Pinned checksums and the published runtime configuration are recorded in `runtime-reference.json`. The Windows helper verifies the official archive and model before extracting or using them.
