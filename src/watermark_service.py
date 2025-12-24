#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SGP 水印服务 v1.0 - 纯水印版权保护系统
功能：频域盲水印注入 + 元数据无损搬运
Author: JCHSH
"""

import os
import configparser
import glob
import cv2
import numpy as np
from PIL import Image, PngImagePlugin
from .watermark_core import add_invisible_watermark


def load_config(config_file='config.ini'):
    """加载配置文件"""
    config = configparser.ConfigParser()
    
    if not os.path.exists(config_file):
        print(f"⚠ 警告: 配置文件 {config_file} 不存在，使用默认配置")
        return {
            'input_dir': 'input_images',
            'output_dir': 'output_encrypted',
            'watermark_text': 'SGP SECURITY',
            'watermark_intensity': 100,
            'output_suffix': '_SGP_Signed'
        }
    
    config.read(config_file, encoding='utf-8-sig')
    
    # 读取路径配置
    input_dir = config.get('Paths', 'input_dir', fallback='input_images')
    output_dir = config.get('Paths', 'output_dir', fallback='output_encrypted')
    
    # 读取水印配置
    watermark_text = config.get('Watermark', 'text', fallback='SGP SECURITY')
    watermark_text = watermark_text.replace('\\n', '\n')
    watermark_intensity = config.getint('Watermark', 'intensity', fallback=100)
    
    # 读取输出配置
    output_suffix = config.get('Output', 'suffix', fallback='_SGP_Signed')
    
    return {
        'input_dir': input_dir,
        'output_dir': output_dir,
        'watermark_text': watermark_text,
        'watermark_intensity': watermark_intensity,
        'output_suffix': output_suffix
    }


def ensure_directories(cfg):
    """确保所有必需的目录存在"""
    dirs = [cfg['input_dir'], cfg['output_dir']]
    
    for directory in dirs:
        if not os.path.exists(directory):
            os.makedirs(directory)
            print(f"  ✓ 创建目录: {directory}/")


def process_image(input_path, cfg, user_uuid='SGP_User'):
    """
    处理单张图片：水印注入 + 元数据无损搬运
    
    核心流程：
    1. 使用 Pillow 读取原图，提取并保存 PngInfo（chara等元数据）
    2. 将图片转换为 OpenCV 格式
    3. 调用 watermark_core.add_invisible_watermark 添加频域水印
    4. 将处理后的 OpenCV 图片转回 PIL 格式
    5. 使用 image.save(path, pnginfo=original_metadata) 保存，确保元数据完整搬运
    
    参数：
        input_path: 输入图片路径
        cfg: 配置字典
        user_uuid: Discord用户UUID (如 <@1399304164919742526>)，默认为 'SGP_User'
    """
    print(f"\n{'='*70}")
    filename = os.path.basename(input_path)
    filename_stem = os.path.splitext(filename)[0]
    print(f"处理图片: {filename}")
    print(f"{'='*70}")
    
    try:
        # 1. 读取原图并提取元数据
        print(f"\n[1/4] 读取原图并提取元数据...")
        original_img = Image.open(input_path)
        original_img.load()  # 🔥 确保完全加载图片
        print(f"  ✓ 图片尺寸: {original_img.size[0]} x {original_img.size[1]}")
        print(f"  ✓ 图片模式: {original_img.mode}")
        
        # 🔥 关键修复：提取原图的所有 PNG 元数据（使用 text 而不是 info）
        original_metadata = PngImagePlugin.PngInfo()
        if hasattr(original_img, 'text'):
            # 遍历原图的所有文本块 (包括 'chara')
            for key, value in original_img.text.items():
                original_metadata.add_text(key, value, zip=False)
            
            # 特别检查 chara 字段
            if 'chara' in original_img.text:
                chara_length = len(original_img.text['chara'])
                print(f"  ✓ 检测到原图 chara 元数据（长度: {chara_length} 字符，将原封不动保留）")
            else:
                print(f"  ℹ 原图无 chara 元数据")
        else:
            print(f"  ⚠ 警告: 图片无 text 属性，尝试使用 info 作为后备方案")
            if hasattr(original_img, 'info'):
                for key, value in original_img.info.items():
                    if isinstance(value, (str, bytes)):
                        original_metadata.add_text(key, value if isinstance(value, str) else value.decode('utf-8', errors='ignore'), zip=False)
        
        # 2. 添加频域水印
        print(f"\n[2/4] 添加频域盲水印...")
        
        # 构建动态水印文本（定长换行策略：UUID每12字符一行 + 时间）
        from datetime import datetime
        
        # 清洗UUID（去除<, >, @等符号）
        import re
        cleaned_uuid = re.sub(r'[^0-9]', '', user_uuid)
        
        # 定长换行：每12个字符切分为一行
        MAX_LINE_CHARS = 12
        uuid_lines = []
        for i in range(0, len(cleaned_uuid), MAX_LINE_CHARS):
            uuid_lines.append(cleaned_uuid[i:i+MAX_LINE_CHARS])
        
        # 拼接：UUID行 + 时间
        watermark_lines = uuid_lines + [datetime.now().strftime('%Y-%m-%d %H:%M')]
        dynamic_watermark_text = '\n'.join(watermark_lines)
        
        print(f"  水印内容:")
        for i, line in enumerate(watermark_lines, 1):
            print(f"    第{i}行: {line}")
        
        # 将 PIL 图片转换为 OpenCV 格式进行水印处理
        temp_path = 'temp_for_watermark.png'
        original_img.save(temp_path, 'PNG')
        
        # 调用水印核心模块
        watermarked_array = add_invisible_watermark(
            input_image_path=temp_path,
            output_image_path=None,
            watermark_text=dynamic_watermark_text,
            intensity=cfg['watermark_intensity']
        )
        
        # 清理临时文件
        if os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except PermissionError:
                pass
        
        if watermarked_array is False or watermarked_array is None:
            print("\n  ❌ 水印处理失败")
            return None
        
        print(f"  ✓ 水印注入成功")
        
        # 3. 将 OpenCV 格式转回 PIL 格式
        print(f"\n[3/4] 转换为 PIL 格式...")
        watermarked_rgb = cv2.cvtColor(watermarked_array, cv2.COLOR_BGR2RGB)
        watermarked_img = Image.fromarray(watermarked_rgb)
        print(f"  ✓ 格式转换完成")
        
        # 4. 保存图片（关键：保留原始元数据）
        print(f"\n[4/4] 保存已签名图片...")
        
        # 使用已清洗的UUID作为文件名后缀
        if not cleaned_uuid:
            cleaned_uuid = 'SGP_User'
        
        output_filename = f"{filename_stem}_{cleaned_uuid}.png"
        output_path = os.path.join(cfg['output_dir'], output_filename)
        
        # 🔥 关键步骤：使用 pnginfo 参数保留原图元数据
        watermarked_img.save(output_path, 'PNG', pnginfo=original_metadata)
        
        file_size = os.path.getsize(output_path)
        print(f"  ✓ 已保存: {output_filename}")
        print(f"  ✓ 文件大小: {file_size:,} 字节 ({file_size/1024:.2f} KB)")
        
        # 🔥 验证元数据是否成功保留（使用 text 而不是 info）
        print(f"\n  📋 验证元数据保留...")
        verify_img = Image.open(output_path)
        if hasattr(verify_img, 'text') and 'chara' in verify_img.text:
            saved_chara_length = len(verify_img.text['chara'])
            print(f"  ✅ chara 元数据已成功保留！（长度: {saved_chara_length} 字符）")
        elif hasattr(original_img, 'text') and 'chara' in original_img.text:
            print(f"  ❌ 严重警告: chara 元数据丢失！")
        else:
            print(f"  ℹ 原图无 chara 元数据，无需验证")
        
        print(f"\n{'='*70}")
        print(f"✓ {filename} 处理完成！")
        print(f"{'='*70}")
        
        return output_path
        
    except Exception as e:
        print(f"\n❌ 处理失败: {e}")
        import traceback
        traceback.print_exc()
        return None


def batch_process():
    """批量处理主函数"""
    print("=" * 70)
    print("SGP 水印服务 - 纯水印版权保护系统")
    print("=" * 70)
    
    # 读取Bot指令配置
    config = configparser.ConfigParser()
    config.read('config.ini', encoding='utf-8-sig')
    sign_cmd = config.get('BotCommands', 'sign_cmd', fallback='/bot:制作水印')
    print(f"Discord Bot 调用指令: {sign_cmd}")
    print("=" * 70)
    
    # 1. 加载配置
    print(f"\n[初始化] 加载配置文件...")
    cfg = load_config('config.ini')
    
    print(f"  ✓ 输入目录: {cfg['input_dir']}/")
    print(f"  ✓ 输出目录: {cfg['output_dir']}/")
    print(f"  ✓ 水印文本: {repr(cfg['watermark_text'])}")
    print(f"  ✓ 水印强度: {cfg['watermark_intensity']}")
    print(f"  ✓ 输出后缀: {cfg['output_suffix']}")
    
    # 2. 创建目录
    print(f"\n[初始化] 检查并创建目录...")
    ensure_directories(cfg)
    
    # 3. 扫描输入目录
    print(f"\n[扫描] 搜索图片文件...")
    
    # 支持的图片格式
    image_extensions = ['*.png', '*.jpg', '*.jpeg', '*.PNG', '*.JPG', '*.JPEG']
    image_files = []
    
    for ext in image_extensions:
        pattern = os.path.join(cfg['input_dir'], ext)
        image_files.extend(glob.glob(pattern))
    
    if not image_files:
        print(f"\n  ⚠ 警告: {cfg['input_dir']}/ 目录为空")
        print(f"  请将待处理的图片放入该目录")
        return
    
    print(f"  ✓ 发现 {len(image_files)} 张图片:")
    for i, img_path in enumerate(image_files, 1):
        print(f"    {i}. {os.path.basename(img_path)}")
    
    # 4. 批量处理
    print(f"\n[处理] 开始批量水印注入...")
    print(f"{'='*70}")
    
    success_count = 0
    fail_count = 0
    signed_files = []
    
    for i, img_path in enumerate(image_files, 1):
        print(f"\n进度: [{i}/{len(image_files)}]")
        
        signed_path = process_image(img_path, cfg)
        
        if signed_path:
            success_count += 1
            signed_files.append(signed_path)
        else:
            fail_count += 1
    
    # 5. 输出统计
    print(f"\n{'='*70}")
    print(f"批量处理完成！")
    print(f"{'='*70}")
    print(f"\n统计信息:")
    print(f"  总计: {len(image_files)} 张")
    print(f"  成功: {success_count} 张")
    print(f"  失败: {fail_count} 张")
    
    print(f"\n输出位置:")
    print(f"  已签名图片: {cfg['output_dir']}/")
    
    print(f"\n{'='*70}")
    print(f"💡 提示: 使用审计指令生成水印分析报告")
    print(f"{'='*70}")
    
    return signed_files


if __name__ == '__main__':
    batch_process()
