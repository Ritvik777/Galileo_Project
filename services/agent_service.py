from agents import ask, get_graph_image


def ask_agent(question: str) -> dict:
    return ask(question)


def load_graph_image() -> bytes:
    return get_graph_image()
