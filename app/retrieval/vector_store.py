import os

from dotenv import load_dotenv
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct

load_dotenv()

QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")

COLLECTION_NAME = "youtube_chunks"

client = QdrantClient(
    url=QDRANT_URL,
    api_key=QDRANT_API_KEY,
    timeout=60
)


def create_collection():

    if not client.collection_exists(COLLECTION_NAME):

        client.create_collection(
            collection_name=COLLECTION_NAME,
            vectors_config=VectorParams(
                size=384,
                distance=Distance.COSINE
            )
        )

        print("✅ Collection created")

    else:
        print("✅ Collection already exists")


def create_payload_indexes():

    client.create_payload_index(
        collection_name=COLLECTION_NAME,
        field_name="video_id",
        field_schema="keyword"
    )

    print("✅ video_id index created")


def store_chunks(chunks, embeddings, video_id):

    points = []

    for i, (chunk, embedding) in enumerate(
        zip(chunks, embeddings)
    ):

        point = PointStruct(
            id=i,
            vector=embedding.tolist(),
            payload={
                "text": chunk["text"],
                "start": chunk["start"],
                "end": chunk["end"],
                "video_id": video_id,
                "chunk_index": i
            }
        )

        points.append(point)

    client.upsert(
        collection_name=COLLECTION_NAME,
        points=points
    )

    print(f"✅ Stored {len(points)} chunks in Qdrant")