"""
Real neural embeddings, using a pretrained sentence-transformers model
instead of our own simplified word-counting.

HONEST NOTE: the first time this runs, it downloads about 80MB of model
weights from Hugging Face -- this needs a real internet connection. After
that first download, the model is cached on disk and loads instantly, even
offline. I could not fully test this myself in my own sandboxed environment
because it can't reach huggingface.co -- you're the one who gets to confirm
this actually works, on your own machine.

Install requirement (run this once in your terminal):
    pip install sentence-transformers
"""

from sentence_transformers import SentenceTransformer

_model = None


def get_model():
    """
    Loads the pretrained model the first time it's needed, and reuses that
    same loaded model on every later call (loading it is slow, so we only
    want to do it once).

    Returns:
        SentenceTransformer: the loaded model.
    """
    global _model

    if _model is None:
        _model = SentenceTransformer("all-MiniLM-L6-v2")

    return _model


def build_neural_vector(text):
    """
    Converts text into a real neural embedding vector.

    Args:
        text (str): any piece of text.

    Returns:
        dict: {"0": value, "1": value, ...} -- using the same dict shape as
              our bag-of-words vectors, so the exact same dot_product() and
              magnitude() functions from semantic.py work unchanged on it.
    """
    model = get_model()
    dense_vector = model.encode(text)

    return {str(index): float(value) for index, value in enumerate(dense_vector)}


def neural_cosine_similarity(text_a, text_b):
    """
    Cosine similarity using real neural embeddings instead of word counts.

    Args:
        text_a (str): first piece of text.
        text_b (str): second piece of text.

    Returns:
        float: similarity score, 0.0 to 1.0 (roughly -- neural embeddings
              can occasionally give small negative values for very
              unrelated text, which is normal).
    """
    from retrieval.semantic import dot_product, magnitude

    vector_a = build_neural_vector(text_a)
    vector_b = build_neural_vector(text_b)

    dot = dot_product(vector_a, vector_b)
    mag_a = magnitude(vector_a)
    mag_b = magnitude(vector_b)

    if mag_a == 0 or mag_b == 0:
        return 0.0

    return dot / (mag_a * mag_b)