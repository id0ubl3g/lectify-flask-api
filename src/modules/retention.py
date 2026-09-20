from datetime import datetime, timedelta, timezone

DEFAULT_RETENTION_DAYS = 30

class Retention:
    def __init__(self, grid_fs, documents_collection, chunks_collection, plans: dict) -> None:
        self.grid_fs = grid_fs
        self.documents_collection = documents_collection
        self.chunks_collection = chunks_collection
        self.plans = plans

    def retention_days(self, plan: str | None) -> int:
        return self.plans.get(plan, {}).get("days", DEFAULT_RETENTION_DAYS)

    def expires_at(self, plan: str | None) -> datetime:
        return datetime.now(timezone.utc) + timedelta(days=self.retention_days(plan))

    def purge_expired(self) -> int:
        expired = self.documents_collection.find(
            {"expires_at": {"$lte": datetime.now(timezone.utc)}},
            {"_id": 1}
        )

        removed = 0

        for document in expired:
            self.grid_fs.delete(document["_id"])
            removed += 1

        return removed

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
            "orphan_chunks": self.purge_orphan_chunks()
        }
