import reflex as rx
import os
import json
from typing import List, Dict
from openai import OpenAI

# SQLModel（未来可扩展数据库）
from sqlmodel import SQLModel

from ..templates import web_structure


# =====================================================
# OpenAI配置
# =====================================================

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://openai.cau.edu.cn/v1")

MODEL_NAME = "qwen3.6"

client = OpenAI(
    api_key=OPENAI_API_KEY,
    base_url=OPENAI_BASE_URL,
)


# =====================================================
# State（核心）
# =====================================================

class AssistantState(rx.State):

    # 用户输入
    question: str = ""

    # 文档上下文（PDF / txt / 粘贴内容）
    context_text: str = ""

    # Canvas内容（右侧）
    canvas_content: str = ""

    # UI状态
    is_processing: bool = False
    status_message: str = ""

    # 聊天历史（不用Base，直接dict）
    chat_history: List[Dict[str, str]] = []

    # =========================
    # setter
    # =========================
    def set_question(self, value: str):
        self.question = value

    def set_context(self, value: str):
        self.context_text = value

    # =========================
    # 提问主逻辑（流式）
    # =========================
    @rx.event
    async def ask_question(self):

        if not self.question.strip():
            self.status_message = "请输入问题"
            return

        self.is_processing = True

        question = self.question

        # 记录用户消息
        self.chat_history.append({
            "role": "user",
            "content": question
        })

        yield

        try:

            # 最近10轮对话
            history_text = "\n".join(
                f"{m['role']}: {m['content']}"
                for m in self.chat_history[-10:]
            )

            current_canvas = self.canvas_content

            prompt = f"""
你是一个智能Canvas助手（类似ChatGPT Canvas）。

=====================
文档上下文
=====================
{self.context_text}

=====================
历史对话
=====================
{history_text}

=====================
当前Canvas内容
=====================
{current_canvas}

=====================
用户问题
=====================
{question}

=====================
任务
=====================

请完成：

1. chat_answer：给出简洁回答（用于左侧聊天）
2. canvas_content：更新右侧Canvas（Markdown格式）

要求：
- canvas_content必须是结构化Markdown
- 如果已有Canvas内容，请在其基础上优化或扩展
- 不要删除已有重要信息
- 适合知识整理/笔记/代码/表格

返回JSON：

{{
  "chat_answer": "",
  "canvas_content": ""
}}
"""

            stream = client.chat.completions.create(
                model=MODEL_NAME,
                messages=[
                    {
                        "role": "system",
                        "content": "你是一个专业知识整理助手，擅长总结、结构化输出、Markdown编写。"
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                temperature=0.3,
                stream=True,
            )

            full_text = ""

            for chunk in stream:
                delta = chunk.choices[0].delta.content or ""
                full_text += delta
                yield  # 流式刷新UI

            # 解析JSON
            try:
                result = json.loads(full_text)

                chat_answer = result.get("chat_answer", "已生成")
                canvas_content = result.get("canvas_content", "")

            except Exception:
                chat_answer = "内容已生成"
                canvas_content = full_text

            # AI回复
            self.chat_history.append({
                "role": "assistant",
                "content": chat_answer
            })

            # 更新Canvas
            if canvas_content.strip():
                self.canvas_content = canvas_content

            self.question = ""
            self.status_message = "完成"

        except Exception as e:
            self.status_message = f"错误：{str(e)}"

        finally:
            self.is_processing = False

            yield rx.call_script(
                """
                const el = document.getElementById('chat-scroll');
                if (el) el.scrollTop = el.scrollHeight;
                """
            )


# =====================================================
# UI组件
# =====================================================

def status_bar():
    return rx.cond(
        AssistantState.status_message != "",
        rx.callout(
            AssistantState.status_message,
            icon="info",
            width="100%",
        ),
        rx.fragment()
    )


# ---------------------------
# 文档上下文
# ---------------------------
def context_panel():
    return rx.card(
        rx.vstack(
            rx.heading("📄 文档上下文", size="4"),
            rx.text_area(
                value=AssistantState.context_text,
                on_change=AssistantState.set_context,
                placeholder="粘贴PDF文本 / 知识库内容",
                min_height="160px",
                width="100%",
            ),
        ),
        width="100%",
    )


# ---------------------------
# Chat面板
# ---------------------------
def chat_panel():
    return rx.card(
        rx.vstack(
            rx.heading("💬 对话", size="4"),

            rx.scroll_area(
                rx.vstack(
                    rx.foreach(
                        AssistantState.chat_history,
                        lambda m: rx.box(
                            rx.cond(
                                m["role"] == "user",
                                rx.vstack(
                                    rx.badge("你"),
                                    rx.text(m["content"]),
                                    align_items="start",
                                ),
                                rx.vstack(
                                    rx.badge("AI", color_scheme="blue"),
                                    rx.text(m["content"]),
                                    align_items="start",
                                ),
                            ),
                            width="100%",
                            padding="10px",
                            border_bottom="1px solid #eee",
                        ),
                    ),
                    width="100%",
                ),
                id="chat-scroll",
                type="always",
                scrollbars="vertical",
                style={"height": "100%"},
            ),

            width="100%",
            height="100%",
        ),
        width="35%",
        height="100%",
    )


# ---------------------------
# Canvas面板
# ---------------------------
def canvas_panel():
    return rx.card(
        rx.vstack(
            rx.hstack(
                rx.heading("✨ Canvas", size="4"),
                rx.spacer(),
                rx.badge("Markdown"),
                width="100%",
            ),

            rx.scroll_area(
                rx.markdown(AssistantState.canvas_content),
                type="always",
                style={
                    "height": "100%",
                    "padding": "12px"
                },
            ),

            width="100%",
            height="100%",
        ),
        width="65%",
        height="100%",
    )


# ---------------------------
# 输入栏
# ---------------------------
def input_bar():
    return rx.card(
        rx.hstack(
            rx.input(
                placeholder="请输入问题...",
                value=AssistantState.question,
                on_change=AssistantState.set_question,
                flex="1",
            ),
            rx.button(
                "发送",
                on_click=AssistantState.ask_question,
                loading=AssistantState.is_processing,
                color_scheme="blue",
            ),
            width="100%",
        ),
        width="100%",
    )


# =====================================================
# 页面
# =====================================================

@rx.page("/assistant")
@web_structure
def assistant_page():
    return rx.container(
        rx.vstack(
            rx.heading("📚 Smart Canvas Assistant", size="7"),

            context_panel(),

            status_bar(),

            rx.hstack(
                chat_panel(),
                canvas_panel(),
                width="100%",
                height="75vh",
                spacing="4",
            ),

            input_bar(),

            width="100%",
            spacing="4",
        ),
        max_width="95%",
    )