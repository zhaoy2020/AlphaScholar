# --- Multi-agent ---
import json
import re 

from llms import Config
from prompts import SYSTEM_PROMPT, RETRIEVER_PROMPT, ANALYST_PROMPT, WRITER_PROMPT, EVALUATION_PROMPT
from tools import TOOLS, TOOL_FUNCTIONS
from memory import Memory 
from utils import show


class Agent:
    '''Agent = Perception + LLM + Tools + Memory.
    Perception: user input text
    LLM: openai.OpenAI
    Tools: openai function calling
    Memory: short-term memory (conversation history) + long-term memory (file storage)
    '''

    def __init__(self, platform: str, system_prompt: str, memory_file: str, memory_dir: str = './memory'):
        self.client, self.model = Config(platform=platform).create_client_and_model()
        self.tools, self.tool_functions = TOOLS, TOOL_FUNCTIONS
        self.memory = Memory(storage_path=f"{memory_dir}/{memory_file}")
        self.memory.add_message(role='system', content=system_prompt)

    
    def run_llm(self, use_tool: bool = False, stream: bool = True, temprature: float = 0.2):
        '''调用 LLM 生成响应，支持工具调用和流式输出'''

        if use_tool:
            while True:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=self.memory.get_messages(),
                    tools=self.tools,
                    tool_choice="auto",
                    stream=False,
                    temperature=temprature
                )
                msg = response.choices[0].message
                if msg.tool_calls:
                    if msg.content:
                        show(f"\n\n💭 模型思考: {msg.content}\n\n")
                    # ★ 先添加 assistant 消息（content 可能为空，但 tool_calls 不空，表示模型在思考工具调用方案）
                    self.memory.add_message(role="assistant", content=msg.content or "", tool_calls=msg.tool_calls)
                    for tool_call in msg.tool_calls:
                        func_name = tool_call.function.name
                        args = json.loads(tool_call.function.arguments)
                        show(f"\n🔍 调用工具: {func_name}({args})\n")
                        result = self.tool_functions[func_name](**args)
                        show(f'\n✅ 调用结果：{result[:100]}\n\n')
                        # 再添加 tool 结果（注意：工具调用结果作为新的消息添加到记忆中，role 是 'tool'，并且关联 tool_call_id 以便追踪）
                        self.memory.add_message(role='tool', content=result, tool_call_id=tool_call.id)
                    continue
                else:
                    # 模型不再调用工具，准备流式生成最终回答
                    show("\n\n💡 模型不再调用工具，准备生成最终回答...\n\n")
                    break   # 跳出循环，使用流式输出

        # 最终回复用流式生成
        response = self.client.chat.completions.create(
            model=self.model,
            messages=self.memory.get_messages(),
            stream=stream,
            temperature=temprature,
        )
        if stream:
            # 流式输出
            full_response = ""
            for chunk in response:
                if chunk.choices and len(chunk.choices) > 0:
                    delta = chunk.choices[0].delta
                    if delta and delta.content:
                        token = delta.content
                        full_response += token
                        show(token)  # 实时输出生成内容
            self.memory.add_message(role='assistant', content=full_response)
            return full_response
        else:
            # 非流式输出
            full_response = response.choices[0].message.content or ''
            self.memory.add_message(role='assistant', content=full_response)
            return full_response
    

