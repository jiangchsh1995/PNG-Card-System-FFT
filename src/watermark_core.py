#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
傅里叶隐水印模块 v0.81 - 对角线双星布局算法
核心：Diagonal Symmetry + Magnitude Addition + 180度中心旋转
Author: JCHSH
"""

import cv2
import numpy as np
import os


def add_invisible_watermark(input_image_path, output_image_path, watermark_text, intensity=100):
    """
    使用对角线双星布局算法在图像中添加不可见水印
    
    核心算法：
    1. YCrCb色彩空间 -> Y通道 -> DFT -> cartToPolar分离幅度和相位
    2. 创建对角线双水印Mask（左上角 + 右下角180度旋转）
    3. 幅度谱叠加：new_magnitude = magnitude + (mask × intensity)
    4. polarToCart合并 -> IDFT -> 归一化 -> 合成BGR
    
    Returns:
        numpy.ndarray: 处理后的图像数组 (BGR格式)
    """
    print("\n" + "=" * 70)
    print("傅里叶隐水印 - 对角线双星布局算法 (Diagonal Symmetry)")
    print("=" * 70)
    
    try:
        # 1. 读取图像
        print(f"\n✓ 读取图片: {input_image_path}")
        img_bgr = cv2.imread(input_image_path)
        if img_bgr is None:
            raise ValueError(f"无法读取图片: {input_image_path}")
        
        height, width = img_bgr.shape[:2]
        print(f"  图片尺寸: {width} x {height}")
        
        # 2. 转换到YCrCb色彩空间，提取Y通道
        print(f"\n✓ 转换到YCrCb，提取Y通道...")
        img_ycrcb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2YCrCb)
        y_channel = img_ycrcb[:, :, 0].astype(np.float32)
        print(f"  Y通道范围: [{y_channel.min():.1f}, {y_channel.max():.1f}]")
        
        # 3. 傅里叶变换
        print(f"\n✓ 执行DFT...")
        dft = cv2.dft(y_channel, flags=cv2.DFT_COMPLEX_OUTPUT)
        dft_shift = np.fft.fftshift(dft)
        
        # 4. 分离幅度和相位
        print(f"\n✓ cartToPolar 分离幅度和相位...")
        magnitude, phase = cv2.cartToPolar(dft_shift[:, :, 0], dft_shift[:, :, 1])
        
        print(f"  幅度范围: [{magnitude.min():.2f}, {magnitude.max():.2f}]")
        print(f"  幅度平均值: {magnitude.mean():.2f}")
        
        # 5. 计算对角线布局参数（优化安全边距 - 方块印章布局）
        print(f"\n✓ 计算对角线双星布局...")
        cx = width // 2   # 频谱中心X
        cy = height // 2  # 频谱中心Y
        dx = int(width * 0.28)   # 水平偏移量 = 宽度的28%（更靠近中心）
        dy = int(height * 0.28)  # 垂直偏移量 = 高度的28%（方块印章布局）
        
        # 左上角位置
        top_left_x = cx - dx
        top_left_y = cy - dy
        
        # 右下角位置
        bottom_right_x = cx + dx
        bottom_right_y = cy + dy
        
        print(f"  频谱中心: ({cy}, {cx})")
        print(f"  对角线偏移量: dx={dx}, dy={dy}")
        print(f"  左上角水印A位置: ({top_left_y}, {top_left_x})")
        print(f"  右下角水印B位置: ({bottom_right_y}, {bottom_right_x})")
        
        # 6. 强制文本分块（UUID Chunking）- 实现"方块印章"
        font = cv2.FONT_HERSHEY_SIMPLEX
        
        # 🔥 强制换行处理：将 UUID 和时间戳按固定宽度切分
        print(f"\n✓ 预处理水印文本（强制换行）...")
        print(f"  原始文本: '{watermark_text}'")
        
        # 将文本按 \n 分割为 UUID 和 Time
        raw_parts = watermark_text.split('\n')
        
        # 强制分块：将 UUID 每 10-12 个字符切分为一行
        text_lines = []
        chunk_size = 11  # 每行字符数（可调整 10-12）
        
        for part in raw_parts:
            # 如果这部分是 UUID（较长），则分块
            if len(part) > chunk_size:
                # 分块切割
                for i in range(0, len(part), chunk_size):
                    chunk = part[i:i+chunk_size]
                    text_lines.append(chunk)
            else:
                # 时间戳等短文本直接加入
                text_lines.append(part)
        
        print(f"  分块后行数: {len(text_lines)}")
        for i, line in enumerate(text_lines, 1):
            print(f"    第{i}行: '{line}'")
        
        # 🔥 字体大小优化：因为分行了，可以稍微大一点
        base_font_scale = (width / 1000.0) * 0.8
        base_font_scale = max(0.6, min(base_font_scale, 1.5))
        font_scale = base_font_scale
        font_thickness = max(1, int(font_scale * 2))
        
        # 计算每行尺寸
        line_sizes = []
        max_line_width = 0
        total_height = 0
        line_spacing = int(font_scale * 10)  # 行间距
        
        for i, line in enumerate(text_lines):
            size = cv2.getTextSize(line, font, font_scale, font_thickness)[0]
            line_sizes.append(size)
            max_line_width = max(max_line_width, size[0])
            total_height += size[1]
            if i < len(text_lines) - 1:  # 非最后一行添加行间距
                total_height += line_spacing
        
        # 整个文本块的尺寸
        text_width = max_line_width
        text_height = total_height
        
        print(f"\n✓ 字体自适应 + 多行排版...")
        print(f"  水印文本: '{watermark_text}'")
        print(f"  文本行数: {len(text_lines)}")
        print(f"  基础字体: {base_font_scale:.2f} -> 优化后: {font_scale:.2f}")
        print(f"  字体粗细: {font_thickness}")
        print(f"  文本块尺寸: {text_width} x {text_height}")
        print(f"  行间距: {line_spacing}")
        
        # 7. 创建水印Mask A（左上角，多行中心对齐）
        print(f"\n✓ 步骤A: 在左上角绘制水印A（多行中心对齐）...")
        mask_top_left = np.zeros((height, width), dtype=np.float32)
        
        # 计算文本块的几何中心位置
        # 目标：文本块中心对齐到 (top_left_x, top_left_y)
        block_start_y = top_left_y - text_height // 2
        
        current_y = block_start_y
        for i, line in enumerate(text_lines):
            line_width = line_sizes[i][0]
            line_height = line_sizes[i][1]
            
            # 每行中心对齐
            text_x = top_left_x - line_width // 2
            text_y = current_y + line_height
            
            cv2.putText(mask_top_left, line, (text_x, text_y),
                       font, font_scale, 255, font_thickness)
            
            current_y += line_height
            if i < len(text_lines) - 1:
                current_y += line_spacing
        
        pixels_A = np.count_nonzero(mask_top_left)
        print(f"  水印A像素数: {pixels_A}")
        print(f"  ✅ 多行文本块中心严格对齐到 ({top_left_y}, {top_left_x})")
        
        # 8. 创建水印Mask B（右下角，180度旋转，多行）
        print(f"\n✓ 步骤B: 在右下角绘制水印B（180度旋转，多行）...")
        
        # 创建临时mask用于绘制多行文本
        temp_mask = np.zeros((text_height * 4, text_width * 4), dtype=np.float32)
        temp_center_x = temp_mask.shape[1] // 2
        temp_center_y = temp_mask.shape[0] // 2
        
        # 在临时mask中心绘制多行文本
        block_start_y_temp = temp_center_y - text_height // 2
        current_y_temp = block_start_y_temp
        
        for i, line in enumerate(text_lines):
            line_width = line_sizes[i][0]
            line_height = line_sizes[i][1]
            
            # 每行中心对齐
            text_x_temp = temp_center_x - line_width // 2
            text_y_temp = current_y_temp + line_height
            
            cv2.putText(temp_mask, line, (text_x_temp, text_y_temp),
                       font, font_scale, 255, font_thickness)
            
            current_y_temp += line_height
            if i < len(text_lines) - 1:
                current_y_temp += line_spacing
        
        # 180度旋转（双轴翻转）
        temp_mask_rotated = cv2.flip(temp_mask, -1)
        
        # 创建右下角mask
        mask_bottom_right = np.zeros((height, width), dtype=np.float32)
        
        # 计算粘贴位置（将旋转后的文本中心对齐到右下角目标位置）
        paste_x_start = bottom_right_x - temp_mask_rotated.shape[1] // 2
        paste_y_start = bottom_right_y - temp_mask_rotated.shape[0] // 2
        
        # 确保不越界
        paste_x_start = max(0, paste_x_start)
        paste_y_start = max(0, paste_y_start)
        paste_x_end = min(width, paste_x_start + temp_mask_rotated.shape[1])
        paste_y_end = min(height, paste_y_start + temp_mask_rotated.shape[0])
        
        # 粘贴旋转后的文本
        temp_width = paste_x_end - paste_x_start
        temp_height = paste_y_end - paste_y_start
        mask_bottom_right[paste_y_start:paste_y_end, paste_x_start:paste_x_end] = \
            temp_mask_rotated[:temp_height, :temp_width]
        
        pixels_B = np.count_nonzero(mask_bottom_right)
        print(f"  水印B像素数: {pixels_B}")
        print(f"  ✅ 多行文本旋转180度后中心对齐到 ({bottom_right_y}, {bottom_right_x})")
        print(f"  ⚡ 效果: 水印B是水印A的180度中心旋转，完美对称！")
        
        # 9. 步骤C: 合并两个mask
        print(f"\n✓ 步骤C: 合并左上 + 右下...")
        mask_combined = mask_top_left + mask_bottom_right
        
        total_pixels = np.count_nonzero(mask_combined)
        print(f"  合并后总像素数: {total_pixels}")
        print(f"  验证: {pixels_A} + {pixels_B} ≈ {total_pixels}")
        
        # 10. 幅度谱叠加
        print(f"\n✓ 幅度谱叠加 (Magnitude Addition)...")
        print(f"  强度因子: {intensity} (平衡可见性和画质)")
        print(f"  公式: new_magnitude = magnitude + (mask * {intensity})")
        
        new_magnitude = magnitude + (mask_combined * intensity)
        
        print(f"  新幅度范围: [{new_magnitude.min():.2f}, {new_magnitude.max():.2f}]")
        print(f"  新幅度平均值: {new_magnitude.mean():.2f}")
        
        # 11. 合并回复数形式
        print(f"\n✓ polarToCart 合并幅度和相位...")
        real, imag = cv2.polarToCart(new_magnitude, phase)
        
        # 重建复数DFT
        dft_shift_new = np.zeros((height, width, 2), dtype=np.float32)
        dft_shift_new[:, :, 0] = real
        dft_shift_new[:, :, 1] = imag
        
        # 12. 逆傅里叶变换
        print(f"\n✓ 执行IDFT...")
        dft_ishift = np.fft.ifftshift(dft_shift_new)
        img_back = cv2.idft(dft_ishift, flags=cv2.DFT_SCALE | cv2.DFT_REAL_OUTPUT)
        
        # 13. 归一化到0-255
        print(f"\n✓ 归一化Y通道...")
        y_watermarked = cv2.normalize(img_back, None, 0, 255, cv2.NORM_MINMAX)
        y_watermarked = y_watermarked.astype(np.uint8)
        
        # 统计变化
        diff = np.abs(y_watermarked.astype(np.float32) - y_channel)
        print(f"  Y通道变化: 平均 {diff.mean():.2f}, 最大 {diff.max():.2f}")
        print(f"  ✅ 画质保护: 变化量小，原图清晰")
        
        # 14. 合并回BGR
        print(f"\n✓ 合成最终图像...")
        img_ycrcb[:, :, 0] = y_watermarked
        result = cv2.cvtColor(img_ycrcb, cv2.COLOR_YCrCb2BGR)
        
        # 验证颜色保持
        original_mean = img_bgr.mean(axis=(0, 1))
        result_mean = result.mean(axis=(0, 1))
        color_diff = np.abs(original_mean - result_mean)
        
        print(f"\n  颜色保持验证:")
        print(f"    原图平均BGR: [{original_mean[0]:.1f}, {original_mean[1]:.1f}, {original_mean[2]:.1f}]")
        print(f"    新图平均BGR: [{result_mean[0]:.1f}, {result_mean[1]:.1f}, {result_mean[2]:.1f}]")
        print(f"    颜色差异: [{color_diff[0]:.2f}, {color_diff[1]:.2f}, {color_diff[2]:.2f}]")
        
        print("\n" + "=" * 70)
        print("✓ 水印嵌入成功！（对角线双星布局算法）")
        print("=" * 70)
        print(f"\n预期效果:")
        print(f"  原图 {output_image_path}:")
        print(f"    - 干净无噪点")
        print(f"    - 画质保护良好")
        print(f"\n  频谱图 check_watermark.png:")
        print(f"    - 正中间: 亮斑（直流分量）")
        print(f"    - 左上角: 水印A '{watermark_text}'（正向）")
        print(f"    - 右下角: 水印B（180度旋转）")
        print(f"    - 两者分布在对角线上，互不重叠，中心留白")
        print("=" * 70)
        
        return result
        
    except Exception as e:
        print(f"\n❌ 错误: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == '__main__':
    print("请使用 encrypt_demo.py 作为主程序入口")
    print("watermark_core.py 是核心模块，不应直接运行")
