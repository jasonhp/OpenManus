import asyncio
import json
import re
import time
import uuid
from collections import deque
from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set, Union

from openai.types.chat.chat_completion_message import ChatCompletionMessage
from pydantic import BaseModel, Field, field_serializer, model_validator

from app.tool import base


class AgentStatus(str, Enum):
    """agent status enum - use str inheritance for automatic serialization"""

    ERROR = "error"
    RUNNING = "running"
    STOPPED = "stopped"
    TERMINATED = "terminated"


@dataclass
class Message:
    """tool usage message"""

    action: Optional[str] = None
    param: Optional[str] = None


class MessageType(str, Enum):
    """message type enum - use str inheritance for automatic serialization"""

    TEXT = "text"


class Sender(str, Enum):
    """message sender enum - use str inheritance for automatic serialization"""

    ASSISTANT = "assistant"
    USER = "user"


@dataclass
class Step:
    """task planning return result"""

    result: Optional[str] = None
    step: Optional[int] = None
    type: Optional[str] = None


@dataclass
class Bash:
    command: str
    result: str


@dataclass
class CreateChatCompletion:
    result: Optional[Union[float, int, bool, str, List[Any], Dict[str, Any]]] = None
    response: Optional[Union[float, int, bool, str, List[Any], Dict[str, Any]]] = None


@dataclass
class ToolResult:
    """ToolResult"""

    output: str
    base64_image: Optional[str] = None
    error: Optional[str] = None
    system: Optional[str] = None


@dataclass
class Planning:
    command: str
    result: ToolResult
    plan_id: Optional[str] = None
    step_index: Optional[str] = None
    step_notes: Optional[str] = None
    step_status: Optional[str] = None
    steps: Optional[List[str]] = None
    title: Optional[str] = None


@dataclass
class StrReplaceEditor:
    command: str
    path: str
    result: ToolResult
    """for create"""
    file_text: Optional[str] = None
    insert_line: Optional[str] = None
    new_str: Optional[str] = None
    old_str: Optional[str] = None
    view_range: Optional[List[int]] = None


class Status(str, Enum):
    """status enum - use str inheritance for automatic serialization"""

    FAILURE = "failure"
    SUCCESS = "success"


@dataclass
class Terminate:
    result: str
    status: Status


@dataclass
class BrowserUseTool:
    """browser use tool detail"""

    # required parameters
    action: str

    # optional parameters
    url: Optional[str] = None
    index: Optional[int] = None
    text: Optional[str] = None
    scroll_amount: Optional[int] = None
    tab_id: Optional[int] = None
    query: Optional[str] = None
    goal: Optional[str] = None
    keys: Optional[str] = None
    seconds: Optional[int] = None

    # result fields
    result: Optional[str] = None
    status: Optional[str] = None
    error: Optional[str] = None
    output: Optional[str] = None
    base64_image: Optional[str] = None
    system: Optional[str] = None

    # extra data
    extra_data: Dict[str, Any] = Field(default_factory=dict)

    def __post_init__(self):
        """pass extra data"""
        for key, value in self.__dict__.copy().items():
            if key not in self.__annotations__ and key != "extra_data":
                self.extra_data[key] = value
                delattr(self, key)


@dataclass
class WebSearch:
    """web search detail"""

    query: str
    result: List[str]


class COSUpload(BaseModel):
    """COS upload operation details"""

    file_path: Optional[str] = None
    content: Optional[str] = None
    file_name: Optional[str] = None
    directory: Optional[str] = None
    url: Optional[str] = None
    result: Optional[ToolResult] = None


class R2Upload(BaseModel):
    """R2 upload operation details"""

    file_path: Optional[str] = None
    content: Optional[str] = None
    file_name: Optional[str] = None
    directory: Optional[str] = None
    result: Optional[ToolResult] = None


class ToolStatus(str, Enum):
    """tool usage status enum - use str inheritance for automatic serialization"""

    EXECUTING = "executing"
    FAIL = "fail"
    SUCCESS = "success"


