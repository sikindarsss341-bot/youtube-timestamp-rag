from app.retrieval.retriever import search_chunks


query = input("Ask a question: ")

results = search_chunks(query)


print("\n🔎 Relevant chunks:\n")

for i, result in enumerate(results, 1):

    print(f"--- Result {i} ---")
    print(f"Score: {result.score:.4f}")
    print(f"Start: {result.payload['start']:.2f}s")
    print(f"End: {result.payload['end']:.2f}s")
    print(f"Text: {result.payload['text']}")
    print()