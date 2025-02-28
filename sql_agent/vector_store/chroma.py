from typing import Any, List

import chromadb
from overrides import override

from sql_agent.config import System
from sql_agent.vector_store import VectorStore


class Chroma(VectorStore):
    def __init__(
            self,
            system: System
    ):
        super().__init__(system)
        self.chroma_client = chromadb.PersistentClient(path=system.settings.persist_directory)

    @override
    def query(
            self,
            query_texts: List[str],
            db_connection_id: str,
            collection: str,
            num_results: int,
    ) -> list:
        try:
            target_collection = self.chroma_client.get_collection(collection)
        except ValueError:
            return []

        query_results = target_collection.query(
            query_texts=query_texts,
            n_results=num_results,
            where={"db_connection_id": db_connection_id},
        )
        return self.convert_to_pinecone_object_model(query_results)

    @override
    def add_record(
            self,
            documents: str,
            db_connection_id: str,  # noqa: ARG002
            collection: str,
            metadata: Any,
            ids: List[str] = None,
    ):
        target_collection = self.chroma_client.get_or_create_collection(collection)
        existing_rows = target_collection.get(ids=ids)
        if len(existing_rows["documents"]) == 0:
            target_collection.add(documents=documents, metadatas=metadata, ids=ids)

    @override
    def delete_record(self, collection: str, id: str):
        target_collection = self.chroma_client.get_or_create_collection(collection)
        target_collection.delete(ids=[id])

    @override
    def delete_collection(self, collection: str):
        return super().delete_collection(collection)

    @override
    def create_collection(self, collection: str):
        return super().create_collection(collection)

    def convert_to_pinecone_object_model(self, chroma_results: dict) -> List:
        results = []
        for i in range(len(chroma_results["ids"][0])):
            results.append(
                {
                    "id": chroma_results["ids"][0][i],
                    "score": chroma_results["distances"][0][i],
                }
            )
        return results
