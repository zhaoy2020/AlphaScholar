import json
import re
import openai
from tools import TOOLS, TOOL_FUNCTIONS
from prompts import SYSTEM_PROMPT, EVALUATION_PROMPT


def evaluate_report(client: openai.OpenAI, model: str, report: str) -> dict:
    """调用模型评审报告，返回包含 score, issues, suggestion 的字典"""
    try:
        resp = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": EVALUATION_PROMPT},
                {"role": "user", "content": report}
            ],
            temperature=0.1,    # 评审需要稳定
        )
        content = resp.choices[0].message.content
        # 尝试提取 JSON（可能包裹在 ```json 中）
        json_match = re.search(r'\{[\s\S]*\}', content)
        if json_match:
            result = json.loads(json_match.group())
        else:
            result = json.loads(content)
        result.setdefault("score", 0)
        result.setdefault("issues", [])
        result.setdefault("suggestion", "")
        return result
    
    except Exception as e:
        # 评审失败时默认低分，触发重试
        return {"score": 0, "issues": [f"评审异常: {str(e)}"], "suggestion": "请重新生成更规范的报告"}


def run_agent_stream(user_input: str, client: openai.OpenAI, model: str,
                     max_retries: int = 3, quality_threshold: int = 7):
    """
    生成器函数，自动进行多轮改进直至报告质量达标。
    用法: for chunk in run_agent_stream(...): print(chunk, end="", flush=True)
    """
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_input},
    ]
    retries = 0
    final_report = ""

    while True:
        # === 内部思考/工具调用循环 ===
        while True:
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                tools=TOOLS,
                tool_choice="auto",
                stream=False
            )
            msg = response.choices[0].message

            if msg.tool_calls:
                for tool_call in msg.tool_calls:
                    func_name = tool_call.function.name
                    args = json.loads(tool_call.function.arguments)
                    yield f"\n🔍 调用工具: {func_name}({args})\n"

                    result = TOOL_FUNCTIONS[func_name](**args)
                    messages.append({
                        "role": "tool",
                        "tool_call_id": tool_call.id,
                        "content": result
                    })
                    # 打印工具返回内容（方便调试，生产环境可去除）
                    print(f"[工具返回]: {result[:200]}...", flush=True)
                messages.append(msg)
                continue
            # 无工具调用，进入报告生成阶段
            break

        # === 流式生成报告 ===
        yield "\n📝 正在生成报告...\n"
        stream = client.chat.completions.create(
            model=model,
            messages=messages,
            stream=True
        )
        full_response = ""
        for chunk in stream:
            if chunk.choices and len(chunk.choices) > 0:
                delta = chunk.choices[0].delta
                if delta and delta.content:
                    token = delta.content
                    full_response += token
                    print(token, end="", flush=True)   # 实时输出
        messages.append({"role": "assistant", "content": full_response})

        # === 自动评审 ===
        yield "\n\n🔎 正在评估报告质量...\n"
        evaluation = evaluate_report(client, model, full_response)
        score = evaluation["score"]
        issues = evaluation["issues"]
        suggestion = evaluation["suggestion"]
        yield f"📊 当前评分: {score}/10\n"
        if issues:
            yield f"⚠️ 发现问题: {'; '.join(issues)}\n"
        yield f"💡 建议: {suggestion}\n"

        # 判断是否达标
        if score >= quality_threshold:
            final_report = full_response
            yield "\n✅ 报告质量达标，输出最终结果。\n"
            break
        else:
            retries += 1
            if retries > max_retries:
                yield f"\n⚠️ 已达最大重试次数（{max_retries}），将使用当前版本。\n"
                final_report = full_response
                break
            # 追加改进指令
            feedback = (f"报告质量评分只有{score}/10，存在以下问题：{'；'.join(issues)}。"
                        f"建议：{suggestion}。请根据这些意见改进报告，若需补充文献请重新检索。")
            messages.append({"role": "user", "content": feedback})
            yield f"\n🔄 正在进行第 {retries} 次改进...\n"

    # === 报告完成后，进入用户交互（多轮对话） ===
    while True:
        user_next = input("\n\n继续提问（或 'end' 结束）: ").strip()
        if user_next.lower() == 'end':
            yield "再见！"
            # break
            return messages
        
        messages.append({"role": "user", "content": user_next})
        yield "\n继续调研...\n"
        # 重新进入工具/报告循环（复用上面的逻辑）
        retries = 0  # 重置重试计数器
        # 注意：这里为了简洁，直接递归调用？更好的做法是抽取内部循环，此处为示例清晰，用循环包装
        # 实际可使用一个子函数来避免重复代码，此处略。