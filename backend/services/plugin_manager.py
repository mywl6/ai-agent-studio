"""插件包安装（zip 格式）"""
import json
import zipfile
from pathlib import Path
from backend.config import PLUGINS_DIR


def install_plugin(zip_path: str) -> dict:
    """安装插件：解压 zip 到 plugins/ 目录"""
    with zipfile.ZipFile(zip_path, "r") as zf:
        manifest_data = None
        for name in zf.namelist():
            if name.endswith("manifest.json"):
                manifest_data = json.loads(zf.read(name))
                break

        if not manifest_data:
            raise ValueError("插件包中没有 manifest.json")

        plugin_name = manifest_data.get("name", "unknown")
        plugin_dir = PLUGINS_DIR / plugin_name
        plugin_dir.mkdir(parents=True, exist_ok=True)
        zf.extractall(plugin_dir)

    return manifest_data


def uninstall_plugin(plugin_name: str) -> bool:
    """卸载插件"""
    plugin_dir = PLUGINS_DIR / plugin_name
    if plugin_dir.exists():
        import shutil
        shutil.rmtree(plugin_dir)
        return True
    return False


def list_plugins() -> list[dict]:
    """列出已安装的插件"""
    plugins = []
    if PLUGINS_DIR.exists():
        for d in PLUGINS_DIR.iterdir():
            if d.is_dir() and d.name != "__pycache__":
                manifest_path = d / "manifest.json"
                if manifest_path.exists():
                    with open(manifest_path, "r", encoding="utf-8") as f:
                        plugins.append(json.load(f))
    return plugins
