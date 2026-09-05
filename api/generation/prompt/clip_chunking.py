import torch

_CHUNK_SIZE = 75


def needs_chunking(tokenizer, text: str) -> bool:
    token_count = len(tokenizer(text, add_special_tokens=False)["input_ids"])
    return token_count > _CHUNK_SIZE


def supports_chunking(pipeline) -> bool:
    """True only when every text encoder the pipeline has is CLIP-family (e.g.
    SD/SDXL) — i.e. CLIP's hidden states are genuinely what feeds cross-attention.
    A pipeline that pairs CLIP with a non-CLIP encoder (e.g. FLUX's CLIP + T5) uses
    CLIP only for a pooled/global vector while the other encoder carries the actual
    per-token content, so chunking CLIP there wouldn't recover anything and would
    silently drop the real (already-long-context) conditioning instead.
    """
    text_encoder = getattr(pipeline, "text_encoder", None)
    if getattr(pipeline, "tokenizer", None) is None or text_encoder is None:
        return False
    if "CLIP" not in type(text_encoder).__name__:
        return False

    text_encoder_2 = getattr(pipeline, "text_encoder_2", None)
    if text_encoder_2 is not None and "CLIP" not in type(text_encoder_2).__name__:
        return False

    return True


def build_long_prompt_embeds(pipeline, prompt: str, negative_prompt: str | None) -> dict:
    """Bypasses CLIP's 77-token limit by tokenizing the full prompt without
    truncation, splitting it into <=75-token chunks (leaving room for BOS/EOS),
    encoding each chunk separately, and concatenating the resulting per-token
    hidden states along the sequence dimension. This is only valid because CLIP's
    contribution to cross-attention is a per-token sequence — for encoders whose
    output is a single pooled/global vector (e.g. FLUX's CLIP path), extending
    length this way has no equivalent, so this only applies to CLIP text encoders
    used as the (or a) primary sequence encoder, e.g. SD/SDXL-family pipelines.

    SDXL's second encoder is also the source of the pooled embedding, so when
    tokenizer_2/text_encoder_2 are present, their first chunk's pooled output is
    used as pooled_prompt_embeds/negative_pooled_prompt_embeds — chunking has no
    bearing on the pooled vector itself, only on the per-token sequence.
    """
    negative_prompt = negative_prompt or ""
    device = pipeline._execution_device
    num_chunks = max(
        _chunk_count(pipeline.tokenizer, prompt),
        _chunk_count(pipeline.tokenizer, negative_prompt),
        1,
    )

    prompt_embeds, pooled_prompt_embeds = _encode(pipeline.tokenizer, pipeline.text_encoder, prompt, num_chunks, device)
    negative_prompt_embeds, negative_pooled_embeds = _encode(
        pipeline.tokenizer, pipeline.text_encoder, negative_prompt, num_chunks, device
    )

    result = {"prompt_embeds": prompt_embeds, "negative_prompt_embeds": negative_prompt_embeds}

    tokenizer_2 = getattr(pipeline, "tokenizer_2", None)
    text_encoder_2 = getattr(pipeline, "text_encoder_2", None)
    if tokenizer_2 is not None and text_encoder_2 is not None:
        prompt_embeds_2, pooled_prompt_embeds = _encode(tokenizer_2, text_encoder_2, prompt, num_chunks, device)
        negative_prompt_embeds_2, negative_pooled_embeds = _encode(
            tokenizer_2, text_encoder_2, negative_prompt, num_chunks, device
        )
        result["prompt_embeds"] = torch.cat([result["prompt_embeds"], prompt_embeds_2], dim=-1)
        result["negative_prompt_embeds"] = torch.cat([result["negative_prompt_embeds"], negative_prompt_embeds_2], dim=-1)

    if pooled_prompt_embeds is not None:
        result["pooled_prompt_embeds"] = pooled_prompt_embeds
        result["negative_pooled_prompt_embeds"] = negative_pooled_embeds

    return result


def _chunk_count(tokenizer, text: str) -> int:
    return len(_token_chunks(tokenizer, text))


def _token_chunks(tokenizer, text: str) -> list[list[int]]:
    ids = tokenizer(text, truncation=False, add_special_tokens=False)["input_ids"]
    chunks = [ids[i : i + _CHUNK_SIZE] for i in range(0, len(ids), _CHUNK_SIZE)]
    return chunks or [[]]


def _encode(tokenizer, text_encoder, text: str, num_chunks: int, device) -> tuple[torch.Tensor, torch.Tensor | None]:
    chunks = _token_chunks(tokenizer, text)
    chunks += [[]] * (num_chunks - len(chunks))

    bos = tokenizer.bos_token_id
    eos = tokenizer.eos_token_id
    pad = tokenizer.pad_token_id if tokenizer.pad_token_id is not None else eos
    max_length = tokenizer.model_max_length

    input_ids = []
    for chunk in chunks:
        ids = [bos, *chunk, eos]
        ids += [pad] * (max_length - len(ids))
        input_ids.append(ids[:max_length])

    output = text_encoder(torch.tensor(input_ids, device=device), output_hidden_states=True)
    hidden_states = output.hidden_states[-2]
    sequence_embeds = hidden_states.reshape(1, -1, hidden_states.shape[-1])

    pooled = getattr(output, "text_embeds", None)
    if pooled is None:
        pooled = getattr(output, "pooler_output", None)
    pooled_embeds = pooled[:1] if pooled is not None else None

    return sequence_embeds, pooled_embeds
