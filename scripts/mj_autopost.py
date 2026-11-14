#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""mj_autopost.py — Midjourney 素体人偶合成后期自动化（mjweb 原生异步 API）

子命令:
  health                             检查 mjweb 服务
  lint   --brief FILE                检查 brief 里的提示词是否踩坑（不调用 API）
  gen    --brief FILE --shot ID      单镜头出图
  batch  --brief FILE                批量出图（先全部提交，再逐个轮询）
  erase  --image FILE                擦除人偶，生成干净背景板
  sheet  --dir DIR                   生成联系表

认证（按优先级）:
  --api-key  /  MJ_API_KEY  /  ~/.config/mjweb/api_key
地址（按优先级）:
  --base  /  MJ_API_BASE  /  ~/.config/mjweb/base  /  http://127.0.0.1:8087
"""

from __future__ import annotations

import argparse
import base64
import json
import os
import re
import shutil
import ssl
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

DEFAULT_BASE = "http://127.0.0.1:8087"
IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".webp"}
GROUP_SIZE = 4

MANNEQUIN = "a slim adult female faceless matte grey artist mannequin with smooth jointed limbs"
COLOR_GATE = "only the mannequin is matte grey, the rest of the scene in full rich color"
DEFAULT_NEGATIVE = [
    "real human", "clothing", "hair", "text", "watermark",
    "monochrome", "grayscale", "clay render", "white model", "desaturated",
]
ERASE_PROMPT = (
    "remove the grey faceless mannequin completely from the scene and reconstruct the empty "
    "background behind it, continue the surrounding architecture, ground texture and lighting "
    "seamlessly, keep the camera angle, framing, perspective, color and every other element "
    "unchanged, photorealistic, cinematic"
)


class ApiError(RuntimeError):
    pass


INSECURE = False
_SSL_CONTEXT = None


def ssl_context():
    """优先用 certifi 的 CA 包；自建服务证书链不完整时可用 --insecure。"""
    global _SSL_CONTEXT
    if _SSL_CONTEXT is None:
        if INSECURE:
            _SSL_CONTEXT = ssl._create_unverified_context()
        else:
            try:
                import certifi
                _SSL_CONTEXT = ssl.create_default_context(cafile=certifi.where())
            except Exception:
                _SSL_CONTEXT = ssl.create_default_context()
    return _SSL_CONTEXT


def now() -> str:
    return datetime.now(timezone.utc).astimezone().isoformat(timespec="seconds")


def die(message: str, code: int = 2):
    print(f"ERROR: {message}", file=sys.stderr)
    raise SystemExit(code)


def read_config(name: str) -> str:
    path = Path.home() / ".config" / "mjweb" / name
    if path.is_file():
        return path.read_text(encoding="utf-8").strip()
    return ""


def resolve_base(args) -> str:
    base = args.base or os.environ.get("MJ_API_BASE") or read_config("base") or DEFAULT_BASE
    return base.rstrip("/")


def resolve_key(args) -> str:
    key = (
        args.api_key
        or os.environ.get("MJ_API_KEY")
        or os.environ.get("MJWEB_API_KEY")
        or read_config("api_key")
    )
    if not key:
        die(
            "缺少 API Key。设置 MJ_API_KEY，或写入 ~/.config/mjweb/api_key。"
            "（mjweb 主 Key 在服务器 /home/admin/mjweb/api_key）"
        )
    return key.strip()


def api_json(base: str, path: str, payload=None, key=None, timeout: int = 60):
    url = base + path
    data = None
    if payload is not None:
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(url, data=data, method="POST" if data is not None else "GET")
    req.add_header("User-Agent", "mj-autopost/1.0")
    if data is not None:
        req.add_header("Content-Type", "application/json")
    if key:
        req.add_header("Authorization", "Bearer " + key)
    try:
        with urllib.request.urlopen(req, timeout=timeout, context=ssl_context()) as resp:
            raw = resp.read()
            return json.loads(raw.decode("utf-8")) if raw else {}
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", "replace")
        try:
            parsed = json.loads(body)
            detail = parsed.get("error") or parsed.get("detail") or parsed
        except Exception:
            detail = body[:800]
        raise ApiError(f"HTTP {exc.code} {path}: {detail}") from None
    except urllib.error.URLError as exc:
        reason = exc.reason
        if isinstance(reason, ssl.SSLError) or "CERTIFICATE_VERIFY_FAILED" in str(reason):
            raise ApiError(
                "TLS 证书校验失败：本机 Python 缺少 CA 或服务端证书链不完整；"
                "可加 --insecure（仅限自建服务）或安装 certifi"
            ) from None
        raise ApiError(f"无法连接 {base}：{reason}") from None


def download(url: str, dest: Path, timeout: int = 180):
    dest.parent.mkdir(parents=True, exist_ok=True)
    req = urllib.request.Request(url, headers={"User-Agent": "mj-autopost/1.0"})
    tmp = dest.with_name(dest.name + ".part")
    try:
        with urllib.request.urlopen(req, timeout=timeout, context=ssl_context()) as resp, open(tmp, "wb") as fh:
            shutil.copyfileobj(resp, fh)
        tmp.replace(dest)
    finally:
        if tmp.exists():
            tmp.unlink(missing_ok=True)


def write_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def safe_id(value: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9._-]+", "-", str(value)).strip("-")
    return cleaned or "shot"


def mannequin_sentence(shot: dict):
    raw = shot.get("mannequin", True)
    if raw is False:
        return None
    if isinstance(raw, dict):
        if raw.get("enabled") is False:
            return None
        size = str(raw.get("size") or "slim adult female").strip()
        size = re.sub(r"^a\s+", "", size, flags=re.I)
        base = f"a {size} faceless matte grey artist mannequin with smooth jointed limbs"
        tails = [str(raw.get(k)).strip() for k in ("pose", "extra") if str(raw.get(k) or "").strip()]
        return base + (", " + ", ".join(tails) if tails else "")
    if isinstance(raw, str):
        text = raw.strip()
        return f"{MANNEQUIN}, {text}" if text else MANNEQUIN
    return MANNEQUIN


def compose(shot: dict, defaults: dict) -> str:
    """按固定骨架拼提示词：焦段→机位→景别→构图→人偶→互动→环境→光线→颜色→画风→参数。"""
    if shot.get("prompt"):
        return str(shot["prompt"]).strip()

    def pick(name: str, fallback: str = "") -> str:
        value = shot.get(name)
        if value is None or value == "":
            value = defaults.get(name, fallback)
        return str(value).strip() if value is not None else ""

    parts = []
    for key in ("focal", "camera", "framing", "composition"):
        value = pick(key)
        if value:
            parts.append(value)

    mannequin = mannequin_sentence(shot)
    if mannequin:
        parts.append(mannequin)

    for key in ("animal", "interaction", "scene", "light", "color"):
        value = pick(key)
        if value:
            parts.append(value)

    style = pick("style", "photorealistic, cinematic")
    if style:
        parts.append(style)

    if mannequin and "only the mannequin is matte grey" not in " ".join(parts).lower():
        parts.append(COLOR_GATE)

    params = pick("params")
    if params:
        parts.append(params)

    descriptive = [p.strip().strip(",") for p in parts if p.strip() and not p.lstrip().startswith("--")]
    param_parts = [p.strip() for p in parts if p.strip().startswith("--")]
    prompt = ", ".join(p for p in descriptive if p)
    if param_parts:
        prompt = (prompt + " " + " ".join(param_parts)).strip()

    negative = shot.get("negative")
    if negative is None:
        negative = defaults.get("negative", DEFAULT_NEGATIVE if mannequin else [])
    negative = [str(x).strip() for x in negative if str(x).strip()]
    negative += [str(x).strip() for x in shot.get("negative_extra", []) if str(x).strip()]
    seen = set()
    deduped = []
    for item in negative:
        token = item.lower()
        if token not in seen:
            seen.add(token)
            deduped.append(item)
    if deduped:
        prompt += " --no " + ", ".join(deduped)
    return prompt


def lint_prompt(prompt: str, shot: dict, defaults: dict, mode: str = "gen"):
    """返回 (errors, warnings)。errors 会阻止提交，warnings 只提示。"""
    errors = []
    warnings = []
    low = prompt.lower()
    no_segment = low.split("--no", 1)[1] if "--no" in low else ""

    if re.search(r"\bsexy\b", low):
        errors.append("含 sexy：改用 graceful S-curve pose / alluring pose / hip cocked")
    for word in ("giant", "huge", "enormous", "colossal"):
        if re.search(rf"\b{word}\b", low):
            errors.append(f"含大小词 {word}：动物会被画成巨兽，删掉只写物种名")

    def terms(value):
        if isinstance(value, str):
            return [value]
        return list(value or [])

    forbidden = terms(defaults.get("forbidden_terms")) + terms(shot.get("forbidden_terms"))
    for term in forbidden:
        term = str(term).strip()
        if term and term.lower() in low:
            errors.append(f"含禁用词“{term}”（角色名/游戏名会把画风拉向原作）")

    mannequin = mannequin_sentence(shot)
    if mannequin:
        if "matte grey artist mannequin" not in low and "matte gray artist mannequin" not in low:
            errors.append("缺少人偶标准句（matte grey artist mannequin）")
        if "only the mannequin is matte grey" not in low:
            warnings.append("缺少颜色锚点句：整张图可能发灰成白模")
        for word in ("real human", "clothing", "hair"):
            if word not in no_segment:
                warnings.append(f"--no 里缺少 {word}")
        for word in ("monochrome", "grayscale", "clay render", "white model", "desaturated"):
            if word not in no_segment:
                warnings.append(f"--no 里缺少防发灰词 {word}")

    if re.search(r"\btiger\b", low) and not re.search(r"\bcat\b|\bkitten\b", no_segment):
        warnings.append("画老虎时建议在 --no 里加 cat, kitten")
    if "full body" in low and "entire body including hands and feet" not in low:
        warnings.append("全身景别建议加 her entire body including hands and feet inside the frame")

    if mode == "erase":
        for word in ("person", "girl", "human", "woman", "people"):
            if re.search(rf"\b{word}\b", low):
                errors.append(f"擦除提示词含 {word}：会把真人招回来，只描述空场景")
    return errors, warnings


def load_brief(path: str) -> dict:
    file = Path(path)
    if not file.is_file():
        die(f"brief 不存在：{file}")
    try:
        data = json.loads(file.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        die(f"brief JSON 解析失败：{exc}")
    if not isinstance(data, dict):
        die("brief 顶层必须是对象")
    shots = data.get("shots")
    if not isinstance(shots, list) or not shots:
        die("brief 缺少非空 shots 数组")
    seen = set()
    for shot in shots:
        if not isinstance(shot, dict) or not shot.get("id"):
            die("每个 shot 必须是对象且带 id")
        sid = str(shot["id"])
        if sid in seen:
            die(f"shot id 重复：{sid}")
        seen.add(sid)
    if not isinstance(data.get("defaults", {}), dict):
        die("brief.defaults 必须是对象")
    return data


def find_shot(brief: dict, shot_id: str) -> dict:
    for shot in brief["shots"]:
        if str(shot["id"]) == shot_id:
            return shot
    ids = ", ".join(str(s["id"]) for s in brief["shots"])
    die(f"找不到 shot {shot_id}；可用：{ids}")


def prepare(shot: dict, defaults: dict, out_root: Path) -> dict:
    shot_dir = out_root / safe_id(str(shot["id"]))
    shot_dir.mkdir(parents=True, exist_ok=True)
    prompt = compose(shot, defaults)
    errors, warnings = lint_prompt(prompt, shot, defaults)
    (shot_dir / "prompt.txt").write_text(prompt + "\n", encoding="utf-8")
    write_json(shot_dir / "lint.json", {"errors": errors, "warnings": warnings})
    return {
        "shot": shot,
        "dir": shot_dir,
        "prompt": prompt,
        "errors": errors,
        "warnings": warnings,
    }


def submitted_prompt(prep: dict, defaults: dict) -> str:
    shot = prep["shot"]
    prompt = prep["prompt"]
    aspect = shot.get("aspect", defaults.get("aspect"))
    if aspect and not re.search(r"(?<!\S)--ar(?:\s|=)", prompt, re.I):
        prompt = f"{prompt} --ar {aspect}"
    return prompt


def submit_prep(base: str, key: str, prep: dict, defaults: dict) -> dict:
    shot = prep["shot"]
    payload = {
        "prompt": submitted_prompt(prep, defaults),
        "version": str(shot.get("version", defaults.get("version", "8.2"))),
        "mode": str(shot.get("mode", defaults.get("mode", "fast"))),
        "private": bool(shot.get("private", defaults.get("private", False))),
    }
    aspect = shot.get("aspect", defaults.get("aspect"))
    if aspect:
        payload["aspect"] = str(aspect)
    res = api_json(base, "/imagine", payload, key=key, timeout=180)
    task_id = res.get("task_id")
    if not task_id:
        raise ApiError(f"提交后未返回 task_id：{res}")
    write_json(prep["dir"] / "task.json", {
        "task_id": task_id,
        "job_id": res.get("job_id"),
        "status": res.get("status"),
        "submitted_at": now(),
        "prompt": payload["prompt"],
    })
    prep["task_id"] = task_id
    return res


def wait_task(base: str, key: str, task_id: str, timeout: int, interval: int = 5) -> dict:
    deadline = time.monotonic() + timeout
    last_status = "UNKNOWN"
    while time.monotonic() < deadline:
        task = api_json(base, f"/task/{task_id}", key=key, timeout=60)
        status = str(task.get("status", "")).upper()
        last_status = status
        urls = task.get("image_urls_abs") or task.get("image_urls") or []
        if status in ("SUCCESS", "PARTIAL", "RETRIEVAL_PAUSED") and urls:
            return task
        if status in ("FAILURE", "SUBMISSION_UNKNOWN"):
            raise ApiError(f"任务 {task_id} 失败：{task.get('error') or status}")
        time.sleep(interval)
    raise ApiError(f"任务 {task_id} 等待超时（最后状态 {last_status}）")


def save_images(base: str, task: dict, dest_dir: Path, prefix: str = ""):
    urls = list(task.get("image_urls_abs") or [])
    if not urls:
        urls = [urllib.parse.urljoin(base + "/", str(u)) for u in task.get("image_urls") or []]
    files = []
    errors = []
    for index, url in enumerate(urls, 1):
        if not url.lower().startswith(("http://", "https://")):
            url = urllib.parse.urljoin(base + "/", url.lstrip("/"))
        suffix = Path(urllib.parse.urlparse(url).path).suffix.lower()
        if suffix not in IMAGE_EXTS:
            suffix = ".png"
        dest = dest_dir / f"{prefix}{index:02d}{suffix}"
        try:
            download(url, dest)
            files.append({"index": index, "url": url, "file": str(dest)})
        except Exception as exc:
            errors.append({"index": index, "url": url, "error": str(exc)})
    return files, errors


def finalize(base: str, key: str, prep: dict, timeout: int, prefix: str = "") -> dict:
    task = wait_task(base, key, prep["task_id"], timeout)
    files, download_errors = save_images(base, task, prep["dir"], prefix=prefix)
    status = "SUCCESS" if files else "FAILED"
    meta = {
        "id": prep["shot"]["id"],
        "status": status,
        "prompt": prep["prompt"],
        "warnings": prep["warnings"],
        "images": files,
        "download_errors": download_errors,
        "task_id": prep["task_id"],
        "finished_at": now(),
        "task": task,
    }
    write_json(prep["dir"] / "meta.json", meta)
    return meta


def write_failure(prep: dict, message: str) -> dict:
    meta = {
        "id": prep["shot"]["id"],
        "status": "FAILED",
        "prompt": prep.get("prompt", ""),
        "warnings": prep.get("warnings", []),
        "error": message,
        "finished_at": now(),
    }
    write_json(prep["dir"] / "meta.json", meta)
    return meta


def print_lint(prep: dict):
    for warning in prep["warnings"]:
        print(f"  ! {prep['shot']['id']}: {warning}")
    for error in prep["errors"]:
        print(f"  x {prep['shot']['id']}: {error}")


def cmd_health(args) -> int:
    base = resolve_base(args)
    print(json.dumps(api_json(base, "/health", timeout=20), ensure_ascii=False))
    return 0


def cmd_lint(args) -> int:
    brief = load_brief(args.brief)
    defaults = brief.get("defaults") or {}
    errors_count = 0
    warnings_count = 0
    for shot in brief["shots"]:
        prompt = compose(shot, defaults)
        errors, warnings = lint_prompt(prompt, shot, defaults)
        errors_count += len(errors)
        warnings_count += len(warnings)
        print(f"[{shot['id']}]")
        for warning in warnings:
            print(f"  ! {warning}")
        for error in errors:
            print(f"  x {error}")
        if not errors and not warnings:
            print("  ok")
    print(f"\n合计：{errors_count} 个错误，{warnings_count} 个提醒")
    return 1 if errors_count else 0


def cmd_gen(args) -> int:
    brief = load_brief(args.brief)
    defaults = brief.get("defaults") or {}
    shot = find_shot(brief, args.shot)
    out_root = Path(args.out or brief.get("output") or brief.get("project") or "mj-runs")
    prep = prepare(shot, defaults, out_root)
    print(f"[{shot['id']}] 提示词：\n{prep['prompt']}\n")
    print_lint(prep)
    if prep["errors"] and not args.allow_lint_errors:
        print("\n存在 lint 错误，已停止提交。加 --allow-lint-errors 可强行提交。", file=sys.stderr)
        return 1
    if args.dry_run:
        print(f"\nDRY RUN：已写入 {prep['dir'] / 'prompt.txt'}")
        return 0
    base = resolve_base(args)
    key = resolve_key(args)
    submit_prep(base, key, prep, defaults)
    print(f"已提交 task={prep['task_id']}，等待出图……")
    try:
        meta = finalize(base, key, prep, args.timeout)
    except ApiError as exc:
        write_failure(prep, str(exc))
        raise
    print(f"完成：{meta['status']}，{len(meta['images'])} 张，目录 {prep['dir']}")
    for image in meta["images"]:
        print(f"  {image['file']}")
    return 0 if meta["status"] == "SUCCESS" else 1


def cmd_batch(args) -> int:
    brief = load_brief(args.brief)
    defaults = brief.get("defaults") or {}
    out_root = Path(args.out or brief.get("output") or brief.get("project") or "mj-runs")

    shots = brief["shots"]
    if args.only:
        wanted = [item.strip() for item in args.only.split(",") if item.strip()]
        shots = [shot for shot in shots if str(shot["id"]) in wanted]
        if not shots:
            die("--only 没有匹配到任何 shot id")

    pending = []
    skipped = 0
    failed = 0
    for shot in shots:
        shot_dir = out_root / safe_id(str(shot["id"]))
        meta_path = shot_dir / "meta.json"
        if not args.force and meta_path.is_file():
            try:
                old = json.loads(meta_path.read_text(encoding="utf-8"))
                files_exist = all(Path(item["file"]).is_file() for item in old.get("images", []))
                if old.get("status") == "SUCCESS" and files_exist:
                    print(f"[{shot['id']}] 已完成，跳过")
                    skipped += 1
                    continue
            except Exception:
                pass
        prep = prepare(shot, defaults, out_root)
        print_lint(prep)
        if prep["errors"] and not args.allow_lint_errors:
            write_failure(prep, "; ".join(prep["errors"]))
            print(f"[{shot['id']}] lint 错误，标记失败", file=sys.stderr)
            failed += 1
            continue
        pending.append(prep)

    if args.dry_run:
        print(f"\nDRY RUN：{len(pending)} 个镜头待提交，输出目录 {out_root}")
        for prep in pending:
            print(f"  {prep['shot']['id']} -> {prep['dir']}")
        return 0

    if not pending:
        print(f"\n没有待提交镜头（跳过 {skipped}，失败 {failed}）")
        return 0

    base = resolve_base(args)
    key = resolve_key(args)

    submitted = []
    for index, prep in enumerate(pending):
        try:
            submit_prep(base, key, prep, defaults)
            print(f"[{prep['shot']['id']}] 已提交 task={prep['task_id']}")
            submitted.append(prep)
        except ApiError as exc:
            write_failure(prep, str(exc))
            print(f"[{prep['shot']['id']}] 提交失败：{exc}", file=sys.stderr)
            failed += 1
        if args.submit_delay > 0 and index < len(pending) - 1:
            time.sleep(args.submit_delay)

    succeeded = 0
    for prep in submitted:
        print(f"[{prep['shot']['id']}] 等待出图……")
        try:
            meta = finalize(base, key, prep, args.timeout)
            if meta["status"] == "SUCCESS":
                succeeded += 1
            else:
                failed += 1
            print(f"[{prep['shot']['id']}] {meta['status']}，{len(meta['images'])} 张")
        except ApiError as exc:
            write_failure(prep, str(exc))
            print(f"[{prep['shot']['id']}] 失败：{exc}", file=sys.stderr)
            failed += 1

    print(f"\n汇总：成功 {succeeded}，跳过 {skipped}，失败 {failed}，共 {len(shots)} 个镜头")
    print(f"输出目录：{out_root}")
    if succeeded:
        print(f"联系表：python3 {Path(__file__).name} sheet --dir {out_root}")
    return 0 if failed == 0 else 1


def cmd_erase(args) -> int:
    image = Path(args.image)
    if not image.is_file():
        die(f"图片不存在：{image}")
    out_dir = Path(args.out) if args.out else image.parent / "clean"
    out_dir.mkdir(parents=True, exist_ok=True)
    prompt = (args.prompt or ERASE_PROMPT).strip()
    errors, warnings = lint_prompt(prompt, {"id": "erase", "mannequin": False}, {}, mode="erase")
    print(f"擦除提示词：\n{prompt}\n")
    for warning in warnings:
        print(f"  ! {warning}")
    for error in errors:
        print(f"  x {error}")
    if errors and not args.allow_person_words:
        die("擦除提示词包含会招回真人的词，已停止。改提示词或加 --allow-person-words。")
    if args.dry_run:
        print(f"\nDRY RUN：输出目录 {out_dir}")
        return 0

    base = resolve_base(args)
    key = resolve_key(args)
    suffix = image.suffix.lower()
    mime = "image/jpeg" if suffix in (".jpg", ".jpeg") else "image/webp" if suffix == ".webp" else "image/png"
    encoded = base64.b64encode(image.read_bytes()).decode("ascii")
    payload = {
        "prompt": prompt,
        "version": args.version,
        "mode": args.mode,
        "private": False,
        "image_base64": f"data:{mime};base64,{encoded}",
    }
    res = api_json(base, "/imagine", payload, key=key, timeout=240)
    task_id = res.get("task_id")
    if not task_id:
        die(f"提交后未返回 task_id：{res}")
    write_json(out_dir / "erase-task.json", {
        "source": str(image),
        "task_id": task_id,
        "job_id": res.get("job_id"),
        "prompt": prompt,
        "submitted_at": now(),
    })
    print(f"已提交 task={task_id}，等待出图……")
    task = wait_task(base, key, task_id, args.timeout)
    files, download_errors = save_images(base, task, out_dir, prefix="clean-")
    write_json(out_dir / "erase-meta.json", {
        "source": str(image),
        "status": "SUCCESS" if files else "FAILED",
        "prompt": prompt,
        "images": files,
        "download_errors": download_errors,
        "task_id": task_id,
        "finished_at": now(),
        "task": task,
    })
    print(f"完成：{len(files)} 张，目录 {out_dir}")
    for item in files:
        print(f"  {item['file']}")
    print("提醒：reference edit 会整图重绘，必须逐张目检残肢、灰影、倒影和构图漂移。")
    return 0 if files else 1


def cmd_sheet(args) -> int:
    root = Path(args.dir)
    if not root.is_dir():
        die(f"目录不存在：{root}")
    out = Path(args.out) if args.out else root / "sheet.jpg"
    out.parent.mkdir(parents=True, exist_ok=True)
    files = sorted(
        path for path in root.rglob("*")
        if path.is_file()
        and path.suffix.lower() in IMAGE_EXTS
        and path.resolve() != out.resolve()
    )
    if not files:
        die(f"{root} 里没有图片")
    files = files[: args.limit]

    try:
        from PIL import Image, ImageDraw
    except ImportError:
        html_path = out.with_suffix(".html")
        items = []
        for path in files:
            rel = os.path.relpath(path, html_path.parent)
            items.append(f'<figure><img src="{rel}" loading="lazy"><figcaption>{rel}</figcaption></figure>')
        html_path.write_text(
            "<!doctype html><meta charset='utf-8'><title>MJ contact sheet</title>"
            "<style>body{background:#eee;font:12px -apple-system,sans-serif;margin:16px}"
            "main{display:grid;grid-template-columns:repeat(auto-fill,minmax(240px,1fr));gap:12px}"
            "figure{background:#fff;margin:0;padding:8px}img{width:100%;height:auto}"
            "figcaption{color:#333;margin-top:4px;word-break:break-all}</style>"
            "<main>" + "".join(items) + "</main>",
            encoding="utf-8",
        )
        print(f"未安装 Pillow，已生成 HTML 联系表：{html_path}")
        return 0

    thumb_w = args.thumb
    thumb_h = int(thumb_w * 0.75)
    label_h = 24
    cols = max(1, args.cols)
    rows = (len(files) + cols - 1) // cols
    canvas = Image.new("RGB", (cols * thumb_w, rows * (thumb_h + label_h)), (245, 245, 245))
    draw = ImageDraw.Draw(canvas)
    for index, path in enumerate(files):
        try:
            image = Image.open(path)
            image.thumbnail((thumb_w, thumb_h))
        except Exception:
            continue
        x = (index % cols) * thumb_w
        y = (index // cols) * (thumb_h + label_h)
        canvas.paste(image, (x + (thumb_w - image.width) // 2, y + (thumb_h - image.height) // 2))
        label = path.relative_to(root).as_posix()
        if len(label) > 46:
            label = "..." + label[-43:]
        draw.text((x + 6, y + thumb_h + 5), label, fill=(40, 40, 40))
    canvas.save(out, quality=88)
    print(f"联系表：{out}（{len(files)} 张）")
    return 0


def build_parser():
    parser = argparse.ArgumentParser(
        description="Midjourney 素体人偶合成后期自动化（mjweb 原生异步 API）"
    )
    sub = parser.add_subparsers(dest="command", required=True)

    def add_common(target):
        target.add_argument("--base", help="mjweb 地址，默认读 MJ_API_BASE / ~/.config/mjweb/base")
        target.add_argument("--api-key", help="mjweb Key，默认读 MJ_API_KEY / ~/.config/mjweb/api_key")
        target.add_argument("--insecure", action="store_true", help="跳过 TLS 证书校验（仅限自建服务）")

    health = sub.add_parser("health", help="检查 mjweb 服务")
    add_common(health)
    health.set_defaults(func=cmd_health)

    lint = sub.add_parser("lint", help="检查 brief 提示词（不调用 API）")
    add_common(lint)
    lint.add_argument("--brief", required=True)
    lint.set_defaults(func=cmd_lint)

    gen = sub.add_parser("gen", help="单镜头出图")
    add_common(gen)
    gen.add_argument("--brief", required=True)
    gen.add_argument("--shot", required=True)
    gen.add_argument("--out", help="输出根目录，默认 brief.output")
    gen.add_argument("--dry-run", action="store_true", help="只拼提示词和 lint，不提交")
    gen.add_argument("--timeout", type=int, default=1800, help="单任务等待秒数，默认 1800")
    gen.add_argument("--allow-lint-errors", action="store_true")
    gen.set_defaults(func=cmd_gen)

    batch = sub.add_parser("batch", help="批量出图")
    add_common(batch)
    batch.add_argument("--brief", required=True)
    batch.add_argument("--out", help="输出根目录，默认 brief.output")
    batch.add_argument("--only", help="只跑这些 id，逗号分隔")
    batch.add_argument("--force", action="store_true", help="忽略已完成记录，重跑")
    batch.add_argument("--dry-run", action="store_true", help="只拼提示词和 lint，不提交")
    batch.add_argument("--timeout", type=int, default=1800, help="单任务等待秒数，默认 1800")
    batch.add_argument("--submit-delay", type=float, default=2.0, help="提交间隔秒数，默认 2")
    batch.add_argument("--allow-lint-errors", action="store_true")
    batch.set_defaults(func=cmd_batch)

    erase = sub.add_parser("erase", help="擦除人偶，生成干净背景板")
    add_common(erase)
    erase.add_argument("--image", required=True)
    erase.add_argument("--prompt", help="自定义擦除提示词；默认只描述空场景")
    erase.add_argument("--out", help="输出目录，默认图片旁的 clean/")
    erase.add_argument("--version", default="8.2", help="仅 V8.1/V8.2 支持垫图编辑")
    erase.add_argument("--mode", default="fast", choices=("fast", "relax"))
    erase.add_argument("--timeout", type=int, default=1800)
    erase.add_argument("--dry-run", action="store_true")
    erase.add_argument("--allow-person-words", action="store_true")
    erase.set_defaults(func=cmd_erase)

    sheet = sub.add_parser("sheet", help="生成联系表")
    add_common(sheet)
    sheet.add_argument("--dir", required=True)
    sheet.add_argument("--out", help="输出文件，默认 dir/sheet.jpg")
    sheet.add_argument("--cols", type=int, default=5)
    sheet.add_argument("--thumb", type=int, default=360)
    sheet.add_argument("--limit", type=int, default=60)
    sheet.set_defaults(func=cmd_sheet)

    return parser


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    global INSECURE
    INSECURE = bool(getattr(args, "insecure", False) or os.environ.get("MJ_INSECURE") == "1")
    try:
        return args.func(args)
    except ApiError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    except KeyboardInterrupt:
        print("已中断", file=sys.stderr)
        return 130


if __name__ == "__main__":
    raise SystemExit(main())