class TypeEnum(str, Enum):
    """event type enum - use str inheritance for automatic serialization"""

    ACT = "act"
    CHAT = "chat"
    COMPLETE = "complete"
    LIVE_STATUS = "liveStatus"
    RESULT = "result"
    STATUS_UPDATE = "statusUpdate"
    STEP = "step"
    THINK = "think"
    TOOL = "tool"
    TOOL_USED = "toolUsed"
    PLAN_UPDATE = "planUpdate"


class Message(BaseModel):
    """tool usage message"""

    action: Optional[str] = None
    param: Optional[str] = None


class Step(BaseModel):
    """task planning return result"""

    id: Optional[str] = None
    title: Optional[str] = None
    status: Optional[str] = None


class ToolResult(BaseModel):
    """tool result"""

    output: Optional[str] = None
    base64_image: Optional[str] = None
    error: Optional[str] = None
    system: Optional[str] = None
    url: Optional[str] = None


class BrowserUseTool(BaseModel):
    """browser tool detail"""

    action: str
    url: Optional[str] = None
    index: Optional[int] = None
    text: Optional[str] = None
    scroll_amount: Optional[int] = None
    tab_id: Optional[int] = None
    query: Optional[str] = None
    goal: Optional[str] = None
    keys: Optional[str] = None
    seconds: Optional[int] = None
    result: Optional[ToolResult] = None
    status: Optional[str] = None
    extra_data: Dict[str, Any] = Field(default_factory=dict)


class WebSearch(BaseModel):
    """web search detail"""

    query: str
    result: List[str]


class Bash(BaseModel):
    """bash command detail"""

    command: str
    result: str


class CreateChatCompletion(BaseModel):
    """chat completion detail"""

    result: Optional[Any] = None
    response: Optional[Any] = None


class StrReplaceEditor(BaseModel):
    """str replace editor detail"""

    command: Optional[str] = None
    path: Optional[str] = None
    result: Optional[ToolResult] = None
    file_text: Optional[str] = None
    insert_line: Optional[str] = None
    new_str: Optional[str] = None
    old_str: Optional[str] = None
    view_range: Optional[List[int]] = None


class Terminate(BaseModel):
    """terminate detail"""

    result: str
    status: Status


class Planning(BaseModel):
    """planning detail"""

    command: str
    result: ToolResult
    plan_id: Optional[str] = None
    step_index: Optional[int] = None
    step_notes: Optional[str] = None
    step_status: Optional[str] = None
    steps: Optional[List[str]] = None
    title: Optional[str] = None


class PythonExecResul(BaseModel):
    output: Optional[str] = None
    success: Optional[bool] = None


class PythonExecute(BaseModel):
    """python execute detail"""

    code: Optional[str] = None
    result: Optional[ToolResult] = None


class DeployWebsite(BaseModel):
    """Website deployment operation details"""

    folder_path: Optional[str] = None
    site_name: Optional[str] = None
    file_count: Optional[int] = None
    entry_url: Optional[str] = None
    result: Optional[ToolResult] = None


class VerifyWebsite(BaseModel):
    url: str
    title: Optional[str] = None
    status_code: Optional[int] = None
    success: bool = False
    issue_count: Optional[int] = None
    success_count: Optional[int] = None
    resource_count: Optional[int] = None


class ToolDetail(BaseModel):
    """tool result detail"""

    create_chat_completion: Optional[CreateChatCompletion] = None
    planning: Optional[Planning] = None
    bash: Optional[Bash] = None
    browser_use: Optional[BrowserUseTool] = None
    web_search: Optional[WebSearch] = None
    str_replace_editor: Optional[StrReplaceEditor] = None
    terminate: Optional[Terminate] = None
    python_execute: Optional[PythonExecute] = None
    cos_upload: Optional[COSUpload] = None
    r2_upload: Optional[R2Upload] = None
    deploy_website: Optional[DeployWebsite] = None
    verify_website: Optional[VerifyWebsite] = None
    finish: Optional[str] = None


