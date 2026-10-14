"""Download the pinned official Windows CPU runtime and model. No system install."""
import hashlib
from pathlib import Path
import urllib.request
import zipfile

ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT/'runtime'
DOWNLOADS = [
    ('llama-b11617-bin-win-cpu-x64.zip',
     'https://github.com/ggml-org/llama.cpp/releases/download/b11617/llama-b11617-bin-win-cpu-x64.zip',
     '1bad07f7993889a1f7431ad647904294f56919bf0bc84f4021327db1641a411c'),
    ('Qwen3-0.6B-Q8_0.gguf',
     'https://huggingface.co/Qwen/Qwen3-0.6B-GGUF/resolve/23749fefcc72300e3a2ad315e1317431b06b590a/Qwen3-0.6B-Q8_0.gguf',
     '9465e63a22add5354d9bb4b99e90117043c7124007664907259bd16d043bb031')
]


def main():
    RUNTIME.mkdir(exist_ok=True)
    for name,url,expected in DOWNLOADS:
        dest = RUNTIME/name
        if not dest.exists():
            partial = dest.with_suffix(dest.suffix+'.part')
            print('Downloading',name,flush=True)
            urllib.request.urlretrieve(url,partial)
            with partial.open('rb') as stream:
                digest = hashlib.file_digest(stream,'sha256').hexdigest()
            if digest != expected:
                raise ValueError(f'Checksum mismatch for {name}; partial file retained for inspection.')
            partial.replace(dest)
        with dest.open('rb') as stream:
            if hashlib.file_digest(stream,'sha256').hexdigest() != expected:
                raise ValueError(f'Checksum mismatch for existing {name}.')
    target = (RUNTIME/'llama').resolve()
    with zipfile.ZipFile(RUNTIME/DOWNLOADS[0][0]) as archive:
        for name in archive.namelist():
            if not (target/name).resolve().is_relative_to(target):
                raise ValueError('Unsafe archive member.')
        archive.extractall(target)
    print('Ready. Run scripts/start_model.ps1 in one terminal, then invoice-review extract examples/standard.txt in another.')


if __name__ == '__main__':
    main()
