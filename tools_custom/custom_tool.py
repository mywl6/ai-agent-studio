import json
import mimetypes
import os
from typing import Optional

import httpx
from backend.services.tool_registry import registry


@registry.register(
    name="custom_tool",
    description=(
        "上传文件到 0330 云盘 (https://pan.0330.top/api.php)。"
        "支持通过 POST 参数或 HTTP Basic Auth 认证。"
        "成功后可获取下载链接和预览链接。"
        "适用于需要将文件上传至第三方云盘并获取公开链接的场景。"
    ),
    icon="🔧",
    category="API",
)
def custom_tool(
    file_path: str,
    username: str,
    password: str,
    show: int = 1,
    ispwd: int = 0,
    pwd: Optional[str] = None,
    format: str = "json",
    callback: Optional[str] = None,
    backurl: Optional[str] = None,
) -> str:
    """
    上传文件到 0330 云盘 (https://pan.0330.top/api.php)。

    根据 API 文档，本函数接受本地文件路径、用户名和密码（支持 POST 参数方式或 Basic Auth 方式），
    可选的展示状态、密码保护等参数，返回上传结果字符串。

    参数:
        file_path: 要上传的本地文件路径（字符串）
        username: 云盘注册用户名
        password: 云盘登录密码
        show: 是否在首页展示（1 展示，0 隐藏，默认 1）
        ispwd: 是否设置下载密码（0 否，1 是，默认 0）
        pwd: 下载密码，仅当 ispwd=1 时有效（只能包含字母和数字）
        format: 返回格式（json/jsonp/form，默认 json）
        callback: JSONP 回调函数名，仅当 format=jsonp 时有效
        backurl: 上传成功后的跳转地址，仅当 format=form 时有效

    返回:
        上传结果字符串。成功时包含下载地址等信息；失败时包含错误信息。

    异常:
        若网络错误、文件不存在或 JSON 解析失败，则返回相应错误描述。
    """
    if not os.path.isfile(file_path):
        return f"文件不存在: {file_path}"

    filename = os.path.basename(file_path)
    mime_type, _ = mimetypes.guess_type(file_path)
    if mime_type is None:
        mime_type = "application/octet-stream"

    url = "https://pan.0330.top/api.php"

    data = {
        "username": username,
        "password": password,
        "show": str(show),
        "ispwd": str(ispwd),
        "format": format,
    }
    if ispwd == 1 and pwd is not None:
        data["pwd"] = pwd
    if format == "jsonp" and callback is not None:
        data["callback"] = callback
    if format == "form" and backurl is not None:
        data["backurl"] = backurl

    try:
        with open(file_path, "rb") as f:
            files = {"file": (filename, f, mime_type)}
            with httpx.Client(timeout=60.0) as client:
                response = client.post(url, files=files, data=data)
    except httpx.RequestError as e:
        return f"网络请求失败: {e}"
    except OSError as e:
        return f"文件读取失败: {e}"

    try:
        result = response.json()
    except json.JSONDecodeError:
        return f"响应解析失败（非 JSON 格式）: {response.text[:200]}"

    code = result.get("code")
    msg = result.get("msg", "无提示信息")

    if code == 0:
        downurl = result.get("downurl", "")
        viewurl = result.get("viewurl", "")
        name = result.get("name", "")
        size = result.get("size", 0)
        hash_str = result.get("hash", "")
        exists = result.get("exists", 0)
        lines = [
            f"上传成功！",
            f"文件: {name} ({size} 字节)",
            f"MD5: {hash_str}",
            f"秒传: {'是' if exists == 1 else '否'}",
        ]
        if downurl:
            lines.append(f"下载地址: {downurl}")
        if viewurl:
            lines.append(f"预览地址: {viewurl}")
        return "\n".join(lines)
    else:
        return f"上传失败 (code={code}): {msg}"