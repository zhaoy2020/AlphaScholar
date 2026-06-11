import reflex as rx
import os
from openai import OpenAI
from typing import Literal
import asyncio
import PyPDF2  # 用于提取 PDF 文本

from ..templates import web_structure


# ------------------- Configs --------------------
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "EMPTY")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://openai.cau.edu.cn/v1")
MODEL_NAME = "qwen3.6"
client = OpenAI(api_key=OPENAI_API_KEY, base_url=OPENAI_BASE_URL)


# ------------------- States --------------------
class ReaderState(rx.State):
    uploaded_files: list[str] = []          # 文件名列表（用于展示）
    pdf_url: str = ""                       # 上传后 PDF 的可访问 URL
    text_area_value_left: str = "PDF"       # 左侧分段控件值："PDF" 或 "OCR"
    text_area_value_right: str = "Summary"  # 右侧分段控件值
    ocr_text: str = ""                      # OCR 提取的原始文本
    summary_text: str = ""                  # 生成的总结文本
    is_processing: bool = False             # 处理中状态（OCR/总结）

    def set_control_left(self, value: str | list[str]):
        if isinstance(value, list):
            value = value[0] if value else "PDF"
        self.text_area_value_left = value

    def set_control_right(self, value: str | list[str]):
        if isinstance(value, list):
            value = value[0] if value else "Summary"
        self.text_area_value_right = value

    async def upload_file(self, files: list[rx.UploadFile]):
        """处理文件上传，保存文件并记录 URL"""
        for file in files:
            data = await file.read()
            path = rx.get_upload_dir() / file.name
            with path.open("wb") as f:
                f.write(data)
            # 存储文件名和可访问的 URL
            self.uploaded_files.append(file.name)
            # self.pdf_url = rx.get_upload_url(file.name)  # 获取相对 URL（如 /uploaded_files/xxx.pdf）
            self.pdf_url = f"/{rx.get_upload_url(file.name)}"  # 确保以斜杠开头

    @rx.var
    def show_uploaded_files(self) -> str:
        """返回已上传文件的文件名字符串"""
        if self.uploaded_files:
            return ", ".join(self.uploaded_files)
        return "No files uploaded."

    def clear_file(self):
        """清空所有上传文件并重置相关状态"""
        self.uploaded_files.clear()
        self.pdf_url = ""
        self.ocr_text = ""
        self.summary_text = ""
        uploaded_dir = rx.get_upload_dir()
        for file in uploaded_dir.iterdir():
            file.unlink(missing_ok=True)

    @rx.event
    async def run_ocr(self):
        """提取 PDF 文本（异步调用同步阻塞操作）"""
        if not self.uploaded_files:
            rx.toast.error("请先上传 PDF 文件")
            return
        self.is_processing = True
        yield
        try:
            # 获取第一个上传文件的本地路径
            file_path = rx.get_upload_dir() / self.uploaded_files[0]
            # 将同步 OCR 操作放到线程中执行，避免阻塞
            text = await asyncio.to_thread(extract_pdf_text, file_path)
            self.ocr_text = text
            rx.toast.success("OCR 提取完成")
        except Exception as e:
            rx.toast.error(f"OCR 失败: {str(e)}")
        finally:
            self.is_processing = False

    @rx.event
    async def summarize(self):
        """根据右侧选择的方式（Summary/Extensive/Intensive）生成总结"""
        # 优先使用 OCR 文本，若为空则提示错误
        source_text = self.ocr_text
        if not source_text.strip():
            rx.toast.error("请先运行 OCR 提取文本")
            return
        self.is_processing = True
        yield
        try:
            prompt = build_summary_prompt(source_text, self.text_area_value_right)
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
            rx.toast.success("总结生成完成")
        except Exception as e:
            rx.toast.error(f"总结失败: {str(e)}")
        finally:
            self.is_processing = False


# ------------------- 辅助函数 --------------------
def extract_pdf_text(file_path: str) -> str:
    """使用 PyPDF2 提取 PDF 文本"""
    text = []
    with open(file_path, "rb") as f:
        reader = PyPDF2.PdfReader(f)
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text.append(page_text)
    return "\n".join(text)


