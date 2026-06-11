from openai import OpenAI
import reflex as rx 
import os 
from openai import OpenAI

from ..templates import web_structure

from typing import Literal 



# ------------------- Configs --------------------
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "EMPTY")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://openai.cau.edu.cn/v1")
MODEL_NAME = "qwen3.6"
client = OpenAI(api_key=OPENAI_API_KEY, base_url=OPENAI_BASE_URL)



# ------------------- States --------------------
class ReaderState(rx.State):
    '''The state for the reader page.'''

    def upload_file(self, file: rx.UploadFile):
        '''Handle file upload.'''
        pass

    def clear_file(self):
        '''Clear the uploaded file.'''
        pass
    
    def run_ocr(self): 
        '''Run OCR on the uploaded PDF.'''
        pass

    def summarize(self, method: Literal["Summary", "Extensive", "Intensive"] = "Summary"):
        '''Summarize the uploaded PDF.'''
        pass


# ------------------- Frontend --------------------
def upload_card() -> rx.Component:
    '''The upload card.'''
    
    return rx.card(
        rx.vstack(
            rx.heading("Upload", size="5"),
            rx.upload(
                rx.vstack(
                    # rx.button("Choose PDF", color='black', bg="white", size="3", radius='full', width="100%"),
                    rx.text('Drag and drop files here or click to select files'),
                    align='center',
                    justify='center',
                ),
                id='pdf upload',
                width='100%',
            ),
            rx.hstack(
                rx.button("Upload", color_scheme="blue", size="3", radius='full'),
                rx.button("Clear", color_scheme="red", size="3", radius='full'),
                rx.spacer(),
                rx.button("Run OCR", color_scheme="green", size="3", radius='full'),
                align='center',
                justify='between',
                width='100%',

            ),
            width='100%',
            spacing='1',
        ),
        
        width='100%',
    )


def reader_card() -> rx.Component:
    '''The reader card.'''

    return rx.card(
        rx.heading("Reader", size="5"),
        rx.hstack(
            rx.card(
                rx.vstack(
                    rx.segmented_control.root(
                        rx.segmented_control.item("PDF", value="PDF"),
                        rx.segmented_control.item("OCR", value="OCR"),
                        width="100%",
                    ),
                    rx.text_area(
                        disabled=False,
                        size="3",
                        variant="classic",
                        color_scheme="tomato",
                        radius="full",
                        width="100%",
                        height="100%",
                        min_height="600px",
                    ),
                ),
                width="50%",
                # height="100%",
            ),
            rx.card(
                rx.vstack(
                    rx.segmented_control.root(
                        rx.segmented_control.item("Summary", value="Summary"),
                        rx.segmented_control.item("Extensive", value="Extensive"),
                        rx.segmented_control.item("Intensive", value="Intensive"),
                        width="100%",
                    ),
                    rx.text_area(
                        disabled=False,
                        size="3",
                        variant="classic",
                        color_scheme="tomato",
                        radius="full",
                        width="100%",
                        height="100%",
                        min_height="600px",
                    ),
                ),
                width="50%",
                height="100%",
            )
        ),
        width='100%',
        height="100%",
    )


@rx.page("/reader")
@web_structure
def reader() -> rx.Component:
    '''The reader page.'''
    
    return rx.box(
            rx.vstack(
                upload_card(),
                reader_card(),
            ),
            width="80%",
        )