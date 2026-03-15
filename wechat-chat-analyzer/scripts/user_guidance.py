#!/usr/bin/env python3
"""
用户引导脚本
帮助用户提供正确的联系人标识符
"""

import sys

def get_user_input():
    """获取用户输入的联系人信息"""
    print("=" * 60)
    print("  微信聊天分析 - 联系人识别")
    print("=" * 60)
    print("\n为了更准确地找到您的联系人，请提供以下信息：")
    print("\n提示：使用微信ID（如 'wxid_example123'）是最可靠的方式")
    print("   微信ID是联系人的唯一标识，不会因为昵称或备注的变化而改变")
    
    wechat_id = input("\n请输入联系人的微信ID（如果不知道可以留空）: ").strip()
    
    if wechat_id:
        print(f"\n已获取微信ID: {wechat_id}")
        return wechat_id
    else:
        print("\n未提供微信ID，将尝试使用其他方式识别")
        nickname = input("请输入联系人的昵称: ").strip()
        remark = input("请输入联系人的备注名: ").strip()
        
        if nickname:
            print(f"\n已获取昵称: {nickname}")
            return nickname
        elif remark:
            print(f"\n已获取备注名: {remark}")
            return remark
        else:
            print("\n未提供任何联系人信息，无法继续")
            return None

def main():
    """主函数"""
    contact_id = get_user_input()
    if contact_id:
        print(f"\n联系人标识: {contact_id}")
        print("\n正在启动分析...")
        return contact_id
    else:
        print("\n无法获取联系人信息，分析无法继续")
        sys.exit(1)

if __name__ == "__main__":
    main()
