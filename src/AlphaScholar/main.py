from loguru import logger

from agent import run_agent_stream
from config import Config


def main(config: Config):
    '''主程序入口'''

    # ---------- 配置 ----------
    logger.info("文献调研 Agent (流式输出)")

    client = config.create_client()
    MODEL = config.model

    while True:
        try:
            user_input = input("\n请输入研究方向（或 'exit' 结束）: ").strip() or 'vae在为生物组学中的应用进展。'
            print(f"🔍 检索关键词: {user_input}")

            if user_input.lower() == 'exit':
                logger.info("再见！")
                break

            if not user_input:
                continue

            print("\n✅ 开始调研...")
            gen = run_agent_stream(user_input, client, MODEL)
            for chunk in gen:
                print(chunk, end="", flush=True)
            print("\n\n✅ 调研完成。")

        except KeyboardInterrupt:
            logger.warning("\n\n⚠️ 用户中断。")
            break

        except Exception as e:
            logger.error(f"\n❌ 发生错误: {e}")


if __name__ == "__main__":
    '''运行主程序'''

    main(config=Config(platform="cau", model="qwen3.6"))