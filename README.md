# VASP能量提取工具

> *README文档由Anthropic的Claude 3.7 Sonnet AI助手生成。*

![版本](https://img.shields.io/badge/版本-1.0-blue.svg)
![Python版本](https://img.shields.io/badge/Python-3.6%2B-brightgreen.svg)
![许可证](https://img.shields.io/badge/许可证-MIT-green.svg)

一个功能强大的Python脚本，用于从VASP（Vienna Ab initio Simulation Package）计算结果中提取能量数据并进行反应能量计算的工具。

## 功能特点

- **多种能量提取方法**：优先级自动从OSZICAR、OUTCAR和vasprun.xml文件中提取能量
- **灵活的目录扫描**：支持递归和非递归扫描目录，自动识别VASP计算目录
- **反应能量计算**：解析化学反应方程式并计算能量变化
- **多格式数据输出**：同时支持CSV和JSON格式输出
- **详细的日志记录**：提供不同级别的日志输出，便于跟踪问题
- **强大的错误处理**：各种异常情况的优雅处理

## 安装方法

### 环境要求

- Python 3.6 或更高版本
- 无需额外依赖，仅使用Python标准库

### 下载与安装

1. 克隆或下载本仓库
   ```bash
   git clone https://github.com/qxtyxwr/VaspEnergyExtractor.git
   cd VaspEnergyExtractor
   ```

2. 确保脚本具有执行权限（Linux/Mac用户）
   ```bash
   chmod +x vasp_energy_extractor.py
   ```

## 使用方法

### 基本用法

从当前目录中提取VASP计算能量数据：

```bash
python vasp_energy_extractor.py
```

这将扫描当前目录下的所有子目录，提取VASP计算能量并保存到`energies.csv`文件。

### 命令行选项

| 选项 | 简写 | 描述 | 默认值 |
|------|------|------|--------|
| `--directory` | `-d` | 要扫描的根目录 | 当前目录 |
| `--output` | `-o` | 输出CSV文件名 | energies.csv |
| `--recursive` | `-r` | 递归扫描子目录 | False |
| `--verbose` | `-v` | 显示详细日志输出 | False |
| `--json` | `-j` | 指定JSON格式输出文件名 | 不输出JSON |
| `--reactions` | | 包含反应方程式的文件路径 | 不计算反应能量 |

### 高级用法示例

1. **递归扫描特定目录并保存到自定义文件**
   ```bash
   python vasp_energy_extractor.py -d ./my_calculations -o results.csv -r
   ```

2. **输出详细日志并同时保存JSON格式**
   ```bash
   python vasp_energy_extractor.py -v -j energy_data.json
   ```

3. **计算反应能量**
   ```bash
   python vasp_energy_extractor.py -r --reactions reactions.txt
   ```

## 输入/输出格式说明

### 目录结构要求

脚本会自动识别包含以下任一VASP输出文件的目录：
- OSZICAR
- OUTCAR
- vasprun.xml

示例目录结构：
```
calculations/
├── structure1/
│   ├── OSZICAR
│   ├── OUTCAR
│   └── vasprun.xml
├── structure2/
│   ├── OSZICAR
│   └── OUTCAR
└── structure3/
    └── vasprun.xml
```

### CSV输出格式

输出的CSV文件包含以下内容：
- 元数据（创建时间、根目录、扫描方式）
- 结构名称、能量值(eV)和数据来源
- 反应能量计算结果（如果提供了反应文件）

示例：
```
# VASP能量提取结果
# 创建时间: 2025-03-18 12:30:45
# 根目录: /path/to/calculations
# 递归扫描: Yes

结构,能量 (eV),数据来源
structure1,-120.456789,OSZICAR
structure2,-85.123456,OUTCAR
structure3,-150.234567,vasprun.xml

# 反应能量
反应,能量变化 (eV)
structure1 + structure2 -> structure3,-15.098765
```

### JSON输出格式

JSON输出包含三个主要部分：
- metadata：包含时间戳、根目录和扫描方式信息
- energies：包含所有提取的能量数据（结构名、能量值、数据来源）
- reactions：包含反应方程式及其能量变化（如果提供了反应文件）

### 反应文件格式

反应文件中每行包含一个反应方程式，格式如下：
```
A + 2B -> C + 3D
E + F = 2G
# 这是一个注释行
```

支持的格式说明：
- 反应物和产物用 `->` 或 `=` 分隔
- 系数可以是整数或小数
- 以 `#` 开头的行被视为注释并忽略
- 每个物质名称应与提取的能量数据中的目录名匹配

## 工作流示例

### 示例1：能量提取

1. 准备含有多个VASP计算的目录结构
2. 运行脚本提取能量：
   ```bash
   python vasp_energy_extractor.py -d ./calculations -r -o energies.csv
   ```
3. 查看生成的CSV文件了解能量结果

### 示例2：反应能量计算

1. 创建一个包含反应方程式的文本文件`reactions.txt`：
   ```
   TiO2 + 2H2O -> Ti(OH)4
   FeO + 0.5O2 -> Fe2O3
   ```

2. 运行脚本计算反应能量：
   ```bash
   python vasp_energy_extractor.py -d ./calculations -r --reactions reactions.txt -o reaction_energies.csv
   ```

3. 在输出文件中查看反应能量结果

## 故障排除

### 常见问题

1. **未找到VASP计算目录**
   - 确保目录中包含OSZICAR、OUTCAR或vasprun.xml文件
   - 使用`-v`选项获取详细日志查看扫描情况

2. **无法计算反应能量**
   - 确保反应方程式中的物质名称与提取的能量数据中的目录名完全匹配
   - 检查反应方程式格式是否正确（使用`->`或`=`分隔反应物和产物）

3. **能量值异常**
   - 检查VASP计算是否完全收敛
   - 使用`-v`选项查看能量数据来源文件

## 版权与许可

本项目采用MIT许可证。详情请参阅LICENSE文件。

## 作者

qxtyxwr
