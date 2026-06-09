import reflex as rx

config = rx.Config(
    app_name="alphascholar",
    plugins=[
        rx.plugins.SitemapPlugin(),
        rx.plugins.TailwindV4Plugin(),
    ]
)