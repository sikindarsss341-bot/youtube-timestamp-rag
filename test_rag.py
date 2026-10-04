from app.retrieval.retriever import search_chunks, get_neighbor_chunks
from app.rag.generator import generate_answer
from app.rag.crag import evaluate_retrieval


question = input("Ask a question: ")

results = search_chunks(question)


if not evaluate_retrieval(results):

    print("\n❌ Retrieved information is not relevant enough.")

else:

    all_context = []

    for result in results:

        neighbors = get_neighbor_chunks(
            result,
            window=1
        )

        for chunk in neighbors:
            all_context.append(chunk)


    unique_chunks = {
        chunk.id: chunk
        for chunk in all_context
    }

    context_chunks = list(unique_chunks.values())

    context_chunks.sort(
        key=lambda x: x.payload["chunk_index"]
    )

    context = "\n\n".join(
        chunk.payload["text"]
        for chunk in context_chunks
    )


    answer = generate_answer(
        question,
        context
    )

    print("\n🤖 Answer:")
    print(answer)

    print("\n🕐 Sources:")

    for result in results:

        start = result.payload["start"]

        minutes = int(start // 60)
        seconds = int(start % 60)

        print(f"▶ {minutes}:{seconds:02d}")