import os
import openai
from agent import run_agent_stream
from config import Config




def main(config: Config):
    '''主程序入口'''

    # ---------- 配置 ----------
    client = openai.OpenAI(
        api_key=config.OPENAI_API_KEY,
        base_url=config.OPENAI_BASE_URL
    )
    MODEL = config.MODEL

    print("=" * 50)
    print("文献调研 Agent (流式输出)")
    print("输入 'exit' 退出程序")
    print("=" * 50)

    history_messages: list = []  # 用于记录对话历史，支持多轮交互

    while True:
        try:
            user_input = input("\n请输入研究方向（或 'exit' 结束）: ").strip()
            if user_input.lower() == 'exit':
                print("再见！")
                break
            if not user_input:
                continue

            print("\n开始调研...")
            messages = run_agent_stream(user_input, client, MODEL)
            history_messages.extend(messages)  # 将本轮对话加入历史记录，支持多轮交互
            print("\n\n✅ 调研完成。")

        except KeyboardInterrupt:
            print("\n\n⚠️ 用户中断。")
            break

        except Exception as e:
            print(f"\n❌ 发生错误: {e}")


if __name__ == "__main__":
    main(config=Config())