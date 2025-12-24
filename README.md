# SGP Protocol (ShadowGuard Protocol)

**基于频域的抗干扰盲水印系统**  
**Author: JCHSH**

---

## 📋 项目简介

SGP Protocol 是一个专业的频域盲水印版权保护系统，支持 Discord Bot 集成。系统采用对角线双星布局算法，在频域嵌入不可见水印，同时保持图像画质和元数据的完整性。

### 🎯 核心特性

- **AES-256 级隐形性**：水印完全不可见，肉眼无法察觉
- **双星对角线布局**：对称分布的频域水印，抗裁剪、抗压缩
- **元数据无损搬运**：完整保留 PNG 元数据（包括 chara 等字段）
- **Discord Bot 集成**：支持通过 Bot 指令调用
- **多行动态水印**：支持用户 UUID、时间戳等动态信息

---

## 🚀 快速开始

### 安装依赖

```bash
pip install -r requirements.txt
```

### 使用方法

#### 制作水印

```bash
python main.py sign
```

将 `input_images/` 目录中的图片添加频域盲水印，输出到 `output_signed/`。

#### 查询水印

```bash
python main.py check
```

分析已签名图片，生成频谱报告到 `output_reports/`。

---

## 📁 目录结构

```
cloud-backend/
├── src/                       # 核心代码
│   ├── watermark_service.py   # 水印服务
│   ├── watermark_core.py      # 核心算法
│   └── audit_service.py       # 审计分析
│
├── input_images/              # 输入目录
├── output_signed/             # 已签名图片
├── output_reports/            # 分析报告
│
├── main.py                    # 主程序
├── config.ini                 # 配置文件
├── requirements.txt           # 依赖列表
└── README.md                  # 项目文档
```

---

## ⚙️ 配置说明

编辑 `config.ini` 自定义水印参数：

```ini
[Watermark]
intensity = 100                # 水印强度（推荐 100）

[BotCommands]
sign_cmd = /bot:制作水印       # Discord Bot 制作指令
check_cmd = /bot:查询水印      # Discord Bot 查询指令
```

---

## 🔬 技术原理

### 对角线双星布局算法

1. **频域变换**：YCrCb → DFT → 幅度谱分离
2. **对称嵌入**：左上角 + 右下角（180° 旋转）
3. **幅度叠加**：`new_magnitude = magnitude + mask × intensity`
4. **逆变换**：IDFT → BGR 合成
5. **元数据保留**：使用 `pnginfo` 参数完整搬运

### 核心优势

- **抗干扰**：频域水印抗裁剪、压缩、滤波
- **不可见**：仅在频谱中可见，空域完全隐形
- **可验证**：生成黑白频谱图用于人工裸眼检查

---

## 📧 Discord Bot 集成

系统支持通过 Discord Bot 调用：

```python
# 动态传入用户 UUID 和时间戳
process_image(input_path, cfg, user_uuid='<@1399304164919742526>')
```

水印内容将自动包含：
- 第一行：用户 UUID（例如 `<@1399304164919742526>`）
- 第二行：本地时间戳（精确到分钟，格式：`YYYY-MM-DD HH:MM`）

---

## 📄 许可证

本项目遵循 MIT 许可证。

---

**© 2025 JCHSH - SGP Protocol**
