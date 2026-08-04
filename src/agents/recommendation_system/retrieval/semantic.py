
"""
Semantic retrieval: lets us find resources that are conceptually related to
what the learner needs, even if the exact words don't match.

HONEST NOTE: this uses a simplified "bag-of-words" vector instead of a real
neural embedding model. It's kept here as an automatic fallback in case the
real neural embedding model (embeddings.py) can't load.
"""

import math


def tokenize(text):
    """
    Breaks a piece of text into a list of individual lowercase words.

    Args:
        text (str): any piece of text.

    Returns:
        list: lowercase words.
    """
    return text.lower().split()


def build_word_vector(text):
    """
    Converts text into a "bag-of-words" vector: a dictionary mapping each
    word to how many times it appeared.

    Args:
        text (str): any piece of text.

    Returns:
        dict: {word: count, ...}
    """
    words = tokenize(text)
    vector = {}

    for word in words:
        vector[word] = vector.get(word, 0) + 1

    return vector


def dot_product(vector_a, vector_b):
    """
    Multiplies matching values from two vectors and adds up the results.
    Only words present in BOTH vectors contribute anything.

    Args:
        vector_a (dict): a word-count vector.
        vector_b (dict): another word-count vector.

    Returns:
        int: the dot product.
    """
    total = 0

    for word in vector_a:
        if word in vector_b:
            total += vector_a[word] * vector_b[word]

    return total


def magnitude(vector):
    """
    Calculates the "length" of a vector using the Pythagorean theorem:
    square every value, add them up, take the square root.

    Args:
        vector (dict): a word-count vector.

    Returns:
        float: the magnitude.
    """
    total = 0

    for word in vector:
        total += vector[word] ** 2

    return math.sqrt(total)


def cosine_similarity(text_a, text_b):
    """
    Measures how semantically similar two pieces of text are, from 0.0
    (nothing in common) to 1.0 (identical word usage).

    Args:
        text_a (str): first piece of text.
        text_b (str): second piece of text.

    Returns:
        float: similarity score, 0.0 to 1.0.
    """
    vector_a = build_word_vector(text_a)
    vector_b = build_word_vector(text_b)

    dot = dot_product(vector_a, vector_b)
    mag_a = magnitude(vector_a)
    mag_b = magnitude(vector_b)

    if mag_a == 0 or mag_b == 0:
        return 0.0

    return dot / (mag_a * mag_b)