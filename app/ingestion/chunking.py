def create_chunks(transcript, chunk_duration=60):
    chunks = []

    current_text = []
    chunk_start = None
    chunk_end = None

    for item in transcript:

        if chunk_start is None:
            chunk_start = item.start

        current_text.append(item.text)
        chunk_end = item.start + item.duration

        # Create chunk when duration reaches the limit
        if chunk_end - chunk_start >= chunk_duration:

            chunks.append({
                "start": chunk_start,
                "end": chunk_end,
                "text": " ".join(current_text)
            })

            current_text = []
            chunk_start = None

    # Add remaining text
    if current_text:
        chunks.append({
            "start": chunk_start,
            "end": chunk_end,
            "text": " ".join(current_text)
        })

    return chunks