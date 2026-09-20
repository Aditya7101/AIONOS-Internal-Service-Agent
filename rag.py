import os
import re


KNOWLEDGE_BASE_PATH = os.path.join(
    os.path.dirname(__file__),
    "knowledge_base",
    "policies.txt"
)


def load_knowledge_base():
    """Load the Veridian IT support knowledge base."""
    try:
        with open(KNOWLEDGE_BASE_PATH, "r", encoding="utf-8") as file:
            return file.read()
    except FileNotFoundError:
        return ""


def search_knowledge_base(query):
    """
    Simple keyword-based retrieval.
    Returns the most relevant policy sections.
    """

    knowledge = load_knowledge_base()

    if not knowledge:
        return "No knowledge base information is available."

    sections = re.split(r"\n(?=KB-\d+ |ASSET MANAGEMENT POLICY)", knowledge)

    query_words = set(
        word.lower()
        for word in re.findall(r"\b[a-zA-Z0-9]+\b", query)
        if len(word) > 2
    )

    scored_sections = []

    for section in sections:
        section_words = set(
            word.lower()
            for word in re.findall(r"\b[a-zA-Z0-9]+\b", section)
        )

        score = len(query_words.intersection(section_words))

        if score > 0:
            scored_sections.append((score, section.strip()))

    scored_sections.sort(reverse=True, key=lambda item: item[0])

    if not scored_sections:
        return knowledge

    top_sections = scored_sections[:3]

    return "\n\n".join(section for _, section in top_sections)