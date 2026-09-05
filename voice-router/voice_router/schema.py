"""路由器内部唯一的契约。前端、模型、硬件三边都只认这个形状。

模型输出必须严格匹配 JSON schema，所以 args 不能是自由字典，
用 name/value 列表表达，出去之前再转成 dict。
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class Arg(BaseModel):
    name: str
    value: str


class Command(BaseModel):
    intent: str = Field(description="意图名，必须是路由表里的一个")
    args: list[Arg] = Field(default_factory=list, description="参数，没有就空列表")
    say: str = Field(description="回给用户的一句短话，十个字以内")
    confidence: float = Field(ge=0, le=1, description="0 到 1，拿不准就低")

    def arg_dict(self) -> dict[str, str]:
        return {a.name: a.value for a in self.args}

    def wire(self) -> dict:
        """发给硬件 / 其他进程的形状。一行 JSON，字段越少越好。"""
        return {"intent": self.intent, "args": self.arg_dict()}


# 严格 schema：additionalProperties 关掉，required 全给。
COMMAND_SCHEMA = {
    "type": "object",
    "properties": {
        "intent": {"type": "string"},
        "args": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {"name": {"type": "string"}, "value": {"type": "string"}},
                "required": ["name", "value"],
                "additionalProperties": False,
            },
        },
        "say": {"type": "string"},
        "confidence": {"type": "number"},
    },
    "required": ["intent", "args", "say", "confidence"],
    "additionalProperties": False,
}
