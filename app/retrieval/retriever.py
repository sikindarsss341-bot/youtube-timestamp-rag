from sentence_transformers import SentenceTransformer
from app.retrieval.vector_store import client, COLLECTION_NAME


# Load embedding model
model = SentenceTransformer("all-MiniLM-L6-v2")


def search_chunks(query, top_k=3, score_threshold=0.30):

    # Convert question into embedding
    query_embedding = model.encode(query).tolist()

    # Search Qdrant
    results = client.query_points(
        collection_name=COLLECTION_NAME,
        query=query_embedding,
        limit=top_k,
        with_payload=True
    )

    # Keep only relevant results
    relevant_results = [
        result
        for result in results.points
        if result.score >= score_threshold
    ]

    return relevant_results


def get_neighbor_chunks(result, window=1):

    # Get video ID and chunk number
    video_id = result.payload["video_id"]
    chunk_index = result.payload["chunk_index"]

    # Get chunks belonging to this video
    all_chunks = client.scroll(
        collection_name=COLLECTION_NAME,
        scroll_filter={
            "must": [
                {
                    "key": "video_id",
                    "match": {
                        "value": video_id
                    }
                }
            ]
        },
        limit=100,
        with_payload=True
    )[0]

    neighbors = []

    # Select previous, current, and next chunks
    for chunk in all_chunks:

        index = chunk.payload["chunk_index"]

        if abs(index - chunk_index) <= window:
            neighbors.append(chunk)

    # Keep chunks in chronological order
    neighbors.sort(
        key=lambda x: x.payload["chunk_index"]
    )

    return neighbors