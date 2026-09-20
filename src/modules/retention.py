from datetime import datetime, timedelta, timezone

RETENTION_DAYS = 7

class Retention:
    def __init__(self, grid_fs, documents_collection, chunks_collection, questions_collection) -> None:
        self.grid_fs = grid_fs
        self.documents_collection = documents_collection
        self.chunks_collection = chunks_collection
        self.questions_collection = questions_collection

    def expires_at(self) -> datetime:
        return datetime.now(timezone.utc) + timedelta(days=RETENTION_DAYS)

    def delete_document(self, file_id) -> int:
        self.grid_fs.delete(file_id)

        return self.questions_collection.delete_many({"file_id": file_id}).deleted_count

    def purge_expired(self) -> int:
        expired = self.documents_collection.find(
            {"expires_at": {"$lte": datetime.now(timezone.utc)}},
            {"_id": 1}
        )

        removed = 0

        for document in expired:
            self.delete_document(document["_id"])
            removed += 1

        return removed

    def purge_expired_questions(self) -> int:
        return self.questions_collection.delete_many(
            {"expires_at": {"$lte": datetime.now(timezone.utc)}}
        ).deleted_count

    def purge_orphan_chunks(self, batch_size: int = 1000) -> int:
        pipeline = [
            {"$group": {"_id": "$files_id"}},
            {
                "$lookup": {
                    "from": self.documents_collection.name,
                    "localField": "_id",
                    "foreignField": "_id",
                    "as": "file"
                }
            },
            {"$match": {"file": {"$size": 0}}},
            {"$project": {"_id": 1}}
        ]

        removed = 0
        batch = []

        for document in self.chunks_collection.aggregate(pipeline, allowDiskUse=True):
            batch.append(document["_id"])

            if len(batch) >= batch_size:
                removed += self.chunks_collection.delete_many({"files_id": {"$in": batch}}).deleted_count
                batch = []

        if batch:
            removed += self.chunks_collection.delete_many({"files_id": {"$in": batch}}).deleted_count

        return removed

    def run(self) -> dict:
        return {
            "expired_files": self.purge_expired(),
            "expired_questions": self.purge_expired_questions(),
            "orphan_chunks": self.purge_orphan_chunks()
        }
