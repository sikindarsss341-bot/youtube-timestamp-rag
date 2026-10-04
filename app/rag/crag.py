def evaluate_retrieval(results, threshold=0.30):

    if not results:
        return False

    best_score = max(result.score for result in results)

    return best_score >= threshold