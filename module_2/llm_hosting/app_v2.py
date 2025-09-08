# -*- coding: utf-8 -*-
"""Flask + tiny local LLM standardizer with incremental JSONL CLI output.
Optimized with caching + batching for faster throughput.
"""

from __future__ import annotations

import json
import os
import re
import sys
import difflib
from typing import Any, Dict, List, Tuple

from flask import Flask, jsonify, request
from huggingface_hub import hf_hub_download
from llama_cpp import Llama  # CPU-only by default if N_GPU_LAYERS=0

app = Flask(__name__)

# ---------------- Model config ----------------
MODEL_REPO = os.getenv("MODEL_REPO", "TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF")
MODEL_FILE = os.getenv("MODEL_FILE", "tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf")

N_THREADS = int(os.getenv("N_THREADS", str(os.cpu_count() or 2)))
N_CTX = int(os.getenv("N_CTX", "2048"))
N_GPU_LAYERS = int(os.getenv("N_GPU_LAYERS", "0"))  # 0 → CPU-only

CANON_UNIS_PATH = os.getenv("CANON_UNIS_PATH", "canon_universities.txt")
CANON_PROGS_PATH = os.getenv("CANON_PROGS_PATH", "canon_programs.txt")

# Precompiled JSON matcher
JSON_OBJ_RE = re.compile(r"\{.*?\}", re.DOTALL)

# ---------------- Canonical lists ----------------
def _read_lines(path: str) -> List[str]:
    try:
        with open(path, "r", encoding="utf-8") as f:
            return [ln.strip() for ln in f if ln.strip()]
    except FileNotFoundError:
        return []

CANON_UNIS = _read_lines(CANON_UNIS_PATH)
CANON_PROGS = _read_lines(CANON_PROGS_PATH)

# ---------------- Fixes & Maps ----------------
ABBREV_UNI: Dict[str, str] = {
    r"(?i)^mcg(\.|ill)?$": "McGill University",
    r"(?i)^(ubc|u\.?b\.?c\.?)$": "University of British Columbia",
    r"(?i)^uoft$": "University of Toronto",
}

COMMON_UNI_FIXES: Dict[str, str] = {
    "McGiill University": "McGill University",
    "Mcgill University": "McGill University",
    "University Of British Columbia": "University of British Columbia",
}

COMMON_PROG_FIXES: Dict[str, str] = {
    "Mathematic": "Mathematics",
    "Info Studies": "Information Studies",
}

# ---------------- Few-shot prompt ----------------
SYSTEM_PROMPT = (
    "You are a data cleaning assistant. Standardize degree program and university "
    "names.\n\n"
    "Rules:\n"
    "- Input provides a single string under key `program` that may contain both program and university.\n"
    "- Split into (program name, university name).\n"
    "- Trim extra spaces and commas.\n"
    "- Expand obvious abbreviations.\n"
    "- Use Title Case for program; use official capitalization for university names.\n"
    "- If university cannot be inferred, return \"Unknown\".\n\n"
    "Return JSON ONLY with keys:\n"
    "  standardized_program, standardized_university\n"
)

FEW_SHOTS: List[Tuple[Dict[str, str], Dict[str, str]]] = [
    (
        {"program": "Information Studies, McGill University"},
        {"standardized_program": "Information Studies", "standardized_university": "McGill University"},
    ),
    (
        {"program": "Information, McG"},
        {"standardized_program": "Information Studies", "standardized_university": "McGill University"},
    ),
    (
        {"program": "Mathematics, University Of British Columbia"},
        {"standardized_program": "Mathematics", "standardized_university": "University of British Columbia"},
    ),
]

_LLM: Llama | None = None
_CACHE: Dict[str, Dict[str, str]] = {}  # program_text -> result cache


def _load_llm() -> Llama:
    global _LLM
    if _LLM is not None:
        return _LLM
    model_path = hf_hub_download(
        repo_id=MODEL_REPO,
        filename=MODEL_FILE,
        local_dir="models",
        local_dir_use_symlinks=False,
        force_filename=MODEL_FILE,
    )
    _LLM = Llama(model_path=model_path, n_ctx=N_CTX, n_threads=N_THREADS, n_gpu_layers=N_GPU_LAYERS, verbose=False)
    return _LLM


def _split_fallback(text: str) -> Tuple[str, str]:
    s = re.sub(r"\s+", " ", (text or "")).strip().strip(",")
    parts = [p.strip() for p in re.split(r",| at | @ ", s) if p.strip()]
    prog = parts[0] if parts else ""
    uni = parts[1] if len(parts) > 1 else ""
    if re.fullmatch(r"(?i)mcg(ill)?(\.)?", uni or ""):
        uni = "McGill University"
    if re.fullmatch(r"(?i)(ubc|u\.?b\.?c\.?|university of british columbia)", uni or ""):
        uni = "University of British Columbia"
    prog = prog.title()
    if uni:
        uni = re.sub(r"\bOf\b", "of", uni.title())
    else:
        uni = "Unknown"
    return prog, uni


def _best_match(name: str, candidates: List[str], cutoff: float = 0.86) -> str | None:
    if not name or not candidates:
        return None
    matches = difflib.get_close_matches(name, candidates, n=1, cutoff=cutoff)
    return matches[0] if matches else None


