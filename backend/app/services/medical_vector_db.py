"""
Medical Vector Database Service using pgvector
Handles storage and similarity search of medical situation embeddings
"""

import json
import uuid
import logging
import numpy as np
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

logger = logging.getLogger(__name__)


class MedicalVectorDatabase:
    """
    Vector database for medical situations using pgvector
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.similarity_threshold = 0.85
        self.max_search_results = 5

    async def store_medical_situation(
        self,
        embedding: np.ndarray,
        medical_context: Dict[str, Any],
        analysis_result: Dict[str, Any],
        confidence_score: float = 0.9,
    ) -> str:
        """
        Store a medical situation with its embedding and analysis using pgvector
        """
        try:
            situation_id = str(uuid.uuid4())

            # Convert numpy array to list for pgvector
            embedding_list = embedding.tolist()

            # Anonymize medical context (remove user-specific info)
            anonymized_context = self._anonymize_medical_context(medical_context)

            # Store in database using pgvector
            await self.db.execute(
                text(
                    """
                    INSERT INTO medical_situations 
                    (id, embedding, medical_context, analysis_result, confidence_score, created_at, last_used_at)
                    VALUES (:id, :embedding::vector, :context, :analysis, :confidence, NOW(), NOW())
                """
                ),
                {
                    "id": situation_id,
                    "embedding": str(embedding_list),
                    "context": json.dumps(anonymized_context),
                    "analysis": json.dumps(analysis_result),
                    "confidence": confidence_score,
                },
            )

            await self.db.commit()

            logger.info(f"Stored medical situation: {situation_id}")
            return situation_id

        except Exception as e:
            logger.error(f"Failed to store medical situation: {str(e)}")
            await self.db.rollback()
            raise

    async def search_similar_situations(
        self, query_embedding: np.ndarray, limit: int = 5, min_confidence: float = 0.8
    ) -> List[Dict[str, Any]]:
        """
        Search for similar medical situations using pgvector cosine similarity
        """
        try:
            # Convert query embedding to list for pgvector
            query_list = query_embedding.tolist()

            # Use pgvector's cosine similarity operator for fast search
            result = await self.db.execute(
                text(
                    """
                    SELECT 
                        id,
                        medical_context,
                        analysis_result,
                        confidence_score,
                        usage_count,
                        created_at,
                        1 - (embedding <=> :query_embedding::vector) as similarity_score
                    FROM medical_situations 
                    WHERE confidence_score >= :min_confidence
                        AND 1 - (embedding <=> :query_embedding::vector) >= :threshold
                    ORDER BY embedding <=> :query_embedding::vector
                    LIMIT :limit
                """
                ),
                {
                    "query_embedding": str(query_list),
                    "min_confidence": min_confidence,
                    "threshold": self.similarity_threshold,
                    "limit": limit,
                },
            )
            result = result.fetchall()

            # Format results
            similar_situations = []
            for row in result:
                situation = {
                    "id": row[0],
                    "medical_context": json.loads(row[1]) if row[1] else {},
                    "analysis_result": json.loads(row[2]) if row[2] else {},
                    "confidence_score": row[3],
                    "usage_count": row[4],
                    "similarity_score": float(row[6]) if row[6] else 0.0,
                    "created_at": row[5],
                }
                similar_situations.append(situation)

            logger.info(f"Found {len(similar_situations)} similar medical situations")
            return similar_situations

        except Exception as e:
            logger.error(f"Failed to search similar situations: {str(e)}")
            return []

    async def update_usage_count(self, situation_id: str):
        """
        Increment usage count when a situation is reused
        """
        try:
            await self.db.execute(
                text(
                    """
                    UPDATE medical_situations 
                    SET usage_count = usage_count + 1, last_used_at = NOW()
                    WHERE id = :id
                """
                ),
                {"id": situation_id},
            )
            await self.db.commit()

        except Exception as e:
            logger.error(f"Failed to update usage count: {str(e)}")

    async def get_embedding_by_id(self, situation_id: str) -> Optional[np.ndarray]:
        """
        Retrieve embedding vector by situation ID
        """
        try:
            result = await self.db.execute(
                text("SELECT embedding FROM medical_situations WHERE id = :id"),
                {"id": situation_id},
            )
            result = result.fetchone()

            if result and result[0]:
                # pgvector returns the embedding as a string, parse it back to array
                embedding_str = result[0]
                # Remove brackets and split by comma
                embedding_list = [
                    float(x) for x in embedding_str.strip("[]").split(",")
                ]
                return np.array(embedding_list)

            return None

        except Exception as e:
            logger.error(f"Failed to get embedding: {str(e)}")
            return None

    async def cleanup_old_situations(self, days_old: int = 90):
        """
        Clean up old, unused medical situations
        """
        try:
            cutoff_date = datetime.now() - timedelta(days=days_old)

            result = await self.db.execute(
                text(
                    """
                    DELETE FROM medical_situations 
                    WHERE last_used_at < :cutoff_date 
                    AND usage_count <= 2
                """
                ),
                {"cutoff_date": cutoff_date},
            )

            deleted_count = result.rowcount
            await self.db.commit()

            logger.info(f"Cleaned up {deleted_count} old medical situations")
            return deleted_count

        except Exception as e:
            logger.error(f"Failed to cleanup old situations: {str(e)}")
            return 0

    def _anonymize_medical_context(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Remove personally identifiable information from medical context
        """
        anonymized = context.copy()

        # Remove user-specific identifiers
        anonymized.pop("user_id", None)
        anonymized.pop("user_name", None)
        anonymized.pop("email", None)

        # Keep only medical data patterns
        safe_fields = [
            "medications",
            "symptoms",
            "health_conditions",
            "lab_results",
            "medical_categories",
        ]

        # Filter to only include safe medical data
        filtered_context = {}
        for field in safe_fields:
            if field in anonymized:
                filtered_context[field] = anonymized[field]

        return filtered_context

    async def get_database_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the medical situations database
        """
        try:
            result = await self.db.execute(
                text(
                    """
                    SELECT 
                        COUNT(*) as total_situations,
                        AVG(confidence_score) as avg_confidence,
                        AVG(usage_count) as avg_usage,
                        MAX(last_used_at) as last_activity,
                        COUNT(CASE WHEN created_at >= NOW() - INTERVAL '7 days' THEN 1 END) as recent_additions
                    FROM medical_situations
                """
                )
            )
            result = result.fetchone()

            if result:
                return {
                    "total_situations": result[0],
                    "average_confidence": float(result[1]) if result[1] else 0.0,
                    "average_usage": float(result[2]) if result[2] else 0.0,
                    "last_activity": result[3],
                    "recent_additions": result[4],
                }

            return {}

        except Exception as e:
            logger.error(f"Failed to get database stats: {str(e)}")
            return {}


class SimplifiedVectorSearch:
    """
    Simplified vector search using pgvector for fast similarity queries
    """

    def __init__(self, db: AsyncSession):
        self.db = db
        self.similarity_threshold = 0.85
        # No need for in-memory cache with pgvector - it's fast enough

    async def find_similar_situations(
        self, query_embedding: np.ndarray, medical_context: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """
        Fast similarity search using pgvector
        """
        try:
            query_list = query_embedding.tolist()

            # Use pgvector for fast similarity search
            result = await self.db.execute(
                text(
                    """
                    SELECT 
                        id,
                        medical_context,
                        analysis_result,
                        confidence_score,
                        1 - (embedding <=> :query_embedding::vector) as similarity_score
                    FROM medical_situations 
                    WHERE confidence_score >= 0.8
                        AND 1 - (embedding <=> :query_embedding::vector) >= :threshold
                    ORDER BY embedding <=> :query_embedding::vector
                    LIMIT 5
                """
                ),
                {
                    "query_embedding": str(query_list),
                    "threshold": self.similarity_threshold,
                },
            )
            result = result.fetchall()

            # Format results
            similarities = []
            for row in result:
                result_data = {
                    "situation_id": row[0],
                    "medical_context": json.loads(row[1]) if row[1] else {},
                    "analysis_result": json.loads(row[2]) if row[2] else {},
                    "confidence_score": row[3],
                    "similarity_score": float(row[4]) if row[4] else 0.0,
                }
                similarities.append(result_data)

            logger.info(f"Found {len(similarities)} similar situations using pgvector")
            return similarities

        except Exception as e:
            logger.error(f"pgvector similarity search failed: {str(e)}")
            return []
