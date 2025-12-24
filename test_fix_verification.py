#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
紧急修复验证脚本
验证水印分块和5图报告功能
Author: JCHSH
"""

import os
import sys
from datetime import datetime

# 添加项目根目录到 Python 路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# 直接导入核心函数
import cv2
import numpy as np
from PIL import Image, PngImagePlugin
import configparser
import re

# 导入本地模块
from src.watermark_core import add_invisible_watermark
from src.audit_service import analyze_single_image


def encrypt_single_image(input_path, discord_uid, output_dir='output_encrypted'):
    """简化的加密函数用于测试"""
    os.makedirs(output_dir, exist_ok=True)
    
    # 清洗UUID
    cleaned_uuid = re.sub(r'[^0-9]', '', discord_uid)
    
    # 构建水印文本（强制分块）
    watermark_lines = []
    chunk_size = 11
    for i in range(0, len(cleaned_uuid), chunk_size):
        watermark_lines.append(cleaned_uuid[i:i+chunk_size])
    watermark_lines.append(datetime.now().strftime('%Y-%m-%d'))
    watermark_lines.append(datetime.now().strftime('%H:%M'))
    
    watermark_text = '\n'.join(watermark_lines)
    
    # 添加水印
    watermarked_array = add_invisible_watermark(
        input_image_path=input_path,
        output_image_path=None,
        watermark_text=watermark_text,
        intensity=100
    )
    
    if watermarked_array is False or watermarked_array is None:
        return None
    
    # 保存
    filename_stem = os.path.splitext(os.path.basename(input_path))[0]
    output_filename = f"{filename_stem}_{cleaned_uuid}.png"
    output_path = os.path.join(output_dir, output_filename)
    
    cv2.imwrite(output_path, watermarked_array)
    
    return {'output_file': output_path}

def main():
    print("=" * 70)
    print("紧急修复验证测试")
    print("=" * 70)
    
    # 测试参数
    test_uuid = "<@1399304164919742526>"
    test_image = "input_images/5.png"
    
    if not os.path.exists(test_image):
        print(f"\n❌ 错误: 找不到测试图片 {test_image}")
        return
    
    print(f"\n测试UUID: {test_uuid}")
    print(f"测试图片: {test_image}")
    
    # Step 1: 加密图片（应该自动分块UUID）
    print(f"\n{'='*70}")
    print("Step 1: 加密图片并嵌入水印")
    print(f"{'='*70}")
    
    result = encrypt_single_image(
        input_path=test_image,
        discord_uid=test_uuid,
        output_dir='output_encrypted'
    )
    
    if not result:
        print("\n❌ 加密失败")
        return
    
    output_file = result['output_file']
    print(f"\n✓ 加密成功: {output_file}")
    
    # Step 2: 生成审计报告
    print(f"\n{'='*70}")
    print("Step 2: 生成审计分析报告")
    print(f"{'='*70}")
    
    report_result = analyze_single_image(
        watermarked_path=output_file,
        original_path=test_image,
        save_dir='output_reports'
    )
    
    if not report_result:
        print("\n❌ 报告生成失败")
        return
    
    print(f"\n✓ 报告生成成功:")
    if 'spectrum_file' in report_result:
        print(f"  - 黑白频谱图: {report_result['spectrum_file']}")
    if 'report_file' in report_result:
        print(f"  - 完整5图报告: {report_result['report_file']}")
    
    # Step 3: 验证要求
    print(f"\n{'='*70}")
    print("Step 3: 验证修复效果")
    print(f"{'='*70}")
    
    checks = []
    
    # 检查1: 黑白频谱图是否存在
    if 'spectrum_file' in report_result and os.path.exists(report_result['spectrum_file']):
        checks.append("✓ 黑白频谱图已生成")
    else:
        checks.append("✗ 黑白频谱图缺失")
    
    # 检查2: 5图报告是否存在
    if 'report_file' in report_result and os.path.exists(report_result['report_file']):
        checks.append("✓ 5图分析报告已生成")
    else:
        checks.append("✗ 5图分析报告缺失")
    
    # 检查3: 输出文件大小合理
    if os.path.exists(output_file):
        size = os.path.getsize(output_file)
        if size > 1000:  # 至少1KB
            checks.append(f"✓ 加密图片大小合理 ({size:,} 字节)")
        else:
            checks.append(f"✗ 加密图片可能损坏 ({size} 字节)")
    
    for check in checks:
        print(f"  {check}")
    
    print(f"\n{'='*70}")
    print("修复验证完成！")
    print(f"{'='*70}")
    
    print("\n预期效果:")
    print("  1. UUID <@1399304164919742526> 应该被分成 3-4 行显示")
    print("  2. 水印呈现'方块印章'形状，位于左上和右下对角线")
    print("  3. 5图报告应包含: [原图 | 原图频谱 | 已签名图 | 已签名频谱 | 能量波峰]")
    print("  4. 黑白频谱图中UUID文本清晰可见，无截断")
    
    print("\n请检查输出文件:")
    print(f"  - 加密图: {output_file}")
    if 'spectrum_file' in report_result:
        print(f"  - 频谱图: {report_result['spectrum_file']}")
    if 'report_file' in report_result:
        print(f"  - 完整报告: {report_result['report_file']}")

if __name__ == '__main__':
    main()
