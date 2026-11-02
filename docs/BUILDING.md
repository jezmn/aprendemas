# Building

## Cross-CPU llama-cpp-python

Prebuilt wheels may be compiled with AVX512, causing `OSError: [WinError -1073741795]` on CPUs without AVX512.

### Verify your build

```powershell
python -c "import llama_cpp; print(llama_cpp.llama_print_system_info().decode())"
```

If `AVX512 = 1` appears, rebuild.

### Rebuild steps

1. Download source:
   ```powershell
   pip download llama-cpp-python --no-deps --no-binary llama-cpp-python -d C:\temp\llama_src
   cd C:\temp\llama_src
   tar -xf llama_cpp_python-<VERSION>.tar.gz
   ```
2. Edit `vendor\llama.cpp\ggml\CMakeLists.txt`: set `GGML_NATIVE_DEFAULT OFF` and change the `if` to `if (GGML_NATIVE)`.
3. Delete precompiled DLLs: `Remove-Item "llama_cpp\lib\*"`.
4. Install: `pip install "C:\temp\llama_src\llama_cpp_python-<VERSION>" --no-cache-dir --no-build-isolation`.
5. Verify: expect `AVX2 = 1`, no AVX512.

Repeat on version updates.

## Building the release

```bash
cd chat && pnpm run build && cd ..
pip install pyinstaller
pyinstaller AprendeMas.spec
```

Output: `dist/AprendeMas/` (a folder — the bundled engine is ~150 MB, onefile would extract it to a temp dir on every launch). It embeds piper + onnxruntime + espeak-ng, so the target machine needs nothing installed. Zip it with `model/` and `voices/` for a portable release:

```
AprendeMas/
    AprendeMas.exe
    model/*.gguf
    voices/*.onnx + *.onnx.json
```
