"""Optional local embedding index. Never imports model dependencies in BM25-only mode."""
import os
from functools import lru_cache

@lru_cache(maxsize=2)
def _load_model(model_name):
    from sentence_transformers import SentenceTransformer
    return SentenceTransformer(model_name)

class SemanticIndex:
    def __init__(self, texts):
        self.ready = False
        self.error = ''
        if os.getenv('FAST_ENABLE_SEMANTIC', '1').lower() in ('0', 'false', 'off'):
            self.error = 'Disabled by FAST_ENABLE_SEMANTIC'
            return
        try:
            import numpy as np
            model_name = os.getenv('FAST_EMBEDDING_MODEL', 'sentence-transformers/all-MiniLM-L6-v2')
            self.model = _load_model(model_name)
            self.vectors = np.asarray(self.model.encode(texts, normalize_embeddings=True, show_progress_bar=False), dtype='float32')
            self.ready = True
        except (ImportError, OSError, RuntimeError, ValueError) as exc:
            self.error = f'{type(exc).__name__}: {exc}'

    def rank(self, query):
        if not self.ready:
            return []
        import numpy as np
        try:
            vector = np.asarray(self.model.encode([query], normalize_embeddings=True, show_progress_bar=False)[0], dtype='float32')
        except (RuntimeError, ValueError, OSError) as exc:
            self.error = f'Inference failed: {type(exc).__name__}: {exc}'
            self.ready = False
            return []
        scores = self.vectors @ vector
        return [(float(scores[i]), int(i)) for i in np.argsort(-scores)]
