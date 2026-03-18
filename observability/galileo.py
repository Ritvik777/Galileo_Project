import os
from functools import wraps
from typing import Any, Callable

from config import GALILEO_API_KEY, GALILEO_LOG_STREAM, GALILEO_PROJECT

try:
    from galileo import galileo_context, log as galileo_log
    from galileo.handlers.langchain import GalileoCallback
except Exception:
    galileo_context = None
    galileo_log = None
    GalileoCallback = None

_INITIALIZED = False


def is_galileo_enabled() -> bool:
    return bool(GALILEO_API_KEY and GALILEO_PROJECT and GALILEO_LOG_STREAM and galileo_context and GalileoCallback)


def ensure_galileo_initialized() -> None:
    global _INITIALIZED
    if _INITIALIZED or not is_galileo_enabled():
        return
    galileo_context.init(project=GALILEO_PROJECT, log_stream=GALILEO_LOG_STREAM)
    _INITIALIZED = True


def get_langchain_config(*, metadata: dict[str, Any] | None = None, tags: list[str] | None = None) -> dict[str, Any]:
    if not is_galileo_enabled():
        return {}
    ensure_galileo_initialized()

    logger = galileo_context.get_logger_instance(project=GALILEO_PROJECT, log_stream=GALILEO_LOG_STREAM)
    in_experiment = logger.current_parent() is not None
    callback = GalileoCallback(
        galileo_logger=logger,
        start_new_trace=not in_experiment,
        flush_on_chain_end=not in_experiment,
    )
    config: dict[str, Any] = {"callbacks": [callback]}
    if metadata:
        config["metadata"] = metadata
    if tags:
        config["tags"] = tags
    return config


def log_span(*, span_type: str = "workflow", name: str | None = None) -> Callable:
    if galileo_log:
        kwargs = {"span_type": span_type}
        if name:
            kwargs["name"] = name
        base_decorator = galileo_log(**kwargs)

        def _decorator(fn: Callable) -> Callable:
            decorated = base_decorator(fn)

            @wraps(fn)
            def _wrapped(*args: Any, **kwargs: Any) -> Any:
                ensure_galileo_initialized()
                return decorated(*args, **kwargs)

            return _wrapped

        return _decorator

    def _noop_decorator(fn: Callable) -> Callable:
        @wraps(fn)
        def _wrapped(*args: Any, **kwargs: Any) -> Any:
            return fn(*args, **kwargs)

        return _wrapped

    return _noop_decorator


def get_eval_project(default: str = "galileo-marketing-ai-evals") -> str:
    return os.getenv("GALILEO_EVAL_PROJECT") or GALILEO_PROJECT or default


def start_chat_session(session_name: str) -> bool:
    if not is_galileo_enabled():
        return False
    ensure_galileo_initialized()
    try:
        logger = galileo_context.get_logger_instance(project=GALILEO_PROJECT, log_stream=GALILEO_LOG_STREAM)
        logger.start_session(name=session_name)
        return True
    except Exception:
        return False


def get_logger_instance():
    if not is_galileo_enabled():
        return None
    ensure_galileo_initialized()
    try:
        return galileo_context.get_logger_instance(project=GALILEO_PROJECT, log_stream=GALILEO_LOG_STREAM)
    except Exception:
        return None


def get_console_links() -> dict[str, str]:
    logger = get_logger_instance()
    if logger is None:
        return {}
    try:
        console_url = os.getenv("GALILEO_CONSOLE_URL", "https://app.galileo.ai").rstrip("/")
        project_id = getattr(logger, "project_id", None)
        log_stream_id = getattr(logger, "log_stream_id", None)
        if not project_id or not log_stream_id:
            return {}
        project_url = f"{console_url}/project/{project_id}"
        log_stream_url = f"{project_url}/log-streams/{log_stream_id}"
        return {"project_url": project_url, "log_stream_url": log_stream_url}
    except Exception:
        return {}