def _post_normalize_program(prog: str) -> str:
    p = (prog or "").strip()
    p = COMMON_PROG_FIXES.get(p, p)
    p = p.title()
    if p in CANON_PROGS:
        return p
    match = _best_match(p, CANON_PROGS, cutoff=0.84)
    return match or p


def _post_normalize_university(uni: str) -> str:
    u = (uni or "").strip()
    for pat, full in ABBREV_UNI.items():
        if re.fullmatch(pat, u):
            u = full
            break
    u = COMMON_UNI_FIXES.get(u, u)
    if u:
        u = re.sub(r"\bOf\b", "of", u.title())
    if u in CANON_UNIS:
        return u
    match = _best_match(u, CANON_UNIS, cutoff=0.86)
    return match or u or "Unknown"


def _call_llm_batch(programs: List[str]) -> List[Dict[str, str]]:
    """Batch-call the LLM with multiple program strings."""
    llm = _load_llm()

    # Build messages with few-shots
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    for x_in, x_out in FEW_SHOTS:
        messages.append({"role": "user", "content": json.dumps(x_in)})
        messages.append({"role": "assistant", "content": json.dumps(x_out)})
    # Add batch input
    messages.append(
        {
            "role": "user",
            "content": json.dumps({"programs": programs}, ensure_ascii=False),
        }
    )

    out = llm.create_chat_completion(messages=messages, temperature=0.0, max_tokens=512, top_p=1.0)
    text = (out["choices"][0]["message"]["content"] or "").strip()

    results: List[Dict[str, str]] = []
    try:
        parsed = json.loads(text)
        # Expect list of objects
        if isinstance(parsed, list):
            results = parsed
        elif isinstance(parsed, dict) and "results" in parsed:
            results = parsed["results"]
    except Exception:
        # fallback: naive parsing
        for prog in programs:
            std_prog, std_uni = _split_fallback(prog)
            results.append({"standardized_program": std_prog, "standardized_university": std_uni})

    # Normalize
    out_norm = []
    for i, prog in enumerate(programs):
        if i < len(results):
            std_prog = _post_normalize_program(results[i].get("standardized_program", ""))
            std_uni = _post_normalize_university(results[i].get("standardized_university", ""))
        else:
            std_prog, std_uni = _split_fallback(prog)
        out_norm.append({"standardized_program": std_prog, "standardized_university": std_uni})
    return out_norm


def _normalize_input(payload: Any) -> List[Dict[str, Any]]:
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict) and isinstance(payload.get("rows"), list):
        return payload["rows"]
    return []


@app.get("/")
def health() -> Any:
    return jsonify({"ok": True})


@app.post("/standardize")
def standardize() -> Any:
    payload = request.get_json(force=True, silent=True)
    rows = _normalize_input(payload)

    out: List[Dict[str, Any]] = []
    for row in rows:
        program_text = (row or {}).get("program") or ""
        if program_text in _CACHE:
            result = _CACHE[program_text]
        else:
            result = _call_llm_batch([program_text])[0]
            _CACHE[program_text] = result
        row["llm-generated-program"] = result["standardized_program"]
        row["llm-generated-university"] = result["standardized_university"]
        out.append(row)
    return jsonify({"rows": out})


def _cli_process_file(in_path: str, out_path: str | None, append: bool, to_stdout: bool, batch_size: int = 20) -> None:
    with open(in_path, "r", encoding="utf-8") as f:
        rows = _normalize_input(json.load(f))

    sink = sys.stdout if to_stdout else None
    if not to_stdout:
        out_path = out_path or (in_path + ".jsonl")
        mode = "a" if append else "w"
        sink = open(out_path, mode, encoding="utf-8")

    assert sink is not None

    try:
        # Deduplicate first
        uniq_programs = list({(row or {}).get("program", "") for row in rows})
        to_process = [p for p in uniq_programs if p not in _CACHE]

        # Process in batches
        for i in range(0, len(to_process), batch_size):
            batch = to_process[i : i + batch_size]
            results = _call_llm_batch(batch)
            for prog, res in zip(batch, results):
                _CACHE[prog] = res

        # Write rows with cached results
        for row in rows:
            program_text = (row or {}).get("program") or ""
            result = _CACHE.get(program_text, {"standardized_program": "", "standardized_university": "Unknown"})
            row["llm-generated-program"] = result["standardized_program"]
            row["llm-generated-university"] = result["standardized_university"]
            json.dump(row, sink, ensure_ascii=False)
            sink.write("\n")
            sink.flush()
    finally:
        if sink is not sys.stdout:
            sink.close()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Standardize program/university with a tiny local LLM (batched + cached).")
    parser.add_argument("--file", help="Path to JSON input", default=None)
    parser.add_argument("--serve", action="store_true", help="Run HTTP server instead of CLI.")
    parser.add_argument("--out", default=None, help="Output path for JSONL.")
    parser.add_argument("--append", action="store_true", help="Append instead of overwrite.")
    parser.add_argument("--stdout", action="store_true", help="Write to stdout instead of file.")
    parser.add_argument("--batch-size", type=int, default=20, help="Batch size for LLM calls.")
    args = parser.parse_args()

    if args.serve or args.file is None:
        port = int(os.getenv("PORT", "8000"))
        app.run(host="0.0.0.0", port=port, debug=False)
    else:
        _cli_process_file(in_path=args.file, out_path=args.out, append=args.append, to_stdout=args.stdout, batch_size=args.batch_size)
