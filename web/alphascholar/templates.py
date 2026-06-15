import reflex as rx 

from typing import Callable

from .components.navbar import navbar
from .components.footbar import footbar


def web_structure(page: Callable[[], rx.Component]) -> rx.Component:
    '''The web structure of the app.'''

    return rx.box(
        # 固定导航栏
        rx.box(
            navbar(),
            position="fixed",
            top="0",
            width="100%",
            z_index=10,
            align='center',
            justify='center',
        ),
        # 主内容区域（避开顶部/底部固定栏）
        rx.center(
            page(),
            padding_top="80px",      # 根据 navbar 高度调整
            padding_bottom="60px",   # 根据 footbar 高度调整
            min_height="95vh",
            width="100%",
        ),
        # 固定页脚
        rx.box(
            footbar(),
            # position="fixed",
            # position="sticky",
            # bottom="0",
            # width="100%",
            # z_index=10,
            # align='center',
            # justify='center',
        ),

        width="100%",
        align="center",
        justify="center",
    )

