import functools
import time
import os
import re

from typing import List, Tuple


@functools.lru_cache(maxsize=1)
def get_faculty_contacts_cached(ttl_seconds: int = 3600):
    """Fetch and cache (in-process) faculty contact lines from Selçuk link.
    Returns list[str]. Cache key is function only; TTL simulated by time bucket.
    """
    # Simple TTL invalidation by time bucket
    _ = int(time.time() // ttl_seconds)
    try:
        import requests
        from bs4 import BeautifulSoup
        url = 'https://tf.selcuk.edu.tr/index2.php?lang=tr&birim=033004&page=1642'
        html = requests.get(url, timeout=8).text
        soup = BeautifulSoup(html, 'html.parser')
        texts = []
        for a in soup.find_all('a'):
            mail = a.get('href') or ''
            if mail.startswith('mailto:'):
                email = mail.replace('mailto:', '')
                label = (a.text or '').strip() or email
                texts.append(f"İletişim: {label} - {email}")
        # Deduplicate and limit
        seen = set()
        unique = []
        for t in texts:
            if t not in seen:
                seen.add(t)
                unique.append(t)
        return unique[:20]
    except Exception:
        return []



# -------- FAQ Loader & Matcher --------
_FAQ_CACHE_KEY = "__faq_cache_bucket__"


@functools.lru_cache(maxsize=1)
def load_faq_items(ttl_seconds: int = 300) -> List[Tuple[str, str]]:
    """Load FAQ Q/A pairs from templates/users/faq.md.
    Returns list of (question, answer). Cached with a simple TTL bucket.
    """
    _ = int(time.time() // ttl_seconds)
    base_dir = os.path.dirname(os.path.dirname(__file__))  # project root approx: utils/ -> project
    # Find project root robustly (assumes manage.py at repo root)
    project_root = os.path.abspath(os.path.join(base_dir))
    faq_path = os.path.join(project_root, 'templates', 'users', 'faq.md')
    if not os.path.exists(faq_path):
        return []
    try:
        with open(faq_path, 'r', encoding='utf-8') as f:
            text = f.read()
        # Parse pairs by "Soru:" and "Cevap:" markers
        lines = [ln.strip() for ln in text.splitlines()]
        items: List[Tuple[str, str]] = []
        q = None
        a_lines: List[str] = []
        def flush():
            nonlocal q, a_lines
            if q and a_lines:
                items.append((q, " ".join(a_lines).strip()))
            q, a_lines = None, []
        for ln in lines:
            if ln.lower().startswith('soru:'):
                flush()
                q = ln.split(':', 1)[1].strip()
            elif ln.lower().startswith('cevap:'):
                a_lines.append(ln.split(':', 1)[1].strip())
            elif ln:
                # continuation lines for answer
                if q is not None:
                    a_lines.append(ln)
        flush()
        return items
    except Exception:
        return []


def answer_faq(query: str) -> str:
    """Very simple keyword-based matcher over loaded FAQ items.
    - Lowercases and strips Turkish diacritics approximately.
    - Scores by token overlap; returns best answer if score >= 1 token.
    """
    items = load_faq_items()
    if not items:
        return ''
    def normalize(s: str) -> str:
        s = s.lower()
        table = str.maketrans({
            'ç':'c','ğ':'g','ı':'i','ö':'o','ş':'s','ü':'u',
            'â':'a','î':'i','û':'u'
        })
        return re.sub(r"[^a-z0-9\s]", " ", s.translate(table))
    qn = normalize(query)
    q_tokens = set(t for t in qn.split() if len(t) > 2)
    best = ('', '', 0)
    for (q, a) in items:
        tn = normalize(q)
        tokens = set(t for t in tn.split() if len(t) > 2)
        score = len(q_tokens & tokens)
        if score > best[2]:
            best = (q, a, score)
    return best[1] if best[2] >= 1 else ''

