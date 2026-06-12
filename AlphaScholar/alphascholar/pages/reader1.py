import reflex as rx
import os
from openai import OpenAI
from typing import Literal
import asyncio
import PyPDF2

from ..templates import web_structure


# ------------------- Configs --------------------
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "EMPTY")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://openai.cau.edu.cn/v1")
MODEL_NAME = "qwen3.6"
client = OpenAI(api_key=OPENAI_API_KEY, base_url=OPENAI_BASE_URL)


# ------------------- 辅助函数 --------------------
def extract_pdf_text(file_path: str) -> str:
    text = []
    with open(file_path, "rb") as f:
        reader = PyPDF2.PdfReader(f)
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text.append(page_text)
    return "\n".join(text)


def build_summary_prompt(text: str, mode: str, max_len: int = 10000) -> str:
    base = f"请根据以下文本内容生成{mode}总结。\n\n文本：\n{text[:max_len]}"
    if mode == "Summary":
        return base + "\n\n要求：简洁概括核心内容，200字左右。"
    elif mode == "Extensive":
        return base + "\n\n要求：详细总结，覆盖所有主要观点、方法、结果，500字左右。"
    elif mode == "Intensive":
        return base + "\n\n要求：深入分析，指出关键创新点、局限性和未来方向，400字左右。"
    return base


