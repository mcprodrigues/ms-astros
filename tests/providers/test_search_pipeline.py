def test_search_returns_matching_documents(container):
    container.indexing_pipeline.index_batch_documents(
        [
            {"doc_id": "a", "content": "sindicalismo rural em São Paulo", "metadata": {}},
            {"doc_id": "b", "content": "férias de família no México", "metadata": {}},
        ]
    )

    results = container.search_pipeline.search("sindicalismo", top_k=1)

    assert [doc.id for doc in results] == ["a"]
