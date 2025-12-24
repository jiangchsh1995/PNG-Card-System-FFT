#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SGP 主程序 v1.0 - Discord Bot 入口
纯水印版权保护系统 - 根据 config.ini 中的 [BotCommands] 映射分发任务
Author: JCHSH
"""

import sys
import os
import configparser

# 将 src 目录添加到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))


def load_bot_commands(config_file='config.ini'):
    """读取Bot指令配置"""
    config = configparser.ConfigParser()
    
    if not os.path.exists(config_file):
        return {
            'sign_cmd': '/bot:制作水印',
            'check_cmd': '/bot:查询水印'
        }
    
    config.read(config_file, encoding='utf-8-sig')
    
    sign_cmd = config.get('BotCommands', 'sign_cmd', fallback='/bot:制作水印')
    check_cmd = config.get('BotCommands', 'check_cmd', fallback='/bot:查询水印')
    
    return {
        'sign_cmd': sign_cmd,
        'check_cmd': check_cmd
    }


def show_help(commands):
    """显示帮助信息"""
    print("=" * 70)
    print("SGP Protocol (ShadowGuard Protocol)")
    print("基于频域的抗干扰盲水印系统")
    print("Author: JCHSH")
    print("=" * 70)
    print("\n可用指令：")
    print(f"  {commands['sign_cmd']}  - 制作水印（批量水印注入）")
    print(f"  {commands['check_cmd']}     - 查询水印（生成分析报告）")
    print("\n使用方法：")
    print(f"  python main.py sign      # 制作水印")
    print(f"  python main.py check     # 查询水印")
    print(f"  python main.py --help    # 显示帮助")
    print("\n配置文件：")
    print(f"  config.ini - 修改 [BotCommands] 区域可更改Bot触发词")
    print("=" * 70)


def main():
    """主函数"""
    # 加载Bot指令配置
    commands = load_bot_commands()
    
    # 解析命令行参数
    if len(sys.argv) < 2:
        print("⚠ 错误: 缺少参数")
        print()
        show_help(commands)
        return 1
    
    action = sys.argv[1].lower()
    
    # 显示帮助
    if action in ['--help', '-h', 'help']:
        show_help(commands)
        return 0
    
    # 执行水印签名服务
    elif action in ['sign', 'watermark', 's']:
        print(f"🖊️ 调用指令: {commands['sign_cmd']}")
        print()
        from watermark_service import batch_process
        batch_process()
        return 0
    
    # 执行水印查询服务
    elif action in ['check', 'verify', 'audit', 'c']:
        print(f"🔍 调用指令: {commands['check_cmd']}")
        print()
        from audit_service import batch_analyze
        batch_analyze()
        return 0
    
    # 未知指令
    else:
        print(f"⚠ 错误: 未知指令 '{action}'")
        print()
        show_help(commands)
        return 1


if __name__ == '__main__':
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n⚠ 用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