# ------------------- 状态管理 --------------------
class ReaderState(rx.State):
    uploaded_files: list[str] = []
    pdf_url: str = ""                     # 仅用于 OCR 读取时的文件定位
    control_left_value: str = 'pdf_ocr'
    control_right_value: str = 'Summary'
    ocr_text: str = ""
    deepseek_ocr_text: str = ""
    summary_text: str = ""
    is_processing_run_ocr: bool = False
    is_processing_summarize: bool = False

    # 替代 Toast 的状态提示
    status_message: str = ""
    status_color: str = "green"   # green / red / orange

    def set_control_left(self, value: str | list[str]):
        if isinstance(value, list):
            value = value[0] if value else "pdf_ocr"
        self.control_left_value = value

    def set_control_right(self, value: str | list[str]):
        if isinstance(value, list):
            value = value[0] if value else "Summary"
        self.control_right_value = value

    def set_ocr_text(self, value: str):
        self.ocr_text = value

    def set_deepseek_ocr_text(self, value: str):
        self.deepseek_ocr_text = value

    def set_summary_text(self, value: str):
        self.summary_text = value

    def clear_status(self):
        """手动清除提示条"""
        self.status_message = ""

    async def upload_file(self, files: list[rx.UploadFile]):
        for file in files:
            data = await file.read()
            path = rx.get_upload_dir() / file.name
            with path.open("wb") as f:
                f.write(data)
            self.uploaded_files.append(file.name)
            self.pdf_url = file.name
        self.status_message = "文件上传成功"
        self.status_color = "green"

    @rx.var
    def show_uploaded_files(self) -> str:
        return ", ".join(self.uploaded_files) if self.uploaded_files else "No files uploaded."

    def clear_file(self):
        self.uploaded_files.clear()
        self.pdf_url = ""
        self.ocr_text = ""
        self.deepseek_ocr_text = ""
        self.summary_text = ""
        self.status_message = "已清除所有文件"
        self.status_color = "orange"
        for file in rx.get_upload_dir().iterdir():
            file.unlink(missing_ok=True)

    @rx.event
    async def run_ocr(self):
        if not self.uploaded_files:
            self.status_message = "请先上传 PDF 文件"
            self.status_color = "red"
            return
        self.is_processing_run_ocr = True
        yield
        try:
            file_path = rx.get_upload_dir() / self.uploaded_files[0]
            text = await asyncio.to_thread(extract_pdf_text, str(file_path))
            self.ocr_text = text
            self.status_message = "OCR 提取完成"
            self.status_color = "green"
        except Exception as e:
            self.status_message = f"OCR 失败: {str(e)}"
            self.status_color = "red"
        finally:
            self.is_processing_run_ocr = False
            yield   # 推送状态更新，使提示条显示

    @rx.event
    async def summarize(self):
        # 选择左侧选中的文本来源
        source_text = self.ocr_text if self.control_left_value == "pdf_ocr" else self.deepseek_ocr_text
        if not source_text.strip():
            self.status_message = "请先运行 OCR 提取文本"
            self.status_color = "red"
            return
        self.is_processing_summarize = True
        yield
        try:
            prompt = build_summary_prompt(source_text, self.control_right_value)  # 修正变量引用
            response = await asyncio.to_thread(
                lambda: client.chat.completions.create(
                    model=MODEL_NAME,
                    messages=[
                        {"role": "system", "content": "你是专业的科研助手，请根据提供的文本生成总结。"},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.3,
                    max_tokens=800
                )
            )
            self.summary_text = response.choices[0].message.content
            self.status_message = "总结生成完成"
            self.status_color = "green"
        except Exception as e:
            self.status_message = f"总结失败: {str(e)}"
            self.status_color = "red"
        finally:
            self.is_processing_summarize = False
            yield


# ------------------- 状态提示条组件 --------------------
def status_bar() -> rx.Component:
    return rx.cond(
        ReaderState.status_message != "",
        rx.callout(
            ReaderState.status_message,
            icon="info",
            color_scheme=ReaderState.status_color,
            width="100%",
        ),
    )


# ---------------- Frontend ----------------
def upload_card() -> rx.Component:
    return rx.card(
        rx.vstack(
            rx.heading("Upload", size="5"),
            rx.hstack(
                rx.upload(
                    rx.vstack(
                        rx.text(rx.cond(
                            ReaderState.uploaded_files.length() > 0,
                            ReaderState.show_uploaded_files,
                            "No files uploaded."
                        )),
                        align="center",
                        justify="center",
                    ),
                    id="pdf_upload",
                    width="100%",
                    height="20px",
                    accept={"application/pdf": [".pdf"]},
                    max_files=1,
                ),
                rx.vstack(
                    rx.button("Upload", on_click=ReaderState.upload_file(rx.upload_files("pdf_upload")),
                              color_scheme="blue", size="3", radius="full"),
                    rx.button("Clear", on_click=ReaderState.clear_file,
                              color_scheme="red", size="3", radius="full"),
                    align="center", justify="between", width="100%",
                ),
                spacing="3",   # 修正拼写错误
            ),
            spacing="1",
        ),
        width="100%",
    )


def reader_card() -> rx.Component:
    return rx.card(
        rx.heading("Reader", size="5"),
        rx.hstack(
            # 左侧
            rx.card(
                rx.vstack(
                    rx.hstack(
                        rx.segmented_control.root(
                            rx.segmented_control.item("PDF OCR", value="pdf_ocr"),
                            rx.segmented_control.item("DeepSeek OCR", value="deepseek_ocr"),
                            value=ReaderState.control_left_value,
                            on_change=ReaderState.set_control_left,
                            width="100%",
                        ),
                        rx.button(
                            "Run OCR",
                            on_click=ReaderState.run_ocr,
                            loading=ReaderState.is_processing_run_ocr,
                            color_scheme="green", size="2"
                        ),
                        width="100%", justify="end",
                    ),
                    # 两个 OCR 文本区域（各自绑定 on_change，内容独立保留）
                    rx.cond(
                        ReaderState.control_left_value == "pdf_ocr",
                        rx.text_area(
                            placeholder="OCR text ...",
                            value=ReaderState.ocr_text,
                            on_change=ReaderState.set_ocr_text,
                            size="2",
                            width="100%",
                            height="600px",
                        ),
                        rx.text_area(
                            placeholder="DeepSeek OCR text ...",
                            value=ReaderState.deepseek_ocr_text,
                            on_change=ReaderState.set_deepseek_ocr_text,
                            size="2",
                            width="100%",
                            height="600px",
                        ),
                    ),
                ),
                width="50%",
            ),
            # 右侧
            rx.card(
                rx.vstack(
                    rx.hstack(
                        rx.segmented_control.root(
                            rx.segmented_control.item("Summary", value="Summary"),
                            rx.segmented_control.item("Extensive", value="Extensive"),
                            rx.segmented_control.item("Intensive", value="Intensive"),
                            value=ReaderState.control_right_value,
                            on_change=ReaderState.set_control_right,
                            width="100%",
                        ),
                        rx.button("Generate Summary", on_click=ReaderState.summarize,
                                  loading=ReaderState.is_processing_summarize,
                                  color_scheme="purple", size="2"),
                        width="100%", justify="end",
                    ),
                    rx.text_area(
                        value=ReaderState.summary_text,
                        placeholder="AI Summary ...",
                        on_change=ReaderState.set_summary_text,
                        size="2",
                        variant="classic",
                        width="100%",
                        height="600px",
                    ),
                    spacing="3",
                ),
                width="50%", height="100%",
            ),
            width="100%", height="100%", align_items="stretch", spacing="4",
        ),
        width="100%", height="100%",
    )


@rx.page("/reader")
@web_structure
def reader_page() -> rx.Component:
    return rx.box(
        rx.vstack(
            status_bar(),   # 页面顶部显示操作反馈
            upload_card(),
            reader_card(),
            spacing="4",
            width="100%",
        ),
        width="80%",
    )