# Alpaca 翻译流水线

[English](README.md) · **简体中文**

Alpaca Translation Pipeline 是一个可复现的工作流程，用于识别、清洗、翻译 Alpaca 格式指令数据集中的中文文本，并将译文合并回原数据集。它由早期一次性的数据清洗项目整理而来，正在重构为带测试与明确数据来源记录的小型命令行工具。

本仓库只包含处理代码与小规模示例。在确认原始数据的许可与发布权之前，不会分发原始及翻译后的完整数据集。

## 项目状态

历史流程已成功生成一份翻译后的工作副本。本仓库将该工作整合为可安装的命令行工具，支持原子化 JSON 写入、可续跑的翻译输出、合并完整性报告与测试。

| 阶段 | 历史实现 | 计划发布 |
| --- | --- | --- |
| 中文文本检测 | 已有 | 整合并测试 |
| 候选清洗 | 已有 | 保证对齐的清洗 |
| 翻译与重试 | 已有 | 可续跑执行 |
| 合并回原数据集 | 已有 | 带校验的合并报告 |
| 命令行接口 | 已有 | 五个子命令 |
| 自动化测试 | 已包含 | 无需联网 |

## 项目动机

即使预期以英文为主的指令数据集，也可能混有多语言条目。翻译整个数据集会浪费请求、改动本已正确的内容，并使失败难以追查。本流程只处理含中文的字段，其余内容保持不变。

## 流程

```text
Alpaca JSON 输入
      |
      v
检测含中文的字段
      |
      v
去除空字段与不含中文的候选字段
      |
      v
带重试地翻译 instruction / output 字段
      |
      v
将译文合并到原数据集的副本中
      |
      v
校验记录数、字段与残留中文
```

每个阶段都写出新的文件，原始输入应保持不变。

## 输入格式

默认结构遵循常见的 Alpaca 记录格式：

```json
[
  {
    "system": "",
    "instruction": "",
    "input": "",
    "output": ""
  }
]
```

清洗步骤也将支持选择需要翻译的字符串字段，而不默认只处理 `instruction` 与 `output`。

## 历史工作快照

用于设计本项目的本地科研副本包含：

| 数据 | 条目数 |
| --- | ---: |
| 原始 Alpaca 格式数据集 | 37,168 |
| 初步抽取的中文路径 / 对象 | 10,623 |
| 清洗后的翻译候选 | 3,928 |
| 最终合并数据集 | 37,168 |

以上数字记录的是历史实验，不代表对其他输入数据集的保证。

## 仓库结构

```text
alpaca-translation-pipeline/
├── src/alpaca_translation/
│   ├── detect.py
│   ├── clean.py
│   ├── translate.py
│   ├── merge.py
│   ├── validate.py
│   └── cli.py
├── data/
│   └── samples/
├── tests/
├── pyproject.toml
└── README.md
```

大型输入、输出、日志与检查点应保存在仓库之外。

## 安装

创建独立环境并安装：

```bash
git clone <repository-url>
cd alpaca-translation-pipeline
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e '.[google]'
```

`google` 可选依赖会安装 `deep-translator`。检测、清洗、合并、校验及测试均无需联网，也不依赖翻译库。

## 命令行接口

```bash
# 查找含中文的记录
python -m alpaca_translation detect \
  --input dataset.json \
  --output work/candidates.json

# 去除重复路径与不合适的候选
python -m alpaca_translation clean \
  --input work/candidates.json \
  --output work/candidates-cleaned.json

# 翻译选定字段，进度可续跑
python -m alpaca_translation translate \
  --input work/candidates-cleaned.json \
  --output work/candidates-translated.json \
  --source zh-CN \
  --target en

# 将译文合并到原数据集的副本中
python -m alpaca_translation merge \
  --original dataset.json \
  --translations work/candidates-translated.json \
  --output work/dataset-translated.json \
  --report work/merge-report.json
```

## 安全与校验规则

整理后的实现应遵守以下规则：

- 默认不覆盖原始数据集。
- 合并时保持记录顺序与总数。
- 未选定翻译的字段保持不变。
- 保存进度，使中断的翻译任务可以续跑。
- 对暂时性翻译失败进行有上限的指数退避重试。
- 记录失败及未改变的翻译，且不在日志中写入密钥。
- 报告合并后残留的中文文本。
- 每个阶段都校验 JSON 语法与预期结构。

## 翻译质量

机器翻译可能改变专业术语、代码、公式、专有名词、格式以及安全相关内容。接口返回成功并不代表翻译正确。在用于训练或评测前，应抽取具有统计意义的样本进行审阅，并人工检查重要记录。

为便于复现，正式发布应记录翻译后端、源语言与目标语言、执行日期、依赖版本、过滤规则、重试策略，以及输入输出文件的哈希值。

## 数据来源与发布政策

当前输入文件名表明数据下载自外部数据集平台，但具体的数据集说明与许可尚未确认。因此：

- 不包含完整的原始数据集。
- 不包含完整的翻译后数据集。
- 只提交小规模的合成示例或明确可再分发的示例。
- 未来如发布数据，须注明确切的来源数据集，并遵守其许可与署名要求。

若允许再分发，大型生成数据更适合作为带版本号的数据集发布，而不是反复提交到 Git 历史中。

## 已知局限

- 当前检测器主要针对基本 CJK 统一汉字区段。
- 以英文为主的启发式判断可能误判中英混合的技术文本。
- 历史翻译脚本按顺序发送网络请求，速度可能较慢。
- 翻译服务的行为可能随时间变化。
- 旧脚本使用固定文件名，其中一个使用了已失效的 Windows 路径。
- 历史日志体积较大，不应提交。

## 参与贡献

首个打包版本发布后欢迎贡献，尤其是语言检测测试、可续跑翻译、后端适配、结构校验、术语保留与合并完整性检查等方面。

请勿提交私有数据、访问凭证，或未明确允许再分发的第三方数据集。

## 引用

正式引用格式将随首个版本发布提供。在此之前，请引用仓库地址及所用的具体 commit。

## 许可

尚未选定公开许可。代码许可与未来数据集许可将在确认所有权及来源数据义务后另行说明。