def build_summary_prompt(text: str, mode: str) -> str:
    """根据总结模式构建不同的提示词"""
    base = f"请根据以下文本内容生成{mode}总结。\n\n文本：\n{text[:4000]}"  # 截断避免超出 token 限制
    if mode == "Summary":
        return base + "\n\n要求：简洁概括核心内容，200字左右。"
    elif mode == "Extensive":
        return base + "\n\n要求：详细总结，覆盖所有主要观点、方法、结果，500字左右。"
    elif mode == "Intensive":
        return base + "\n\n要求：深入分析，指出关键创新点、局限性和未来方向，400字左右。"
    return base


# ------------------- Frontend --------------------
def upload_card() -> rx.Component:
    return rx.card(
        rx.vstack(
            rx.heading("Upload", size="5"),
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
                accept={"application/pdf": [".pdf"]},
                max_files=1,
            ),
            rx.hstack(
                rx.button(
                    "Upload",
                    color_scheme="blue",
                    size="3",
                    radius="full",
                    on_click=ReaderState.upload_file(rx.upload_files("pdf_upload"))
                ),
                rx.button(
                    "Clear",
                    color_scheme="red",
                    size="3",
                    radius="full",
                    on_click=ReaderState.clear_file
                ),
                rx.spacer(),
                rx.button(
                    "Run OCR",
                    color_scheme="green",
                    size="3",
                    radius="full",
                    on_click=ReaderState.run_ocr,
                    loading=ReaderState.is_processing
                ),
                align="center",
                justify="between",
                width="100%",
            ),
            width="100%",
            spacing="1",
        ),
        width="100%",
    )


def reader_card() -> rx.Component:
    return rx.card(
        rx.heading("Reader", size="5"),
        rx.hstack(
            # 左侧区域：PDF 查看 / OCR 文本
            rx.card(
                rx.vstack(
                    rx.segmented_control.root(
                        rx.segmented_control.item("PDF", value="PDF"),
                        rx.segmented_control.item("OCR", value="OCR"),
                        value=ReaderState.text_area_value_left,
                        on_change=ReaderState.set_control_left,
                        width="100%",
                    ),
                    # 根据选择显示 iframe 或文本区域
                    rx.cond(
                        ReaderState.text_area_value_left == "PDF",
                        rx.cond(
                            ReaderState.pdf_url != "",
                            rx.el.iframe(
                                src=ReaderState.pdf_url,
                                width="100%",
                                height="600px",
                            ),
                            rx.center(
                                rx.text("No PDF uploaded. Please upload a PDF first.", color="gray"),
                                width="100%",
                                height="600px",
                            ),
                        ),
                        rx.text_area(
                            value=ReaderState.ocr_text,
                            placeholder="OCR 文本将显示在这里...",
                            disabled=False,
                            size="2",
                            variant="classic",
                            width="100%",
                            height="600px",
                        ),
                    ),
                ),
                width="50%",
            ),
            # 右侧区域：总结类型选择 + 总结结果
            rx.card(
                rx.vstack(
                    rx.hstack(
                        rx.segmented_control.root(
                            rx.segmented_control.item("Summary", value="Summary"),
                            rx.segmented_control.item("Extensive", value="Extensive"),
                            rx.segmented_control.item("Intensive", value="Intensive"),
                            value=ReaderState.text_area_value_right,
                            on_change=ReaderState.set_control_right,
                            width="100%",
                        ),
                        rx.button(
                            "Generate Summary",
                            on_click=ReaderState.summarize,
                            loading=ReaderState.is_processing,
                            color_scheme="purple",
                            size="2",
                        ),
                        width="100%",
                        justify="end",
                    ),
                    rx.text_area(
                        value=ReaderState.summary_text,
                        placeholder="生成的总结将显示在这里...",
                        disabled=False,
                        size="2",
                        variant="classic",
                        width="100%",
                        height='600px',
                    ),
                    spacing="3",
                ),
                width="50%",
                height="100%",
            ),
            width="100%",
            height="100%",
            align_items="stretch",
            spacing="4",
        ),
        width="100%",
        height="100%",
    )


@rx.page("/reader")
@web_structure
def reader() -> rx.Component:
    return rx.box(
        rx.vstack(
            upload_card(),
            reader_card(),
            spacing="4",
            width="100%",
        ),
        width="80%",
    )