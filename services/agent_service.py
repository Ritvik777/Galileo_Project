from agents import ask, get_graph_image, get_graph_ascii


def ask_agent(question: str) -> dict:
    return ask(question)


def load_graph_image() -> bytes | None:
    return get_graph_image()


def load_graph_ascii() -> str:
    return get_graph_ascii()
