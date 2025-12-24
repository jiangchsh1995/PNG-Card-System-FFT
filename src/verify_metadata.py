#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
验证脚本 v0.81 - 读取PNG元数据
"""

from PIL import Image
import json
import base64

def read_metadata(image_path):
    """读取PNG图片的元数据，验证chara字段"""
    try:
        img = Image.open(image_path)
        
        print("=" * 60)
        print(f"读取图片: {image_path}")
        print("=" * 60)
        
        # 获取图片基本信息
        print(f"\n图片信息:")
        print(f"  尺寸: {img.size[0]} x {img.size[1]}")
        print(f"  模式: {img.mode}")
        print(f"  格式: {img.format}")
        
        # 读取所有文本元数据
        print(f"\nPNG元数据:")
        chara_data_found = False
        
        if hasattr(img, 'info'):
            if img.info:
                for key, value in img.info.items():
                    if key in ['chara_data', 'chara']:
                        chara_data_found = True
                        print(f"\n  [{key}]:")
                        print(f"    前80个字符: {value[:80]}...")
                        print(f"    总长度: {len(value)} 字符")
                        
                        # 尝试解析JSON
                        try:
                            data = json.loads(value)
                            print(f"\n" + "=" * 60)
                            print("JSON 根节点所有 Keys:")
                            print("=" * 60)
                            
                            keys = list(data.keys())
                            for i, k in enumerate(keys, 1):
                                print(f"  {i}. {k}")
                            
                            # 检查 extensions 字段
                            print(f"\n" + "=" * 60)
                            print("关键字段验证 - extensions:")
                            print("=" * 60)
                            
                            if 'extensions' in data:
                                extensions = data['extensions']
                                if extensions:
                                    print(f"  ✅ extensions 字段存在且不为空")
                                    print(f"  ✅ extensions 类型: {type(extensions).__name__}")
                                    if isinstance(extensions, dict):
                                        print(f"  ✅ extensions 包含 {len(extensions)} 个子字段:")
                                        for ext_key in extensions.keys():
                                            print(f"      - {ext_key}")
                                    elif isinstance(extensions, list):
                                        print(f"  ✅ extensions 包含 {len(extensions)} 个元素")
                                    print(f"\n  🎉 特效数据完整！")
                                else:
                                    print(f"  ⚠️  extensions 字段存在但为空")
                                    print(f"  ⚠️  特效可能无法运行")
                            else:
                                print(f"  ❌ extensions 字段不存在")
                                print(f"  ❌ 特效无法运行")
                                
                        except json.JSONDecodeError:
                            print(f"\n  ⚠️  chara_data 不是有效的 JSON 格式（可能是加密数据）")
                            print(f"  完整的 chara_data (Base64):")
                            print(f"    {value}")
                    else:
                        print(f"  {key}: {value}")
                        
                if not chara_data_found:
                    print("  ⚠️  未找到 chara_data 字段")
            else:
                print("  (未找到元数据)")
        
        print("\n" + "=" * 60)
        print("✓ 元数据读取成功！")
        print("=" * 60)
        
    except FileNotFoundError:
        print(f"❌ 错误: 找不到文件 '{image_path}'")
    except Exception as e:
        print(f"❌ 错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == '__main__':
    import sys
    
    # 支持命令行参数
    if len(sys.argv) > 1:
        input_image = sys.argv[1]
    else:
        input_image = 'encrypted_card.png'
    
    read_metadata(input_image)