class AlphaScholarTwoAgent:
    '''包含一个 Scholar Agent 负责检索和写作，一个 Reviewer Agent 负责评审和反馈。两者循环迭代，直到报告质量达标或达到最大重试次数。'''

    def __init__(self, platform: str = 'cau'):
        self.scholar = Agent(platform=platform, system_prompt=SYSTEM_PROMPT, memory_file='agent_memory.json')
        self.reviewer = Agent(platform=platform, system_prompt=EVALUATION_PROMPT, memory_file='reviewer_memory.json')

    def workflow(self, user_input: str, retries: int = 3, quality_threshold: int = 7):
        '''两个Agent 完成整个调研流程（包含工具调用和自动评审）'''

        self.scholar.memory.add_message(role='user', content=user_input)
        for counter in range(retries):
            show(f'\n\n🔍 第 {counter + 1} 次调研中...\n\n')            
            writer_output = self.scholar.run_llm(use_tool=True, stream=True)

            show('\n\n🔎 评审中...\n\n"')
            self.reviewer.memory.add_message(role='user', content=writer_output)
            evaluation = self.reviewer.run_llm(use_tool=False, stream=False)
            if not evaluation:
                show("❌ 评审未返回有效内容")
                break

            # 解析评审结果，提取 score, issues, suggestion
            json_match = re.search(r'\{[\s\S]*\}', evaluation)
            if json_match:
                result = json.loads(json_match.group())
            else:
                result = json.loads(evaluation)
            result.setdefault("score", 0)
            result.setdefault("issues", [])
            result.setdefault("suggestion", "")
            
            score = result["score"]
            issues = result["issues"]
            suggestion = result["suggestion"]
            show(f"\n\n📊 当前评分: {score}/10\n\n")
            if issues:
                show(f"\n\n⚠️ 发现问题: {'; '.join(issues)}\n\n")
            show(f"\n\n💡 建议: {suggestion}\n\n")

            # --- 判断是否达标 ---
            if score >= quality_threshold:
                show("\n\n✅ 报告质量达标，输出最终结果。\n\n")
                return writer_output  # 结束调研循环，返回最终报告
            else:
                feedback: str = f"报告质量评分只有{score}/10，存在以下问题：{'；'.join(issues)}。\n 建议：{suggestion}。请根据这些意见改进报告，若需补充文献请重新检索。"
                self.scholar.memory.add_message(role='user', content=feedback)
                show(f"\n\n🔄 正在进行第 {counter + 1} 次改进...\n\n")

        show(f"\n\n⚠️ 已达最大重试次数（{retries}），将使用当前版本。\n\n")
        return writer_output
    
    def run(self):
        show("\n\n👋 欢迎使用 AlphaScholar Agent 版本！\n\n")
        final_report: str = ""
        while True:
            try:
                user_input = input("\n请输入研究方向（或 'exit' 结束）: ").strip() or 'vae 在 微生物组学 中的应用进展。'
                if user_input.lower() == 'exit':
                    show("\n\n👋 感谢使用 AlphaScholar，期待下次再见！\n\n")
                    break
                elif user_input.lower() == '':
                    show("\n\n⚠️ 输入不能为空，请重新输入。\n\n")
                else:
                    show(f"\n\n👋 研究主题为：{user_input}\n\n")
                    final_report = self.workflow(user_input=user_input)
            except Exception as e:
                show(f"\n\n❌ 发生错误: {e}\n\n")

        return final_report
    
    def save_report(self, report: str, filename: str = 'final_report.md'):
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(report)
    