class Event(BaseModel):
    """event"""

    # event type (required)
    type: TypeEnum

    # event id - default auto generate
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))

    # timestamp - default current time
    timestamp: int = Field(default_factory=lambda: int(time.time() * 1000))

    # optional fields
    error: Optional[str] = None
    tool_selected: Optional[List[str]] = None
    action_id: Optional[str] = None
    agent_status: Optional[AgentStatus] = None
    attachments: Optional[List[Dict[str, Any]]] = None
    content: Optional[str] = None
    message: Optional[Message] = None
    message_type: Optional[MessageType] = None
    no_render: Optional[bool] = None
    plan_step_id: Optional[str] = None
    sender: Optional[Sender] = None
    step: Optional[int] = None
    steps: Optional[List[Step]] = None
    text: Optional[str] = None
    tool: Optional[str] = None
    tool_detail: Optional[ToolDetail] = None
    tool_status: Optional[ToolStatus] = None

    class Config:
        """Pydantic config"""

        # allow extra fields
        extra = "allow"
        # auto use enum values
        use_enum_values = True
        # exclude fields with default value None
        exclude_none = True


class EventManager:
    def __init__(self, max_events: int = 1000):
        self.events: deque = deque(maxlen=max_events)
        self.clients: Set[asyncio.Queue] = set()
        self._lock = asyncio.Lock()

    async def add_event(self, event: Event) -> None:
        """add event to event list"""
        async with self._lock:
            self.events.append(event)
            await self._notify_clients(event)

    async def _notify_clients(self, event: Event) -> None:
        """notify all connected clients"""
        for client in list(self.clients):
            try:
                await client.put(event)
            except Exception:
                self.clients.discard(client)

    async def connect_client(self, queue: asyncio.Queue, replay: bool = False) -> None:
        """add new client connection"""
        if replay:
            for event in self.events:
                await queue.put(event)
        self.clients.add(queue)

    async def disconnect_client(self, queue: asyncio.Queue) -> None:
        """disconnect client connection"""
        self.clients.discard(queue)

    async def planning_result(
        self,
        args: Any,
        result: Any,
    ) -> Event:
        """process planning result from tool"""
        print(f"Debug planning_result args: {args}, result: {result}")
        print("---------")

        # progress steps
        steps_list = args.get("steps")
        steps = None
        if steps_list and isinstance(steps_list, list):
            steps = [
                Step(id=str(i), title=step, status="not_started")
                for i, step in enumerate(steps_list)
            ]

            # if command is mark_step, update specific step status
            if (
                args.get("command") == "mark_step"
                and args.get("step_index") is not None
            ):
                step_index = int(args.get("step_index"))
                if 0 <= step_index < len(steps):
                    steps[step_index].status = args.get("step_status", "not_started")

        # get command type and plan id
        command = args.get("command", "")
        plan_id = args.get("plan_id", "")
        title = args.get("title", "")

        # create and send event
        event = Event(
            type=TypeEnum.PLAN_UPDATE,
            plan_step_id=plan_id,
            steps=steps,
            tool="planning",
            tool_detail=ToolDetail(
                planning=Planning(
                    command=command,
                    plan_id=plan_id,
                    title=title,
                    step_index=args.get("step_index"),
                    step_notes=args.get("step_notes"),
                    step_status=args.get("step_status"),
                    steps=steps_list,
                    result=ToolResult(
                        output=(
                            result.output if hasattr(result, "output") else str(result)
                        ),
                        base64_image=getattr(result, "base64_image", None),
                        error=getattr(result, "error", None),
                        system=getattr(result, "system", None),
                    ),
                )
            ),
        )
        await self.add_event(event)
        return event

    async def tool_used(
        self, tool_name: str, args: Any, result: Any, success: bool = True
    ) -> Event:
        """process tool used"""
        print("debug {tool_name} ===============")
        if tool_name == "python_execute":
            python_execute = PythonExecute(
                code=args.get("code", ""),
                result=ToolResult(
                    output=(
                        result.output if hasattr(result, "output") else str(result)
                    ),
                    error=None,
                    system=None,
                ),
            )
            event = Event(
                type=TypeEnum.TOOL_USED,
                tool=tool_name,
                tool_selected=tool_name,
                tool_status=ToolStatus.SUCCESS if success else ToolStatus.FAIL,
                content=str(result),
                tool_detail=ToolDetail(python_execute=python_execute),
            )
            await self.add_event(event)
            return event

    async def think(self, result: Any) -> Event:
        """process think result"""
        if isinstance(result, ChatCompletionMessage):
            chat_completion = CreateChatCompletion(
                result=result.content,
                response=result.content,
            )
            event = Event(
                type=TypeEnum.THINK,
                content=result.content,
                sender=Sender.ASSISTANT,
                tool_detail=ToolDetail(create_chat_completion=chat_completion),
            )
            await self.add_event(event)
            return event

    async def tool_result(
        self,
        tool_name: str,
        args: Any,
        result: Any,
        success: bool = True,
        plan_id: str = "",
    ) -> Event:
        """process tool result"""
        # 1. web_search tool
        if tool_name == "web_search":
            if isinstance(args, dict) and isinstance(result, base.ToolResult):
                web_search = WebSearch(
                    query=args.get("query"),
                    result=(
                        [result.output]
                        if isinstance(result.output, str)
                        else result.output
                    ),
                )
                event = Event(
                    type=TypeEnum.TOOL_USED,
                    tool=tool_name,
                    plan_step_id=plan_id,
                    tool_status=ToolStatus.SUCCESS if success else ToolStatus.FAIL,
                    content=str(result),
                    tool_detail=ToolDetail(web_search=web_search),
                )
                await self.add_event(event)
                return event

        # 2. browser_use tool
        elif tool_name == "browser_use":
            if isinstance(args, dict) and isinstance(result, base.ToolResult):
                browser_use = BrowserUseTool(
                    action=args.get("action"),
                    url=args.get("url"),
                    index=args.get("index"),
                    text=args.get("text"),
                    scroll_amount=args.get("scroll_amount"),
                    tab_id=args.get("tab_id"),
                    query=args.get("query"),
                    goal=args.get("goal"),
                    keys=args.get("keys"),
                    seconds=args.get("seconds"),
                    result=ToolResult(
                        output=result.output,
                        base64_image=result.base64_image,
                        error=result.error,
                        system=result.system,
                        url=result.url,
                    ),
                )
                event = Event(
                    type=TypeEnum.TOOL_USED,
                    tool=tool_name,
                    tool_status=ToolStatus.SUCCESS if success else ToolStatus.FAIL,
                    content=str(result),
                    tool_detail=ToolDetail(browser_use=browser_use),
                )
                await self.add_event(event)
                return event

        # 3. str_replace_editor tool
        elif tool_name == "str_replace_editor":
            if isinstance(args, dict) and isinstance(result, base.ToolResult):
                print(f"str_replace_editor args: {args}, result: {result}")
                editor = StrReplaceEditor(
                    command=args.get("command", ""),
                    path=args.get("path", ""),
                    file_text=args.get("file_text"),
                    insert_line=args.get("insert_line"),
                    new_str=args.get("new_str"),
                    old_str=args.get("old_str"),
                    view_range=args.get("view_range"),
                    result=ToolResult(
                        output=result.output,
                        base64_image=result.base64_image,
                        error=result.error,
                        system=result.system,
                    ),
                )
                event = Event(
                    type=TypeEnum.TOOL_USED,
                    tool=tool_name,
                    tool_status=ToolStatus.SUCCESS if success else ToolStatus.FAIL,
                    content=str(result),
                    tool_detail=ToolDetail(str_replace_editor=editor),
                )
                await self.add_event(event)
                return event

        # 4. bash tool
        elif tool_name == "bash":
            if isinstance(args, dict):
                bash = Bash(
                    command=args.get("command", ""),
                    result=(
                        result.output
                        if isinstance(result, base.ToolResult)
                        else str(result)
                    ),
                )
                event = Event(
                    type=TypeEnum.TOOL_USED,
                    tool=tool_name,
                    tool_status=ToolStatus.SUCCESS if success else ToolStatus.FAIL,
                    content=str(result),
                    tool_detail=ToolDetail(bash=bash),
                )
                await self.add_event(event)
                return event

        # 5. terminate toolinate tool
        elif tool_name == "terminate":
            status = Status.SUCCESS if success else Status.FAILURE
            terminate = Terminate(
                result=(
                    result.output
                    if isinstance(result, base.ToolResult)
                    else str(result)
                ),
                status=status,
            )
            event = Event(
                type=TypeEnum.TOOL_USED,
                tool=tool_name,
                tool_status=ToolStatus.SUCCESS if success else ToolStatus.FAIL,
                content=str(result),
                tool_detail=ToolDetail(terminate=terminate),
            )
            await self.add_event(event)
            return event

        # 6. cos_upload tool
        elif tool_name == "cos_upload":
            if isinstance(args, dict) and isinstance(result, base.ToolResult):
                cos_upload = COSUpload(
                    file_path=args.get("file_path"),
                    content=args.get("content"),
                    file_name=args.get("file_name"),
                    directory=args.get("directory"),
                    url=args.get("url"),
                    result=ToolResult(
                        output=result.output,
                        base64_image=result.base64_image,
                        error=result.error,
                        system=result.system,
                    ),
                )
                event = Event(
                    type=TypeEnum.TOOL_USED,
                    tool=tool_name,
                    tool_status=ToolStatus.SUCCESS if success else ToolStatus.FAIL,
                    content=str(result),
                    tool_detail=ToolDetail(cos_upload=cos_upload),
                )
                await self.add_event(event)
                return event

        # 7. r2_upload tool
        elif tool_name == "r2_upload":
            if isinstance(args, dict) and isinstance(result, base.ToolResult):
                # Convert base.ToolResult to dictionary
                result_dict = {
                    "output": (
                        result.output if hasattr(result, "output") else str(result)
                    ),
                    "base64_image": (
                        result.base64_image if hasattr(result, "base64_image") else None
                    ),
                    "error": result.error if hasattr(result, "error") else None,
                    "system": result.system if hasattr(result, "system") else None,
                }

                r2_upload = R2Upload(
                    file_path=args.get("file_path"),
                    content=args.get("content"),
                    file_name=args.get("file_name"),
                    directory=args.get("directory"),
                    result=result_dict,
                )
                event = Event(
                    type=TypeEnum.TOOL_USED,
                    tool=tool_name,
                    tool_status=ToolStatus.SUCCESS if success else ToolStatus.FAIL,
                    content=str(result),
                    tool_detail=ToolDetail(r2_upload=r2_upload),
                )
                await self.add_event(event)
                return event

        # 8. deploy_website tool
        elif tool_name == "deploy_website":
            if isinstance(args, dict) and isinstance(result, base.ToolResult):
                # Extract file count from result output if available
                file_count = None
                if hasattr(result, "output"):
                    count_match = re.search(r"Files uploaded \((\d+)\)", result.output)
                    if count_match:
                        file_count = int(count_match.group(1))

                # Convert base.ToolResult to dictionary
                result_dict = {
                    "output": (
                        result.output if hasattr(result, "output") else str(result)
                    ),
                    "base64_image": (
                        result.base64_image if hasattr(result, "base64_image") else None
                    ),
                    "error": result.error if hasattr(result, "error") else None,
                    "system": result.system if hasattr(result, "system") else None,
                }

                deploy_website = DeployWebsite(
                    folder_path=args.get("folder_path"),
                    site_name=args.get("site_name"),
                    file_count=file_count,
                    entry_url=result.url if hasattr(result, "url") else None,
                    result=result_dict,
                )

                event = Event(
                    type=TypeEnum.TOOL_USED,
                    tool=tool_name,
                    tool_status=ToolStatus.SUCCESS if success else ToolStatus.FAIL,
                    content=str(result),
                    tool_detail=ToolDetail(deploy_website=deploy_website),
                )
                await self.add_event(event)
                return event

        # 9. planning tool
        elif tool_name == "planning":
            if isinstance(args, dict) and isinstance(result, base.ToolResult):
                planning = Planning(
                    command=args.get("command", ""),
                    result=result,
                    plan_id=args.get("plan_id"),
                    step_index=args.get("step_index"),
                    step_notes=args.get("step_notes"),
                    step_status=args.get("step_status"),
                    steps=args.get("steps"),
                    title=args.get("title"),
                )
                event = Event(
                    type=TypeEnum.TOOL_USED,
                    tool=tool_name,
                    tool_status=ToolStatus.SUCCESS if success else ToolStatus.FAIL,
                    content=str(result),
                    tool_detail=ToolDetail(planning=planning),
                )
                await self.add_event(event)
                return event

        # 10. python_execute tool
        elif tool_name == "python_execute":
            if isinstance(args, dict):
                python_execute = PythonExecute(
                    code=args.get("code", ""),
                    result=ToolResult(
                        output=result.get("observation", ""),
                        error=None,
                        system=None,
                    ),
                )
                event = Event(
                    type=TypeEnum.TOOL_USED,
                    tool=tool_name,
                    tool_status=ToolStatus.SUCCESS if success else ToolStatus.FAIL,
                    content=str(result),
                    tool_detail=ToolDetail(python_execute=python_execute),
                )
                await self.add_event(event)
                return event

        # 11. finish tool
        elif tool_name == "finish":
            finish_result = args.get("result", "")
            if not finish_result and hasattr(result, "output"):
                finish_result = result.output

            event = Event(
                type=TypeEnum.TOOL_USED,
                tool=tool_name,
                tool_status=ToolStatus.SUCCESS,
                content=finish_result,
                tool_detail=ToolDetail(finish=finish_result),
            )
            await self.add_event(event)

            # Also send completion event
            await self.complete(finish_result)
            return event

        # 12. verify_website tool
        elif tool_name == "verify_website":
            # Convert tool result to dict
            result_dict = {
                "output": result.output,
                "error": result.error,
                "url": getattr(result, "url", None),
            }

            # Extract metadata from output
            title_match = re.search(r"Title: (.*)\n", result.output)
            title = title_match.group(1) if title_match else None

            status_match = re.search(r"Status: (\d+)\n", result.output)
            status_code = int(status_match.group(1)) if status_match else None

            resource_match = re.search(r"Resource count: (\d+)\n", result.output)
            resource_count = int(resource_match.group(1)) if resource_match else None

            success_count_match = re.search(r"(\d+)\. ", result.output)
            success_count = (
                len(
                    re.findall(r"Successes:\n(.*?)(?:\n\n|$)", result.output, re.DOTALL)
                )
                if "Successes:" in result.output
                else 0
            )

            issue_count_match = (
                re.search(r"(\d+) issues found", result.error) if result.error else None
            )
            issue_count = int(issue_count_match.group(1)) if issue_count_match else 0

            # Determine success based on error
            success = result.error is None or "mostly successful" in result.output

            # Create VerifyWebsite instance
            verify_website = VerifyWebsite(
                url=result_dict.get("url", ""),
                title=title,
                status_code=status_code,
                success=success,
                issue_count=issue_count,
                success_count=success_count,
                resource_count=resource_count,
            )

            # Create event
            event = Event(
                type=TypeEnum.TOOL_USED,
                tool=tool_name,
                tool_status=ToolStatus.SUCCESS if success else ToolStatus.FAIL,
                content=f"Website verification {'succeeded' if success else 'failed'}: {verify_website.url}",
                tool_detail=ToolDetail(
                    verify_website=verify_website,
                ),
            )
            await self.add_event(event)
            return event

        # 13. default: handle other tool types
        event = Event(
            type=TypeEnum.TOOL_USED,
            tool=tool_name,
            tool_detail=ToolDetail(**{tool_name: args}) if args else None,
        )
        await self.add_event(event)
        return event

    async def error(self, error_message: str) -> Event:
        """record error"""
        event = Event(
            type=TypeEnum.STATUS_UPDATE,
            agentStatus=AgentStatus.ERROR,
            error=error_message,
        )
        await self.add_event(event)
        return event

    async def complete(self, final_result: str = None) -> Event:
        """record task complete"""
        event = Event(
            type=TypeEnum.COMPLETE,
            agentStatus=AgentStatus.STOPPED,
            content=final_result,
        )
        await self.add_event(event)
        return event

    def get_json_events(self) -> List[str]:
        """get all events json string list"""
        return [event.model_dump_json() for event in self.events]

    async def event_json_generator(self, replay: bool = True):
        """provide event json stream generator"""
        # send all existing events (if needed)
        if replay:
            for event in self.events:
                yield event.model_dump_json()

        # create queue to receive new events
        queue = asyncio.Queue()
        self.clients.add(queue)

        try:
            while True:
                # wait for new event
                event = await queue.get()
                # output as json
                yield event.model_dump_json()
        finally:
            # clean
            self.clients.discard(queue)
