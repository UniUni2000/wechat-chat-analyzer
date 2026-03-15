#!/usr/bin/env python3
"""
依赖检查与安装脚本
确保所有必要的Python库都已安装
"""

import subprocess
import sys
import importlib
import os

# 依赖列表
REQUIRED_PACKAGES = [
    'pycryptodome',
    'matplotlib',
    'wordcloud',
    'jieba',
    'numpy'
]

def check_dependency(package):
    """检查依赖是否安装"""
    try:
        if package == 'pycryptodome':
            # 特别检查Crypto模块是否可用
            importlib.import_module('Crypto.Cipher.AES')
            return True
        else:
            importlib.import_module(package)
            return True
    except ImportError:
        return False

def install_dependency(package):
    """安装依赖"""
    print(f"正在安装 {package}...")
    try:
        subprocess.check_call([sys.executable, '-m', 'pip', 'install', package, '-q'])
        return True
    except subprocess.CalledProcessError:
        return False

def main():
    print("=" * 60)
    print("  📦 微信聊天分析依赖检查")
    print("=" * 60)
    
    missing_packages = []
    
    for package in REQUIRED_PACKAGES:
        if check_dependency(package):
            print(f"  ✅ {package} 已安装")
        else:
            print(f"  ❌ {package} 未安装")
            missing_packages.append(package)
    
    if missing_packages:
        print("\n正在安装缺失的依赖...")
        for package in missing_packages:
            if install_dependency(package):
                print(f"  ✅ {package} 安装成功")
            else:
                print(f"  ❌ {package} 安装失败")
                
                # 特别处理pycryptodome安装失败的情况
                if package == 'pycryptodome':
                    print("  💡 尝试使用特定版本...")
                    if install_dependency('pycryptodome==3.15.0'):
                        print(f"  ✅ pycryptodome 3.15.0 安装成功")
                    else:
                        print(f"  ❌ pycryptodome 安装仍然失败")
    else:
        print("\n  ✅ 所有依赖已安装")
    
    # 最终验证
    print("\n正在验证所有依赖...")
    all_installed = True
    
    for package in REQUIRED_PACKAGES:
        if check_dependency(package):
            print(f"  ✅ {package} 验证通过")
        else:
            print(f"  ❌ {package} 验证失败")
            all_installed = False
    
    print("\n" + "=" * 60)
    if all_installed:
        print("  ✅ 依赖检查完成，所有依赖已就绪")
        return 0
    else:
        print("  ❌ 部分依赖安装失败，请检查网络连接或手动安装")
        return 1

if __name__ == "__main__":
    sys.exit(main())
