"""List models and disk usage."""

from __future__ import annotations

from .config import PROJECT_ROOT, list_profiles, load_config, paths_from_config
from .manifest import read_manifest
from .utils import format_size


def run_inventory(profile: str | None = None) -> int:
    config = load_config(profile) if profile else load_config()
    paths = paths_from_config(config)
    models_dir = paths["models"]

    print("\nQuantForge Inventory")
    print("=" * 60)
    print(f"Project:  {PROJECT_ROOT}")
    print(f"Profile:  {config.get('profile')}")
    print(f"Models:   {models_dir}")
    print()

    gguf_files = sorted(models_dir.glob("*.gguf"))
    print(f"GGUF files ({len(gguf_files)}):")
    total = 0
    for f in gguf_files:
        size = f.stat().st_size
        total += size
        active = " <-- active" if f.name == config.get("model", {}).get("gguf_output") else ""
        print(f"  {f.name:<40} {format_size(size)}{active}")
    if gguf_files:
        print(f"  Total GGUF: {format_size(total)}")

    print("\nBase weight folders:")
    for d in sorted(models_dir.iterdir()):
        if d.is_dir() and not d.name.startswith("."):
            size = sum(f.stat().st_size for f in d.rglob("*") if f.is_file())
            print(f"  {d.name:<40} {format_size(size)}")

    manifest_path = models_dir / "manifest.json"
    if manifest_path.exists():
        print(f"\nManifest ({manifest_path}):")
        for m in read_manifest(manifest_path).get("models", []):
            print(f"  {m.get('gguf_file')}  sha256={m.get('sha256', '')[:16]}...")

    print(f"\nProfiles: {', '.join(list_profiles())}")
    return 0
