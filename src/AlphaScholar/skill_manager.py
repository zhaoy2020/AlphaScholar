'''
skill_manager.py 负责扫描 skills/ 目录，解析每个 SKILL.md 的 YAML 前置元数据和 Markdown 提示词，并暴露两个核心方法：

1. load_skills() → 返回 Skill 对象列表
2. skills_to_tools() → 将 Skill 列表转为 OpenAI Function Calling 的 tools 格式
'''


import yaml
import re
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class Skill:
    name: str
    description: str
    version: str
    tools: List[str] = field(default_factory=list)
    prompt: str = ""
    references: List[str] = field(default_factory=list)  # 引用文本内容
    skill_dir: Path = None

    def to_tool_schema(self) -> dict:
        """将技能转换为 OpenAI Function Calling 的工具定义"""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "要传递给该技能的完整查询语句，包含用户的具体要求"
                        }
                    },
                    "required": ["query"]
                }
            }
        }


class SkillManager:
    def __init__(self, skills_dir: str = "skills"):
        self.skills_dir = Path(skills_dir)
        self.skills: dict[str, Skill] = {}  # name -> Skill

    def load_skills(self):
        """扫描目录，加载所有技能"""
        if not self.skills_dir.exists():
            print(f"⚠️ 技能目录不存在: {self.skills_dir}")
            return
        for skill_dir in self.skills_dir.iterdir():
            if not skill_dir.is_dir():
                continue
            skill_md = skill_dir / "SKILL.md"
            if not skill_md.exists():
                continue
            try:
                skill = self._parse_skill(skill_md)
                skill.skill_dir = skill_dir
                # 加载 references
                if "## References" in skill_md.read_text(encoding='utf-8'):
                    self._load_references(skill)
                self.skills[skill.name] = skill
                print(f"✅ 技能已加载: {skill.name} (v{skill.version})")
            except Exception as e:
                print(f"❌ 加载技能失败 {skill_dir.name}: {e}")

    def _parse_skill(self, skill_md_path: Path) -> Skill:
        content = skill_md_path.read_text(encoding='utf-8')
        # 提取 YAML 头部
        match = re.match(r'^---\n(.*?)\n---\n(.*)', content, re.DOTALL)
        if not match:
            raise ValueError("SKILL.md 缺少 YAML 头部")
        yaml_part = match.group(1)
        markdown = match.group(2).strip()
        metadata = yaml.safe_load(yaml_part)

        # 提取提示词（## 提示词 之后，下一个 ## 或文件结尾之前）
        prompt = ""
        prompt_match = re.search(r'##\s*提示词\s*\n(.*?)(?=\n##|\Z)', markdown, re.DOTALL)
        if prompt_match:
            prompt = prompt_match.group(1).strip()

        return Skill(
            name=metadata.get("name"),
            description=metadata.get("description", ""),
            version=metadata.get("version", "0.1.0"),
            tools=metadata.get("tools", []),
            prompt=prompt
        )

    def _load_references(self, skill: Skill):
        """读取 references 目录下所有 .md 文件内容并存储在 references 列表中"""
        ref_dir = skill.skill_dir / "references"
        if not ref_dir.exists():
            return
        for ref_file in ref_dir.glob("*.md"):
            try:
                content = ref_file.read_text(encoding='utf-8')
                skill.references.append(content)
            except Exception:
                pass

    def get_skill(self, name: str) -> Optional[Skill]:
        return self.skills.get(name)

    def get_all_tool_schemas(self) -> List[dict]:
        """返回所有技能的 OpenAI 工具定义列表"""
        return [skill.to_tool_schema() for skill in self.skills.values()]