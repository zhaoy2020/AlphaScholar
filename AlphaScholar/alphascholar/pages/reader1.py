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


# ------------------- States --------------------
class ReaderState(rx.State):
    uploaded_files: list[str] = []
    pdf_url: str = ""
    text_area_value_left: str = "PDF"
    text_area_value_right: str = "Summary"
    ocr_text: str = ""
    summary_text: str = ""
    is_processing: bool = False

    def set_control_left(self, value: str | list[str]):
        # if isinstance(value, list):
        #     value = value[0] if value else "PDF"
        self.text_area_value_left = value

    def set_control_right(self, value: str | list[str]):
        # if isinstance(value, list):
        #     value = value[0] if value else "Summary"
        self.text_area_value_right = value

    async def upload_file(self, files: list[rx.UploadFile]):
        for file in files:
            data = await file.read()
            path = rx.get_upload_dir() / file.name
            with path.open("wb") as f:
                f.write(data)
            self.uploaded_files.append(file.name)
            self.pdf_url = file.name
            print(self.pdf_url)

    @rx.var
    def show_uploaded_files(self) -> str:
        if self.uploaded_files:
            return ", ".join(self.uploaded_files)
        return "No files uploaded."

    def clear_file(self):
        self.uploaded_files.clear()
        self.pdf_url = ""
        self.ocr_text = ""
        self.summary_text = ""
        uploaded_dir = rx.get_upload_dir()
        for file in uploaded_dir.iterdir():
            file.unlink(missing_ok=True)

    @rx.event
    async def run_ocr(self):
        if not self.uploaded_files:
            rx.toast.error("请先上传 PDF 文件")
            return
        self.is_processing = True
        yield
        try:
            file_path = rx.get_upload_dir() / self.uploaded_files[0]
            text = await asyncio.to_thread(extract_pdf_text, file_path)
            self.ocr_text = text
            rx.toast.success("OCR 提取完成")
        except Exception as e:
            rx.toast.error(f"OCR 失败: {str(e)}")
        finally:
            self.is_processing = False

    @rx.event
    async def summarize(self):
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
    text = []
    with open(file_path, "rb") as f:
        reader = PyPDF2.PdfReader(f)
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                text.append(page_text)
    return "\n".join(text)


def build_summary_prompt(text: str, mode: str) -> str:
    base = f"请根据以下文本内容生成{mode}总结。\n\n文本：\n{text[:4000]}"
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
            # 左侧：PDF/OCR
            rx.card(
                rx.vstack(
                    rx.segmented_control.root(
                        rx.segmented_control.item("PDF", value="PDF"),
                        rx.segmented_control.item("OCR", value="OCR"),
                        value=ReaderState.text_area_value_left,
                        on_change=ReaderState.set_control_left,
                        width="100%",
                    ),
                    rx.cond(
                        ReaderState.text_area_value_left == "PDF",
                        rx.cond(
                            ReaderState.pdf_url != "",
                            # 修正 embed 参数顺序：子元素在前，关键字参数在后
                            rx.el.embed(
                                src=rx.get_upload_url(ReaderState.pdf_url),
                                width="100%",
                                height="600px",
                            ),
                            rx.center(
                                rx.text("No PDF uploaded.", color="gray"),
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
            # 右侧：总结
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
                        height="600px",
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