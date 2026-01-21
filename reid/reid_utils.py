import numpy as np
from numpy.linalg import norm

def cosine_similarity(a, b):
    return np.dot(a, b) / (norm(a) * norm(b))


def match_embedding(new_emb, stored_embeddings, threshold=0.75):
    best_id = None
    best_score = -1

    for semantic_id, emb_list in stored_embeddings.items():
        for emb in emb_list:
            score = cosine_similarity(new_emb, emb)
            if score > best_score:
                best_score = score
                best_id = semantic_id

    if best_score >= threshold:
        return best_id, best_score

    return None, best_score
