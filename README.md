# AlphaScholar — 多智能体文献调研系统

<p align="center">
  <img src="https://img.shields.io/badge/license-Apache%202.0-blue.svg" alt="License">
  <img src="https://img.shields.io/badge/python-3.10+-green.svg" alt="Python">
  <img src="https://img.shields.io/badge/LLM-OpenAI%20%7C%20DeepSeek-orange.svg" alt="LLM">
</p>

**AlphaScholar** 是一个基于大语言模型（LLM）的多智能体文献调研助手。它能够自动分析你的研究方向，在多个学术数据库（PubMed、arXiv、Semantic Scholar）中执行高级检索，随后通过“分析师-作家-审稿人”的协作流水线生成并反复打磨高质量的文献综述报告。

---

## 核心特性

- 🔍 **多源智能检索**自动为 PubMed、arXiv、Semantic Scholar 生成最合适的检索式（如 PubMed 高级语法 `[tiab]`），克服不同数据库的检索差异。
- 🧠 **多智能体协作**内置检索员、分析师、作家、审稿人四个专职 Agent，各司其职，通过反馈循环不断优化报告质量。
- 🛠️ **可扩展工具系统**使用 Python 装饰器 `@tool` 即可将任意函数转换为 OpenAI Function Calling 工具，自动生成 Schema，零样板代码。
- 📝 **自动评审与迭代**审稿人 Agent 依据文献数量、结构完整性、语言质量等标准进行评分，不达标时自动将修改意见反馈给作家重写，直到质量达标。
- 💾 **长期记忆**检索到的文献和生成的报告会自动存入 JSON 文件，下次调研时可注入历史记忆，避免重复劳动。
- 🌊 **流式输出**报告撰写过程支持流式输出，像 ChatGPT 一样逐字显示，交互体验流畅。
- 🔌 **兼容多种 LLM**
  默认支持 OpenAI、DeepSeek 等兼容接口，只需配置 `base_url` 和 API Key 即可切换模型。

---

## 整体架构

```
┌──────────┐     ┌──────────┐     ┌──────────┐     ┌──────────┐
│ Retriever │────▶│  Analyst │────▶│  Writer  │────▶│ Reviewer │
│  (检索员) │     │  (分析师) │     │  (作家)  │     │  (审稿人) │
└──────────┘     └──────────┘     └──────────┘     └──────────┘
      │                                                  │
      │              ┌──────────────────┐                │
      └─────────────▶│   Tools (工具层)  │◀───────────────┘
                     │  PubMed, arXiv,   │
                     │  Semantic Scholar │
                     └──────────────────┘
```

1. **Retriever** – 解析用户问题，构建检索式，调用学术数据库 API，返回原始文献列表。
2. **Analyst** – 去重、筛选、分类文献，输出结构化的文献数据集。
3. **Writer** – 根据分类数据撰写 Markdown 格式的综述报告。
4. **Reviewer** – 评估报告质量（评分 + 问题 + 建议），若不达标则驱动下一轮“检索 → 分析 → 写作”循环。

---

## 快速开始

### 1. 克隆仓库

```bash
git clone https://github.com/yourname/AlphaScholar.git
cd AlphaScholar
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

主要依赖：`openai`, `pymed`, `arxiv`, `requests`。

### 3. 配置环境变量

复制环境变量模板并填写你的 API Key 和邮箱（用于 PubMed）：

```bash
cp .env.example .env
```

`.env.example` 示例：

```dotenv
OPENAI_API_KEY=your_openai_key
DEEPSEEK_API_KEY=your_deepseek_key
EMAIL=your_email@example.com
OPENAI_BASE_URL=https://api.openai.com/v1    # 或你的代理地址
```

### 4. 运行

```bash
python alpha_scholar.py --help
python .\src\AlphaScholar\alpha_scholar.py --agent two --platform cau --report_path ./reports/vae_with_microbiome_twoagent_cau_log.md --log_path ./logs/training_data.json
```

或者：
```bash
alphascholar --help
alphascholar --agent two --platform cau --report_path ./reports/vae_with_microbiome_twoagent_cau_log.md --log_path ./logs/training_data.json
```

按提示输入研究方向（例如 `vae 在微生物组学中的应用`），AlphaScholar 将自动完成检索、分析、写作、评审，并流式输出最终报告。

---

## 使用示例

```
👋 欢迎使用 AlphaScholar 多Agent 版本！

请输入研究方向（或 'exit' 结束）: Transformer在时间序列预测中的应用
👋 研究主题为：Transformer在时间序列预测中的应用

🔍 检索员工作中...
📊 分析师工作中...
✍️ 第 1 次撰写报告...
🔎 审稿人评审中...
📊 当前评分: 8/10
✅ 报告质量达标，输出最终结果。

## Transformer在时间序列预测中的应用：文献综述
...
```

---

## 自定义工具

你可以轻松扩展自己的工具，只需使用 `@tool` 装饰器并遵循规范的 docstring 格式：

```python
@tool
def my_new_tool(param1: str, param2: int = 10) -> str:
    """
    工具的简要描述。
    Args:
        param1: str; 参数1的描述
        param2: int = 10; 参数2的描述
    Returns:
        str; 返回值的描述
    Example:
        my_new_tool("hello", 5)
    """
    # 实现逻辑
    return "done"
```

工具会自动注册到全局工具集，并被 Agent 调用。

---

## 项目结构

```
AlphaScholar/
├── agent.py             # 单 Agent 和多 Agent 流程（TwoAgent, MultiAgent）
├── llms.py              # LLM 配置与客户端工厂
├── tools.py             # 工具定义与装饰器（PubMed, arXiv, Semantic Scholar 等）
├── prompts.py           # 系统提示词（Retriever, Analyst, Writer, Reviewer）
├── memory.py            # 短期/长期记忆管理
├── utils.py             # 辅助函数（流式输出、日志等）
├── alpha_scholar.py              # 主入口
├── requirements.txt     # 依赖列表
└── .env.example         # 环境变量模板
```

---

## 路线图

- [X] 多源文献检索（PubMed, arXiv, Semantic Scholar）
- [X] 多智能体协作流水线
- [X] 自动评审与迭代优化
- [X] 长期记忆（JSON 存储）
- [X] 流式输出
- [ ] 全文下载与解析（PDF, DOCX）
- [ ] 参考文献格式化（BibTeX, APA）
- [ ] Web 界面（基于 Flet）
- [ ] MCP 工具服务器支持
- [ ] 更多学术数据库（Google Scholar, Web of Science）

---

## 贡献

欢迎提交 Issue 和 Pull Request！在贡献之前请阅读我们的 [贡献指南](CONTRIBUTING.md)（如有）。

---

## 许可证

本项目基于 [Apache License 2.0](LICENSE) 开源。

---

**AlphaScholar** — 让你的文献综述，由智能体代劳。