class AlphaScholarMultiAgent:
    '''包含多个专职 Agent：检索员、分析师、撰写员、审稿人。每个 Agent 专注一个环节，循环迭代改进。'''

    def __init__(self, platform: str = 'cau'):
        self.retriever = Agent(platform=platform, system_prompt=RETRIEVER_PROMPT, memory_file='retriever.json')
        self.analyst = Agent(platform=platform, system_prompt=ANALYST_PROMPT, memory_file='analyst.json')
        self.writer = Agent(platform=platform, system_prompt=WRITER_PROMPT, memory_file='writer.json')
        self.reviewer = Agent(platform=platform, system_prompt=EVALUATION_PROMPT, memory_file='reviewer.json')

    def workflow(self, user_input: str, retries: int = 3, quality_threshold: int = 7):
        '''Planing -> Retrieval -> Analysis -> Writing -> Evaluation -> (可能的) 迭代改进'''

        self.retriever.memory.add_message(role='user', content=user_input)
        for counter in range(retries):
            show('\n\n🔍 检索员工作中...')
            retrieval_result = self.retriever.run_llm(use_tool=True)

            show('\n\n📊 分析师工作中...')
            self.analyst.memory.add_message(role='user', content=retrieval_result)
            analyst_output = self.analyst.run_llm(use_tool=False)

            show(f'\n\n✍️ 第 {counter + 1} 次撰写报告..."')
            self.writer.memory.add_message(role='user', content=analyst_output)
            writer_output = self.writer.run_llm(use_tool=False)

            show('\n\n🔎 审稿人评审中..."')
            self.reviewer.memory.add_message(role='user', content=writer_output)
            evaluation = self.reviewer.run_llm(use_tool=False)
            if not evaluation:
                show("❌ 评审未返回有效内容")
                break

            # 解析评审结果，提取 score, issues, suggestion
            json_match = re.search(r'\{[\s\S]*\}', evaluation)
            if json_match:
                result = json.loads(json_match.group())
            else:
                result = json.loads(evaluation)
            result.setdefault("score", 0)
            result.setdefault("issues", [])
            result.setdefault("suggestion", "")            
            score = result["score"]
            issues = result["issues"]
            suggestion = result["suggestion"]
            show(f"\n\n📊 当前评分: {score}/10\n\n")
            if issues:
                show(f"\n\n⚠️ 发现问题: {'; '.join(issues)}\n\n")
            show(f"\n\n💡 建议: {suggestion}\n\n")

            # --- 判断是否达标 ---
            if score >= quality_threshold:
                show("\n\n✅ 报告质量达标，输出最终结果。\n\n")
                return writer_output  # 结束调研循环，返回最终报告
            else:
                feedback: str = f"报告质量评分只有{score}/10，存在以下问题：{'；'.join(issues)}。\n 建议：{suggestion}。请根据这些意见改进报告，若需补充文献请重新检索。"
                # 只告诉检索员
                self.retriever.memory.add_message(role='user', content=feedback)
                # 分析师和作家重置记忆，避免信息污染
                self.analyst.memory.clear_short_term()  # 需在 Memory 中实现
                self.analyst.memory.add_message(role='system', content=ANALYST_PROMPT)
                self.writer.memory.clear_short_term()
                self.writer.memory.add_message(role='system', content=WRITER_PROMPT)
                # 下一轮循环时，retriever 会基于 feedback 重新检索，然后传给全新的 analyst 和 writer
                show(f"\n🔄 正在进行第 {counter + 1} 次改进...\n")

        show(f"\n\n⚠️ 已达最大重试次数（{retries}），将使用当前版本。\n\n")
        return writer_output
    
    def run(self):
        show("\n\n👋 欢迎使用 AlphaScholar 多Agent 版本！\n\n")
        final_report: str = ""
        while True:
            try:
                user_input = input("\n请输入研究方向（或 'exit' 结束）: ").strip() or 'vae 在 微生物组学 中的应用进展。'
                if user_input.lower() == 'exit':
                    show("\n\n👋 感谢使用 AlphaScholar，期待下次再见！\n\n")
                    break
                elif user_input.lower() == '':
                    show("\n\n⚠️ 输入不能为空，请重新输入。\n\n")
                else:
                    show(f"\n\n👋 研究主题为：{user_input}\n\n")
                    final_report = self.workflow(user_input=user_input)
            except Exception as e:
                show(f"\n\n❌ 发生错误: {e}\n\n")

        return final_report
    
    def save_report(self, report: str, filename: str = 'final_report.md'):
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(report)
    

if __name__ == "__main__":
    platform = 'deepseek'  # 可选 'cau', 'deepseek', 'openai', 'local
    # agent = AlphaScholarTwoAgent(platform=platform)
    agent = AlphaScholarMultiAgent(platform=platform)
    report = agent.run()
    agent.save_report(report, filename='./reports/vae_on_microbiome_final_report.md')
