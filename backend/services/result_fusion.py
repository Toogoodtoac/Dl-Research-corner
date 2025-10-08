"""
Result fusion service for combining search results from multiple models
Inspired by VISIONE's winning approach
"""

from typing import Any, Dict, List, Tuple

import structlog
from core.config import settings
from schemas.search import SearchResult

logger = structlog.get_logger()


class ResultFusionService:
    """
    Service for fusing and ranking search results from multiple models
    Implements various fusion strategies used in VISIONE
    """

    def __init__(self):
        self.fusion_methods = {
            "score": self._fuse_by_score,
            "rank": self._fuse_by_rank,
            "reciprocal_rank": self._fuse_by_reciprocal_rank,
            "weighted": self._fuse_by_weighted_score,
            "borda": self._fuse_by_borda_count,
        }

    def fuse_results(
        self,
        model_results: Dict[str, List[SearchResult]],
        limit: int,
        method: str = None,
    ) -> List[SearchResult]:
        """
        Fuse results from multiple models using the specified method

        Args:
            model_results: Dictionary mapping model names to their search results
            limit: Maximum number of results to return
            method: Fusion method to use

        Returns:
            Fused and ranked list of search results
        """
        if not model_results:
            return []

        if len(model_results) == 1:
            # Only one model, return its results
            return list(model_results.values())[0][:limit]

        # Use default method if none specified
        method = method or settings.FUSION_METHOD

        if method not in self.fusion_methods:
            logger.warning(f"Unknown fusion method {method}, using reciprocal_rank")
            method = "reciprocal_rank"

        logger.info(f"Fusing results using {method} method")

        # Apply fusion method
        fused_results = self.fusion_methods[method](model_results, limit)

        # Post-process results
        if settings.ENABLE_DUPLICATE_REMOVAL:
            fused_results = self._remove_duplicates(fused_results, limit)

        if settings.ENABLE_RESULT_SORTING:
            fused_results = self._sort_results(fused_results)

        return fused_results[:limit]

    def _fuse_by_score(
        self, model_results: Dict[str, List[SearchResult]], limit: int
    ) -> List[SearchResult]:
        """Fuse by taking the highest scores across all models"""
        all_results = []

        for model_name, results in model_results.items():
            for result in results:
                # Create a copy with model information
                fused_result = SearchResult(
                    image_id=result.image_id,
                    score=result.score,
                    link=result.link,
                    image_url=result.image_url,
                    watch_url=result.watch_url,
                    ocr_text=result.ocr_text,
                    bbox=result.bbox,
                    video_id=result.video_id,
                    shot_index=result.shot_index,
                    frame_stamp=result.frame_stamp,
                    file_path=result.file_path,
                )
                all_results.append(fused_result)

        # Sort by score and return top results
        return sorted(all_results, key=lambda x: x.score, reverse=True)[:limit]

    def _fuse_by_rank(
        self, model_results: Dict[str, List[SearchResult]], limit: int
    ) -> List[SearchResult]:
        """Fuse by rank position (lower rank = higher score)"""
        rank_scores = {}

        for model_name, results in model_results.items():
            for rank, result in enumerate(results):
                if result.link not in rank_scores:
                    rank_scores[result.link] = {
                        "result": result,
                        "ranks": [],
                        "models": [],
                    }

                rank_scores[result.link]["ranks"].append(rank + 1)
                rank_scores[result.link]["models"].append(model_name)

        # Calculate average rank for each result
        fused_results = []
        for link, data in rank_scores.items():
            avg_rank = sum(data["ranks"]) / len(data["ranks"])
            # Convert rank to score (lower rank = higher score)
            score = 1.0 / (avg_rank + 1)

            fused_result = SearchResult(
                image_id=data["result"].image_id,
                score=score,
                link=data["result"].link,
                image_url=data["result"].image_url,
                watch_url=data["result"].watch_url,
                ocr_text=data["result"].ocr_text,
                bbox=data["result"].bbox,
                video_id=data["result"].video_id,
                shot_index=data["result"].shot_index,
                frame_stamp=data["result"].frame_stamp,
                file_path=data["result"].file_path,
            )
            fused_results.append(fused_result)

        return sorted(fused_results, key=lambda x: x.score, reverse=True)[:limit]

    def _fuse_by_reciprocal_rank(
        self, model_results: Dict[str, List[SearchResult]], limit: int
    ) -> List[SearchResult]:
        """Fuse using reciprocal rank fusion (RRF) - VISIONE's preferred method"""
        rrf_scores = {}

        for model_name, results in model_results.items():
            for rank, result in enumerate(results):
                if result.link not in rrf_scores:
                    rrf_scores[result.link] = {
                        "result": result,
                        "rrf_score": 0.0,
                        "models": [],
                    }

                # RRF formula: 1 / (k + rank)
                k = 60  # VISIONE uses k=60
                rrf_score = 1.0 / (k + rank + 1)
                rrf_scores[result.link]["rrf_score"] += rrf_score
                rrf_scores[result.link]["models"].append(model_name)

        # Create fused results
        fused_results = []
        for link, data in rrf_scores.items():
            fused_result = SearchResult(
                image_id=data["result"].image_id,
                score=data["rrf_score"],
                link=data["result"].link,
                image_url=data["result"].image_url,
                watch_url=data["result"].watch_url,
                ocr_text=data["result"].ocr_text,
                bbox=data["result"].bbox,
                video_id=data["result"].video_id,
                shot_index=data["result"].shot_index,
                frame_stamp=data["result"].frame_stamp,
                file_path=data["result"].file_path,
            )
            fused_results.append(fused_result)

        return sorted(fused_results, key=lambda x: x.score, reverse=True)[:limit]

    def _fuse_by_weighted_score(
        self, model_results: Dict[str, List[SearchResult]], limit: int
    ) -> List[SearchResult]:
        """Fuse using weighted scores based on model priorities"""
        weighted_scores = {}

        for model_name, results in model_results.items():
            # Get model priority (higher number = higher priority)
            priority = settings.MODEL_PRIORITIES.get(model_name, 1)
            weight = priority / sum(settings.MODEL_PRIORITIES.values())

            for result in results:
                if result.link not in weighted_scores:
                    weighted_scores[result.link] = {
                        "result": result,
                        "weighted_score": 0.0,
                        "models": [],
                    }

                weighted_scores[result.link]["weighted_score"] += result.score * weight
                weighted_scores[result.link]["models"].append(model_name)

        # Create fused results
        fused_results = []
        for link, data in weighted_scores.items():
            fused_result = SearchResult(
                image_id=data["result"].image_id,
                score=data["weighted_score"],
                link=data["result"].link,
                image_url=data["result"].image_url,
                watch_url=data["result"].watch_url,
                ocr_text=data["result"].ocr_text,
                bbox=data["result"].bbox,
                video_id=data["result"].video_id,
                shot_index=data["result"].shot_index,
                frame_stamp=data["result"].frame_stamp,
                file_path=data["result"].file_path,
            )
            fused_results.append(fused_result)

        return sorted(fused_results, key=lambda x: x.score, reverse=True)[:limit]

    def _fuse_by_borda_count(
        self, model_results: Dict[str, List[SearchResult]], limit: int
    ) -> List[SearchResult]:
        """Fuse using Borda count method"""
        borda_scores = {}

        for model_name, results in model_results.items():
            max_rank = len(results)
            for rank, result in enumerate(results):
                if result.link not in borda_scores:
                    borda_scores[result.link] = {
                        "result": result,
                        "borda_score": 0,
                        "models": [],
                    }

                # Borda count: (max_rank - rank) points
                borda_points = max_rank - rank
                borda_scores[result.link]["borda_score"] += borda_points
                borda_scores[result.link]["models"].append(model_name)

        # Create fused results
        fused_results = []
        for link, data in borda_scores.items():
            fused_result = SearchResult(
                image_id=data["result"].image_id,
                score=float(data["borda_score"]),
                link=data["result"].link,
                image_url=data["result"].image_url,
                watch_url=data["result"].watch_url,
                ocr_text=data["result"].ocr_text,
                bbox=data["result"].bbox,
                video_id=data["result"].video_id,
                shot_index=data["result"].shot_index,
                frame_stamp=data["result"].frame_stamp,
                file_path=data["result"].file_path,
            )
            fused_results.append(fused_result)

        return sorted(fused_results, key=lambda x: x.score, reverse=True)[:limit]

    def _remove_duplicates(
        self, results: List[SearchResult], limit: int
    ) -> List[SearchResult]:
        """Remove duplicate results based on image path"""
        seen_paths = set()
        unique_results = []

        for result in results:
            if result.link not in seen_paths:
                seen_paths.add(result.link)
                unique_results.append(result)
                if len(unique_results) >= limit:
                    break

        return unique_results

    def _sort_results(self, results: List[SearchResult]) -> List[SearchResult]:
        """Sort results by score (highest first)"""
        if settings.SORT_BY_SCORE:
            return sorted(results, key=lambda x: x.score, reverse=True)
        return results

    def get_fusion_stats(
        self, model_results: Dict[str, List[SearchResult]]
    ) -> Dict[str, Any]:
        """Get statistics about the fusion process"""
        stats = {
            "total_models": len(model_results),
            "total_results": sum(len(results) for results in model_results.values()),
            "model_breakdown": {},
        }

        for model_name, results in model_results.items():
            stats["model_breakdown"][model_name] = {
                "result_count": len(results),
                "avg_score": (
                    sum(r.score for r in results) / len(results) if results else 0.0
                ),
                "min_score": min(r.score for r in results) if results else 0.0,
                "max_score": max(r.score for r in results) if results else 0.0,
            }

        return stats
