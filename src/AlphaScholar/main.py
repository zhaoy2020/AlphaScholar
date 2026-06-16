
from utils import show
from agent import run_agent_stream
from config import Config


def main(config: Config):
    '''主程序入口'''

    # ---------- 配置 ----------
    show("文献调研 Agent (流式输出)") 
    client, MODEL = config.create_client_and_model()
    while True:
        try:
            user_input = input("\n请输入研究方向（或 'exit' 结束）: ").strip() or 'vae在为生物组学中的应用进展。'
            show(f"🔍 检索关键词: {user_input}")

            if user_input.lower() == 'exit':
                show("\n\n✅ 再见！")
                break
            elif not user_input:
                continue
            else:
                show("\n\n✅ 开始调研...")
                run_agent_stream(user_input, client, MODEL)
                show("\n\n✅ 调研完成。")

        except KeyboardInterrupt:
            show("\n\n⚠️ 用户中断。")
            break

        except Exception as e:
            show(f"\n\n❌ 发生错误: {e}")


if __name__ == "__main__":
    '''运行主程序'''

    main(config=Config(platform="local"))