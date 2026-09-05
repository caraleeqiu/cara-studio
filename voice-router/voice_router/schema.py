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


# ---------------------------------------------------------------- 派活
# 一句话拆成几件事。每件事一个 worker 去干，互不等待。

from typing import Literal


class Task(BaseModel):
    id: str = Field(description="短 id：a、b、c")
    worker: Literal["claude_code", "local"] = Field(
        description="claude_code 干需要思考的活；local 干秒回的本地动作")
    action: str = Field(description="local 的动作：switch_app / open_url / dictate；claude_code 固定填 run")
    instruction: str = Field(description="交代给 worker 的话，写清楚要什么结果")
    needs_confirm: bool = Field(description="发送、删除、付款、给别人发消息一律 true")
    notify: bool = Field(description="干完要不要推通知")


class TaskList(BaseModel):
    tasks: list[Task]
    say: str = Field(description="念回给用户的一句话，列出几件事，二十字以内")


TASKLIST_SCHEMA = {
    "type": "object",
    "properties": {
        "tasks": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "id": {"type": "string"},
                    "worker": {"type": "string", "enum": ["claude_code", "local"]},
                    "action": {"type": "string"},
                    "instruction": {"type": "string"},
                    "needs_confirm": {"type": "boolean"},
                    "notify": {"type": "boolean"},
                },
                "required": ["id", "worker", "action", "instruction", "needs_confirm", "notify"],
                "additionalProperties": False,
            },
        },
        "say": {"type": "string"},
    },
    "required": ["tasks", "say"],
    "additionalProperties": False,
}
