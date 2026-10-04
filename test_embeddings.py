from app.retrieval.embeddings import create_embeddings


texts = [
    "Machine learning learns patterns from data.",
    "RAG retrieves relevant information for an LLM."
]


embeddings = create_embeddings(texts)


print("Number of texts:", len(texts))
print("Number of embeddings:", len(embeddings))
print("Vector size:", len(embeddings[0]))
print("First vector:")
print(embeddings[0])