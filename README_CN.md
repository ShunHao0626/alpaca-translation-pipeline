# Alpaca 翻译流水线

[English](README.md) · **简体中文**

本仓库为 Alpaca 格式指令数据集提供五阶段命令行流水线：识别含中文的字段、清洗候选、带检查点的翻译、按记录索引合并，以及输出校验。

在一次 **37,168 条记录**的处理实例中，清洗后得到 **3,928 个翻译候选**，合并后记录总数保持不变。仓库提供可复用工具、测试和小规模示例。

## 流水线实现

可安装工具支持原子化 JSON 写入、断点续跑、合并完整性报告和离线测试；各阶段的输出便于逐条追踪数据变化。

| 阶段 | 当前软件包 |
| --- | --- |
| 中文文本检测 | `detect`，可配置字段，已测试 |
| 候选清洗 | `clean`，保持记录索引对齐 |
| 翻译与重试 | `translate`，Google 后端，有上限的重试，检查点与续跑 |
| 合并回原数据集 | `merge`，写出副本及计数报告 |
| 数据集检查 | `validate`，报告残留的中文字段 |
| 自动化测试 | 已包含，无需联网 |

## 适用场景

即使预期以英文为主的指令数据集，也可能混有多语言条目。翻译整个数据集会浪费请求、改动本已正确的内容，并使失败难以追查。本流程只处理含中文的字段，其余内容保持不变。

## 流程

```text
Alpaca JSON 输入
      |
      v
检测含中文的字段
      |
      v
去除空字段与不含中文的候选字段（保留重复文本）
      |
      v
带有限次重试地翻译检测到的字段
      |
      v
将译文字段合并到原数据集的副本中
      |
      v
检查记录结构并报告残留中文
```

每个阶段都写出新的文件。工具不会检查输出路径是否与输入路径相同，请自行选择不会覆盖原始输入的输出路径。

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

默认扫描 `system`、`instruction`、`input` 与 `output` 四个字段。`detect`、`merge` 与 `validate` 支持 `--fields`，可用逗号分隔的列表指定其他字符串字段。

## 处理实例

该次处理记录包含：

| 数据 | 条目数 |
| --- | ---: |
| 原始 Alpaca 格式数据集 | 37,168 |
| 初步抽取的中文路径 / 对象 | 10,623 |
| 清洗后的翻译候选 | 3,928 |
| 最终合并数据集 | 37,168 |

这些数字来自最初研究数据集的实际处理记录。

## 仓库结构

```text
alpaca-translation-pipeline/
├── src/alpaca_translation/
│   ├── __main__.py
│   ├── cli.py
│   ├── clean.py
│   ├── detect.py
│   ├── io.py
│   ├── merge.py
│   ├── translate.py
│   └── validate.py
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
git clone https://github.com/ShunHao0626/alpaca-translation-pipeline.git
cd alpaca-translation-pipeline
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e '.[google]'
```

`google` 可选依赖会安装 `deep-translator`。检测、清洗、合并、校验及测试均无需联网，也不依赖翻译库。

## 命令行接口

安装后提供的 `alpaca-translate` 命令与 `python -m alpaca_translation` 等价。

```bash
# 查找含中文的记录
python -m alpaca_translation detect \
  --input dataset.json \
  --output work/candidates.json

# 去除空字段或不含中文的候选字段；不同记录中的相同文本会被刻意保留，
# 以保证每条记录都能拿到译文
python -m alpaca_translation clean \
  --input work/candidates.json \
  --output work/candidates-cleaned.json

# 翻译候选字段。默认每 25 条记录保存一次检查点（--checkpoint-every）；
# 以相同 --output 重新运行即可续跑，--overwrite 则从头开始。
# 另有 --max-retries 与 --delay 参数
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

# 检查记录结构，并列出仍含中文的字段
python -m alpaca_translation validate \
  --input work/dataset-translated.json \
  --report work/validate-report.json
```

## 安全与校验规则

当前软件包已实现：

- JSON 通过临时文件原子化写入，写入中断不会留下截断的文件。
- 合并在深拷贝上进行，保持记录顺序与总数，并拒绝越界索引及不在所选字段列表中的字段。
- 未选定翻译的字段保持不变。
- 翻译进度定期保存检查点，中断后可续跑。
- 每个取值最多重试 `--max-retries` 次（默认 3 次），指数退避间隔为 1 秒、2 秒……；后端返回空值也视为失败。
- `validate` 报告残留中文字段，若存在不是 JSON 对象的记录则以状态码 1 退出。

输入与输出应使用不同路径。某条译文耗尽重试次数后，任务停止，并可从上一个检查点继续。`validate` 命令单独统计残留中文；当前校验覆盖记录形态与选定字段，不执行完整的 Alpaca 结构校验。

## 翻译质量

机器翻译可能改变专业术语、代码、公式、专有名词、格式以及安全相关内容。接口返回成功并不代表翻译正确。在用于训练或评测前，应抽取具有统计意义的样本进行审阅，并人工检查重要记录。

为便于复现，正式发布应记录翻译后端、源语言与目标语言、执行日期、依赖版本、过滤规则、重试策略，以及输入输出文件的哈希值。

## 数据来源与发布政策

最初研究数据集来自外部数据平台，其确切数据卡和再分发条款仍在核实。本仓库发布处理代码与小规模示例。后续数据发布将注明来源，遵守许可和署名要求，并对生成数据进行版本管理。

## 方法特点

- 检测器匹配 CJK 统一汉字、扩展 A 区与兼容汉字（U+3400–4DBF、U+4E00–9FFF、U+F900–FAFF）。字段中只要出现一个此类字符就会整段翻译，因此以英文为主、仅夹带少量中文术语的字段也会被整体翻译；日文汉字同样会被命中。
- 翻译请求按顺序发送，大型数据集可能较慢。
- 命令行目前只接入了 Google 后端（经由 `deep-translator`）。
- 翻译服务的行为可能随时间变化。

## 参与贡献

欢迎贡献，尤其是语言检测测试、后端适配、失败记录、结构校验、术语保留与合并完整性检查等方面。

请勿提交私有数据、访问凭证，或未明确允许再分发的第三方数据集。

## 引用

引用当前代码时，请注明仓库地址及所用的具体 commit。

## 许可

代码与数据集的再使用条款正在分别确认与整理。
