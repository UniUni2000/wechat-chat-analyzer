"""
配置加载器 - 从 config.json 读取路径配置
首次运行时自动检测微信数据目录，检测失败则提示手动配置
"""
import glob
import json
import os
import platform
import sys

CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "config.json")

_DEFAULT_TEMPLATE_DIR = r"D:\xwechat_files\your_wxid\db_storage"

_DEFAULT = {
    "db_dir": _DEFAULT_TEMPLATE_DIR,
    "keys_file": "all_keys.json",
    "decrypted_dir": "decrypted",
    "decoded_image_dir": "decoded_images",
    "wechat_process": "Weixin.exe",
}


def auto_detect_db_dir():
    """从微信本地配置自动检测 db_storage 路径 (Windows)。

    读取 %APPDATA%\\Tencent\\xwechat\\config\\*.ini，
    找到数据存储根目录，然后匹配 xwechat_files\\*\\db_storage。
    """
    appdata = os.environ.get("APPDATA", "")
    config_dir = os.path.join(appdata, "Tencent", "xwechat", "config")
    if not os.path.isdir(config_dir):
        return None

    # 从 ini 文件中找到有效的目录路径
    data_roots = []
    for ini_file in glob.glob(os.path.join(config_dir, "*.ini")):
        try:
            # 微信 ini 可能是 utf-8 或 gbk 编码（中文路径）
            content = None
            for enc in ("utf-8", "gbk"):
                try:
                    with open(ini_file, "r", encoding=enc) as f:
                        content = f.read(1024).strip()
                    break
                except UnicodeDecodeError:
                    continue
            if not content or any(c in content for c in "\n\r\x00"):
                continue
            if os.path.isdir(content):
                data_roots.append(content)
        except OSError:
            continue

    # 在每个根目录下搜索 xwechat_files\*\db_storage
    seen = set()
    candidates = []
    for root in data_roots:
        pattern = os.path.join(root, "xwechat_files", "*", "db_storage")
        for match in glob.glob(pattern):
            normalized = os.path.normcase(os.path.normpath(match))
            if os.path.isdir(match) and normalized not in seen:
                seen.add(normalized)
                candidates.append(match)

    if len(candidates) == 1:
        return candidates[0]
    if len(candidates) > 1:
        # 完全自动化无头环境，遇到多开号或者多用户时，绝不堵塞。
        # 选择最新活跃的那个 db_storage
        candidates.sort(key=lambda x: os.path.getmtime(x) if os.path.exists(x) else 0, reverse=True)
        return candidates[0]
    return None


def auto_detect_macos_db_dir():
    """从 macOS 微信本地配置自动检测 db_storage 路径。

    检测路径: ~/Library/Containers/com.tencent.xinWeChat/Data/Library/Application Support/com.tencent.xinWeChat/4.0b*/
    返回 db_storage 路径（在 4.0b* 目录下）。
    """
    home = os.path.expanduser("~")
    base_path = os.path.join(
        home,
        "Library",
        "Containers",
        "com.tencent.xinWeChat",
        "Data",
        "Library",
        "Application Support",
        "com.tencent.xinWeChat"
    )

    if not os.path.isdir(base_path):
        return None

    # 使用 glob 匹配 4.0b* 目录
    pattern = os.path.join(base_path, "4.0b*")
    version_dirs = glob.glob(pattern)

    if not version_dirs:
        return None

    # 按修改时间排序，选择最新的版本目录
    version_dirs.sort(key=lambda x: os.path.getmtime(x) if os.path.exists(x) else 0, reverse=True)

    # 在最新的版本目录下查找 db_storage
    for version_dir in version_dirs:
        db_storage_path = os.path.join(version_dir, "db_storage")
        if os.path.isdir(db_storage_path):
            return db_storage_path

    return None


def load_config():
    cfg = {}
    if os.path.exists(CONFIG_FILE):
        try:
            with open(CONFIG_FILE) as f:
                cfg = json.load(f)
        except json.JSONDecodeError:
            print(f"[!] {CONFIG_FILE} 格式损坏，将使用默认配置")
            cfg = {}

    # db_dir 缺失或仍为模板值时，尝试自动检测
    db_dir = cfg.get("db_dir", "")
    if not db_dir or db_dir == _DEFAULT_TEMPLATE_DIR or "your_wxid" in db_dir:
        # 根据平台调用不同的检测函数
        system = platform.system()
        if system == "Windows":
            detected = auto_detect_db_dir()
        elif system == "Darwin":
            detected = auto_detect_macos_db_dir()
        else:
            detected = None

        if detected:
            print(f"[+] 自动检测到微信数据目录: {detected}")
            # 合并默认值并保存
            cfg = {**_DEFAULT, **cfg, "db_dir": detected}
            with open(CONFIG_FILE, "w") as f:
                json.dump(cfg, f, indent=4, ensure_ascii=False)
            print(f"[+] 已保存到: {CONFIG_FILE}")
        else:
            if not os.path.exists(CONFIG_FILE):
                with open(CONFIG_FILE, "w") as f:
                    json.dump(_DEFAULT, f, indent=4)
            print(f"[!] 未能自动检测微信数据目录")
            print(f"    请手动编辑 {CONFIG_FILE} 中的 db_dir 字段")
            print(f"    路径可在 微信设置 → 文件管理 中找到")
            sys.exit(1)

    # 将相对路径转为绝对路径
    base = os.path.dirname(os.path.abspath(__file__))
    for key in ("keys_file", "decrypted_dir", "decoded_image_dir"):
        if key in cfg and not os.path.isabs(cfg[key]):
            cfg[key] = os.path.join(base, cfg[key])

    # 自动推导微信数据根目录（db_dir 的上级目录）
    # db_dir 格式: D:\xwechat_files\<wxid>\db_storage
    # base_dir 格式: D:\xwechat_files\<wxid>
    db_dir = cfg.get("db_dir", "")
    if db_dir and os.path.basename(db_dir) == "db_storage":
        cfg["wechat_base_dir"] = os.path.dirname(db_dir)
    else:
        cfg["wechat_base_dir"] = db_dir

    # decoded_image_dir 默认值
    if "decoded_image_dir" not in cfg:
        cfg["decoded_image_dir"] = os.path.join(base, "decoded_images")

    return cfg
