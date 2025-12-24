#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
SGP 审计分析服务 v1.0 - Discord Bot 查询模块
功能：生成水印签名图片的黑白频谱分析报告
Author: JCHSH
"""

import cv2
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import font_manager
import os
import configparser
import glob

# 配置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS', 'DejaVu Sans']
plt.rcParams['axes.unicode_minus'] = False  # 解决负号显示问题


def load_config(config_file='config.ini'):
    """加载配置文件"""
    config = configparser.ConfigParser()
    
    if not os.path.exists(config_file):
        return {
            'report_dir': 'output_reports'
        }
    
    config.read(config_file, encoding='utf-8-sig')
    report_dir = config.get('Paths', 'report_dir', fallback='output_reports')
    
    return {
        'report_dir': report_dir
    }


def analyze_single_image(watermarked_path, original_path=None, save_dir='output_reports'):
    """分析单张水印签名图片，生成黑白频谱对比报告"""
    
    filename = os.path.basename(watermarked_path)
    filename_stem = os.path.splitext(filename)[0]
    
    print(f"\n{'='*70}")
    print(f"SGP 审计分析 - {filename_stem}")
    print(f"{'='*70}")
    
    try:
        # 确保输出目录存在
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)
            print(f"  ✓ 创建目录: {save_dir}/")
        
        # 1. 检查文件是否存在
        if not os.path.exists(watermarked_path):
            print(f"  ❌ 错误: 找不到已签名图 {watermarked_path}")
            return None
        
        print(f"  ✓ 加载已签名图: {os.path.basename(watermarked_path)}")
        
        # 2. 读取已签名图
        img_watermarked = cv2.imread(watermarked_path)
        
        if img_watermarked is None:
            print("  ❌ 错误: 图像加载失败")
            return None
        
        height, width = img_watermarked.shape[:2]
        print(f"  图片尺寸: {width} x {height}")
        
        # 3. 计算黑白频谱（使用灰度图以清晰展示水印痕迹）
        print("  ✓ 计算黑白频谱...")
        
        # 已签名图 -> 灰度 -> DFT 频谱
        gray_watermarked = cv2.cvtColor(img_watermarked, cv2.COLOR_BGR2GRAY).astype(np.float32)
        dft_watermarked = cv2.dft(gray_watermarked, flags=cv2.DFT_COMPLEX_OUTPUT)
        dft_shift_watermarked = np.fft.fftshift(dft_watermarked)
        magnitude_watermarked = cv2.magnitude(dft_shift_watermarked[:, :, 0], dft_shift_watermarked[:, :, 1])
        magnitude_spectrum_watermarked = np.log(magnitude_watermarked + 1)
        
        print(f"  频谱范围: [{magnitude_spectrum_watermarked.min():.2f}, {magnitude_spectrum_watermarked.max():.2f}]")
        
        # 4. 生成纯净的黑白频谱图（无标注，用于人工裸眼检查）
        print("  ✓ 生成纯净黑白频谱图...")
        
        fig_spectrum = plt.figure(figsize=(10, 8))
        ax_spectrum = plt.subplot(1, 1, 1)
        
        im_spectrum = ax_spectrum.imshow(magnitude_spectrum_watermarked, cmap='gray', aspect='auto')
        ax_spectrum.axis('off')
        
        plt.tight_layout(pad=0)
        
        # 保存纯净的黑白频谱图（无任何标记）
        spectrum_file = os.path.join(save_dir, f"{filename_stem}_Spectrum_Gray.png")
        plt.savefig(spectrum_file, dpi=150, bbox_inches='tight', pad_inches=0)
        plt.close(fig_spectrum)
        
        print(f"  ✓ 已保存纯净频谱: {os.path.basename(spectrum_file)}")
        
        result = {
            'spectrum_file': spectrum_file
        }
        
        # 5. 如果有原图，生成完整的5图报告
        if original_path and os.path.exists(original_path):
            print("  ✓ 检测到原图，生成完整5图报告...")
            
            img_original = cv2.imread(original_path)
            if img_original is not None:
                report_file = generate_full_report(
                    img_original, img_watermarked,
                    magnitude_spectrum_watermarked,
                    filename_stem, save_dir,
                    width, height
                )
                result['report_file'] = report_file
        
        print(f"\n{'='*70}")
        print(f"✓ 审计分析完成！")
        print(f"{'='*70}")
        
        return result
        
    except Exception as e:
        print(f"  ❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        return None


def generate_full_report(img_original, img_watermarked, magnitude_spectrum_watermarked,
                         filename_stem, save_dir, width, height):
    """生成完整的5图联动分析报告"""
    
    # 转换为RGB用于显示
    img_original_rgb = cv2.cvtColor(img_original, cv2.COLOR_BGR2RGB)
    img_watermarked_rgb = cv2.cvtColor(img_watermarked, cv2.COLOR_BGR2RGB)
    
    # 计算原图黑白频谱
    gray_original = cv2.cvtColor(img_original, cv2.COLOR_BGR2GRAY).astype(np.float32)
    dft_original = cv2.dft(gray_original, flags=cv2.DFT_COMPLEX_OUTPUT)
    dft_shift_original = np.fft.fftshift(dft_original)
    magnitude_original = cv2.magnitude(dft_shift_original[:, :, 0], dft_shift_original[:, :, 1])
    magnitude_spectrum_original = np.log(magnitude_original + 1)
    
    # 计算水印位置（与 watermark_core.py 保持一致）
    cx = width // 2
    cy = height // 2
    dx = int(width * 0.28)
    dy = int(height * 0.28)
    watermark_row = cy - dy
    
    # 提取能量数据
    energy_original = magnitude_spectrum_original[watermark_row, :]
    energy_watermarked = magnitude_spectrum_watermarked[watermark_row, :]
    
    # 创建横向1x4 + Bottom布局（使用GridSpec）
    from matplotlib.gridspec import GridSpec
    
    fig = plt.figure(figsize=(24, 12))
    gs = GridSpec(2, 4, figure=fig, height_ratios=[1, 0.8], hspace=0.3, wspace=0.3)
    
    # 第一排：横向4张图 [原图 | 原图频谱(无标注) | 已签名图 | 已签名图频谱(带星星)]
    # 子图1: 原图
    ax1 = fig.add_subplot(gs[0, 0])
    ax1.imshow(img_original_rgb)
    ax1.set_title('1. 原始图像', fontsize=13, fontweight='bold', color='#2E86AB')
    ax1.axis('off')
    
    # 子图2: 原图黑白频谱（无标注）
    ax2 = fig.add_subplot(gs[0, 1])
    im2 = ax2.imshow(magnitude_spectrum_original, cmap='gray', aspect='auto')
    ax2.set_title('2. 原始频谱（无标注）', fontsize=13, fontweight='bold', color='#2E86AB')
    ax2.axis('off')
    
    # 子图3: 已签名图
    ax3 = fig.add_subplot(gs[0, 2])
    ax3.imshow(img_watermarked_rgb)
    ax3.set_title('3. 已签名图像 (Signed)', fontsize=13, fontweight='bold', color='#A23B72')
    ax3.axis('off')
    
    # 子图4: 已签名图黑白频谱（带星星标注位置）
    ax4 = fig.add_subplot(gs[0, 3])
    im4 = ax4.imshow(magnitude_spectrum_watermarked, cmap='gray', aspect='auto')
    ax4.set_title('4. 已签名频谱\n★ 对角线水印清晰可见 ★', 
                  fontsize=13, fontweight='bold', color='#A23B72')
    ax4.set_xlabel('频率 X', fontsize=9)
    ax4.set_ylabel('频率 Y', fontsize=9)
    
    # 标注水印位置（星星标记）
    top_left_x = cx - dx
    top_left_y = cy - dy
    bottom_right_x = cx + dx
    bottom_right_y = cy + dy
    
    ax4.plot(top_left_x, top_left_y, 'r*', markersize=20, label='左上水印', 
            markeredgecolor='yellow', markeredgewidth=2)
    ax4.plot(bottom_right_x, bottom_right_y, 'y*', markersize=20, label='右下水印',
            markeredgecolor='red', markeredgewidth=2)
    ax4.legend(loc='upper right', fontsize=10, framealpha=0.9)
    
    # 第二排：能量波峰分析图（横跨全宽，GridSpec[1, :]）
    ax5 = fig.add_subplot(gs[1, :])
    x_axis = np.arange(len(energy_original))
    
    ax5.plot(x_axis, energy_original, 'b--', linewidth=1.5, alpha=0.7, label='原图能量')
    ax5.plot(x_axis, energy_watermarked, 'r-', linewidth=2, alpha=0.9, label='已签名图能量')
    
    ax5.set_title(f'5. 能量波峰分析 (Waveform Analysis)\n水印行 #{watermark_row} - 红蓝对比显示水印能量激增',
                  fontsize=14, fontweight='bold', color='#F18F01')
    ax5.set_xlabel('频率位置 (Pixel)', fontsize=11)
    ax5.set_ylabel('能量强度 (Log Scale)', fontsize=11)
    ax5.legend(loc='upper right', fontsize=11)
    ax5.grid(True, alpha=0.3, linestyle='--')
    
    # 突出显示差异区域
    diff = energy_watermarked - energy_original
    ax5.fill_between(x_axis, energy_original, energy_watermarked,
                     where=(diff > 0.5), alpha=0.3, color='red',
                     label='水印能量增强区')
    
    # 总标题
    fig.suptitle(f'SGP审计分析 - 完整报告: {filename_stem}\n对角线双星布局算法 + 幅度谱叠加法',
                 fontsize=16, fontweight='bold', y=0.98)
    
    plt.tight_layout(rect=[0, 0, 1, 0.96])
    
    # 保存报告
    report_file = os.path.join(save_dir, f"{filename_stem}_Report.png")
    plt.savefig(report_file, dpi=150, bbox_inches='tight')
    plt.close(fig)
    
    file_size = os.path.getsize(report_file)
    print(f"  ✓ 已保存完整报告: {os.path.basename(report_file)}")
    print(f"  文件大小: {file_size:,} 字节 ({file_size/1024/1024:.2f} MB)")
    
    return report_file


def batch_analyze(watermarked_dir='output_encrypted', original_dir='input_images', save_dir=None):
    """批量分析已签名图片，生成频谱报告"""
    
    if save_dir is None:
        cfg = load_config()
        save_dir = cfg['report_dir']
    
    print("=" * 70)
    print("SGP 审计分析服务 - 批量模式")
    print("=" * 70)
    
    # 读取Bot指令配置
    config = configparser.ConfigParser()
    config.read('config.ini', encoding='utf-8-sig')
    check_cmd = config.get('BotCommands', 'check_cmd', fallback='/bot:查询水印')
    print(f"Discord Bot 调用指令: {check_cmd}")
    print("=" * 70)
    
    # 扫描已签名图
    image_extensions = ['*.png', '*.jpg', '*.jpeg', '*.PNG', '*.JPG', '*.JPEG']
    watermarked_files = []
    
    for ext in image_extensions:
        pattern = os.path.join(watermarked_dir, ext)
        watermarked_files.extend(glob.glob(pattern))
    
    if not watermarked_files:
        print(f"\n  ⚠ 警告: {watermarked_dir}/ 目录为空")
        return []
    
    print(f"\n  ✓ 发现 {len(watermarked_files)} 张已签名图片")
    
    results = []
    
    for i, watermarked_path in enumerate(watermarked_files, 1):
        print(f"\n进度: [{i}/{len(watermarked_files)}]")
        
        # 尝试查找对应的原图
        filename = os.path.basename(watermarked_path)
        # 移除 _SGP_Signed 或 _SGP_Encrypted 后缀（兼容旧文件）
        if '_SGP_Signed' in filename:
            original_name = filename.replace('_SGP_Signed', '')
        elif '_SGP_Encrypted' in filename:
            original_name = filename.replace('_SGP_Encrypted', '')
        else:
            original_name = None
        
        if original_name:
            original_path = os.path.join(original_dir, original_name)
            if not os.path.exists(original_path):
                original_path = None
        else:
            original_path = None
        
        result = analyze_single_image(watermarked_path, original_path, save_dir)
        if result:
            results.append(result)
    
    print(f"\n{'='*70}")
    print(f"批量分析完成！")
    print(f"{'='*70}")
    print(f"\n统计信息:")
    print(f"  总计: {len(watermarked_files)} 张")
    print(f"  成功: {len(results)} 张")
    print(f"  失败: {len(watermarked_files) - len(results)} 张")
    
    print(f"\n输出位置:")
    print(f"  分析报告: {save_dir}/")
    
    return results


if __name__ == '__main__':
    batch_analyze()
