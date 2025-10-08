"""
Search service for text, image, and visual search
"""

import asyncio
import os
import sys
from typing import List, Optional, Union

import structlog
from core.config import settings
from schemas.common import ModelType, SearchLogic, SearchResult

# Add parent directory to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), "..", ".."))
# Add utils directory to path for FAISS processing
utils_dir = os.path.join(os.path.dirname(__file__), "..", "utils")
if utils_dir not in sys.path:
    sys.path.append(utils_dir)

logger = structlog.get_logger()


class SearchService:
    """Search service integrating with FAISS processing"""

    def __init__(self):
        self._faiss_engine = None
        self._models_loaded = False
        self._loading_lock = asyncio.Lock()

        logger.info("SearchService initialized")

    async def _ensure_models_loaded(self):
        """Ensure FAISS engine and models are loaded"""
        if self._models_loaded:
            return

        async with self._loading_lock:
            if self._models_loaded:
                return

            logger.info("Loading search models...")

            try:
                # Import and initialize the FAISS engine
                from utils.faiss_processing_beit3 import MyFaiss

                # Check if required directories exist
                checkpoint_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "checkpoints"))
                dict_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "dict"))
                
                logger.info(f"Checking FAISS paths:")
                logger.info(f"  Working directory: {os.getcwd()}")
                logger.info(f"  Checkpoint directory: {checkpoint_dir}")
                logger.info(f"  Dict directory: {dict_dir}")
                logger.info(f"  Checkpoint dir exists: {os.path.exists(checkpoint_dir)}")
                logger.info(f"  Dict dir exists: {os.path.exists(dict_dir)}")

                if not os.path.exists(checkpoint_dir) or not os.path.exists(dict_dir):
                    logger.warning("Required directories not found, using mock mode")
                    self._faiss_engine = None
                else:
                    # Initialize the FAISS engine with available models
                    try:
                        self._faiss_engine = MyFaiss(
                            checkpoint_dir=checkpoint_dir,
                            dict_dir=dict_dir,
                        )

                        # Initialize metadata service
                        from services.metadata_service import metadata_service

                        await metadata_service.initialize()
                        self._metadata_service = metadata_service

                        logger.info(
                            "FAISS engine and metadata service initialized successfully"
                        )

                    except Exception as e:
                        logger.error(f"Failed to initialize FAISS engine: {e}")
                        self._faiss_engine = None

                self._models_loaded = True

            except Exception as e:
                logger.error(f"Failed to load search models: {e}")
                self._models_loaded = False

    async def text_search(
        self, query: str, model_type: ModelType = ModelType.CLIP, limit: int = 20
    ) -> List[SearchResult]:
        """Perform text-based search"""
        await self._ensure_models_loaded()

        logger.info(
            f"🔍 text_search called with query='{query}', model_type={model_type.value}, limit={limit}"
        )
        logger.info(
            f"🔍 _faiss_engine={self._faiss_engine is not None}, _models_loaded={self._models_loaded}"
        )

        if self._faiss_engine is None:
            logger.warning("🔍 FAISS engine is None, returning mock results")
            return self._mock_search_results(limit, "text", query)

        try:
            if model_type == ModelType.ALL:
                logger.info("🔍 Using multi-model search (ALL)")
                # Search across all available models and combine results
                return await self._search_all_models(query, limit)
            else:
                logger.info(f"🔍 Using single model search: {model_type.value}")
                # Use the specified model
                logger.info(f"🔍 Calling FAISS engine.text_search with: text='{query}', k={limit}, model_type='{model_type.value}'")
                logger.info(f"🔍 Model type enum: {model_type}, value: {model_type.value}")
                scores, idxs, image_paths = self._faiss_engine.text_search(
                    text=query, k=limit, model_type=model_type.value
                )
                logger.info(f"🔍 FAISS search returned: scores={len(scores)}, idxs={len(idxs)}, paths={len(image_paths)}")
                logger.info(f"🔍 Scores type: {type(scores)}, shape: {scores.shape if hasattr(scores, 'shape') else 'N/A'}")
                logger.info(f"🔍 Idxs type: {type(idxs)}, shape: {idxs.shape if hasattr(idxs, 'shape') else 'N/A'}")
                logger.info(f"🔍 Paths type: {type(image_paths)}, length: {len(image_paths) if image_paths else 'N/A'}")
                if image_paths:
                    logger.info(f"🔍 First few paths: {image_paths[:3]}")
                else:
                    logger.warning("🔍 No image paths returned from FAISS!")

                results = []
                # Set similarity threshold to filter out poor matches
                # For CLIP models, scores above 0.2 are usually good matches (lowered from 0.3)
                # For LongCLIP, scores above 1.0 are usually good matches (lowered to include L batches)
                # For BEiT3, scores above 0.4 are usually good matches (lowered from 0.5)
                if model_type in [ModelType.LONGCLIP, ModelType.CLIP2VIDEO]:
                    similarity_threshold = 1.0
                elif model_type == ModelType.BEIT3:
                    similarity_threshold = 0.4
                else:
                    similarity_threshold = 0.2
                
                logger.info(f"🔍 Processing {len(scores)} search results with threshold {similarity_threshold}...")
                for i, (score, idx, path) in enumerate(zip(scores, idxs, image_paths)):
                    if path and score >= similarity_threshold:
                        # Create proper image URL for frontend display
                        # The path from id2img.json is already in the format "raw/keyframes/Keyframes_L21/keyframes/L21_V001/001.jpg"
                        # So we just need to prepend "/data/" to make it accessible via the static file mount
                        image_url = f"/data/{path}"

                        # Extract folder and filename from the path
                        # Path format: "raw/keyframes/Keyframes_L21/keyframes/L21_V001/001.jpg"
                        # We want to extract: "L21_V001/001.jpg"
                        file_path = None
                        if path:
                            path_parts = path.split("/")
                            if len(path_parts) >= 3:
                                # Get the last two parts: folder and filename
                                file_path = f"{path_parts[-2]}/{path_parts[-1]}"

                        result = SearchResult(
                            image_id=f"{model_type.value}_{idx}",
                            score=float(score),
                            link=path,
                            image_url=image_url,
                            watch_url=None,
                            ocr_text=None,
                            file_path=file_path,
                        )
                        results.append(result)
                        if i < 3:  # Log first 3 results for debugging
                            logger.info(f"🔍 Result {i+1}: score={score:.4f}, path={path}, file_path={file_path}")
                
                logger.info(f"🔍 Created {len(results)} valid results from {len(scores)} raw results (threshold: {similarity_threshold})")

                # If no results meet the threshold, return a message
                if not results:
                    logger.warning(f"🔍 No results met similarity threshold {similarity_threshold}. Dataset may not contain relevant content.")
                    return []

                # Remove duplicates and return results
                unique_results = self._remove_duplicates(results, limit)
                logger.info(f"🔍 After deduplication: {len(unique_results)} unique results")

                # Enhance results with metadata
                enhanced_results = await self._enhance_results_with_metadata(
                    unique_results
                )
                logger.info(f"🔍 Final enhanced results: {len(enhanced_results)} results")

                return enhanced_results

        except ValueError as e:
            if "not available" in str(e).lower():
                logger.error(f"🔍 Model {model_type.value} not available: {e}")
                # Return empty results instead of mock results when model is not available
                return []
            else:
                logger.error(f"🔍 Text search failed with ValueError: {e}")
                return self._mock_search_results(limit, "text", query)
        except Exception as e:
            logger.error(f"🔍 Text search failed with Exception: {e}")
            import traceback
            logger.error(f"🔍 Traceback: {traceback.format_exc()}")
            # Fallback to mock results
            return self._mock_search_results(limit, "text", query)

    async def _search_all_models(self, query: str, limit: int) -> List[SearchResult]:
        """Search across all available models and combine results"""
        all_results = []

        # Search with CLIP
        try:
            scores, idxs, image_paths = self._faiss_engine.text_search(
                text=query, k=limit, model_type="clip"
            )
            for i, (score, idx, path) in enumerate(zip(scores, idxs, image_paths)):
                if path:
                    image_url = f"/data/{path}"

                    # Extract folder and filename from the path
                    file_path = None
                    if path:
                        path_parts = path.split("/")
                        if len(path_parts) >= 3:
                            # Get the last two parts: folder and filename
                            file_path = f"{path_parts[-2]}/{path_parts[-1]}"

                    result = SearchResult(
                        image_id=f"clip2video_{idx}",
                        score=float(score),
                        link=path,
                        image_url=image_url,
                        watch_url=None,
                        ocr_text=None,
                        file_path=file_path,
                    )
                    all_results.append(result)
        except Exception as e:
            logger.warning(f"CLIP search failed: {e}")

        # Search with LongCLIP if available
        try:
            scores, idxs, image_paths = self._faiss_engine.text_search(
                text=query, k=limit, model_type="longclip"
            )
            for i, (score, idx, path) in enumerate(zip(scores, idxs, image_paths)):
                if path:
                    image_url = f"/data/{path}"

                    # Extract folder and filename from the path
                    file_path = None
                    if path:
                        path_parts = path.split("/")
                        if len(path_parts) >= 3:
                            # Get the last two parts: folder and filename
                            file_path = f"{path_parts[-2]}/{path_parts[-1]}"

                    result = SearchResult(
                        image_id=f"longclip_{idx}",
                        score=float(score),
                        link=path,
                        image_url=image_url,
                        watch_url=None,
                        ocr_text=None,
                        file_path=file_path,
                    )
                    all_results.append(result)
        except Exception as e:
            logger.warning(f"LongCLIP search failed: {e}")

        # Search with CLIP2Video if available
        try:
            scores, idxs, image_paths = self._faiss_engine.text_search(
                text=query, k=limit, model_type="clip2video"
            )
            for i, (score, idx, path) in enumerate(zip(scores, idxs, image_paths)):
                if path:
                    image_url = f"/data/{path}"

                    # Extract folder and filename from the path
                    file_path = None
                    if path:
                        path_parts = path.split("/")
                        if len(path_parts) >= 3:
                            # Get the last two parts: folder and filename
                            file_path = f"{path_parts[-2]}/{path_parts[-1]}"

                    result = SearchResult(
                        image_id=f"clip2video_{idx}",
                        score=float(score),
                        link=path,
                        image_url=image_url,
                        watch_url=None,
                        ocr_text=None,
                        file_path=file_path,
                    )
                    all_results.append(result)
        except Exception as e:
            logger.warning(f"CLIP2Video search failed: {e}")

        # Search with BEIT3 if available
        try:
            logger.info("🔍 Multi-model: Searching with BEIT3...")
            scores, idxs, image_paths = self._faiss_engine.text_search(
                text=query, k=limit, model_type="beit3"
            )
            logger.info(f"🔍 Multi-model BEIT3: scores={len(scores)}, idxs={len(idxs)}, paths={len(image_paths)}")
            for i, (score, idx, path) in enumerate(zip(scores, idxs, image_paths)):
                if path:
                    image_url = f"/data/{path}"

                    # Extract folder and filename from the path
                    file_path = None
                    if path:
                        path_parts = path.split("/")
                        if len(path_parts) >= 3:
                            # Get the last two parts: folder and filename
                            file_path = f"{path_parts[-2]}/{path_parts[-1]}"

                    result = SearchResult(
                        image_id=f"beit3_{idx}",
                        score=float(score),
                        link=path,
                        image_url=image_url,
                        watch_url=None,
                        ocr_text=None,
                        file_path=file_path,
                    )
                    all_results.append(result)
                    if i < 2:  # Log first 2 BEIT3 results
                        logger.info(f"🔍 Multi-model BEIT3 Result {i+1}: score={score:.4f}, path={path}")
            logger.info(f"🔍 Multi-model BEIT3: Added {len([r for r in all_results if r.image_id.startswith('beit3_')])} BEIT3 results")
        except ValueError as e:
            if "BEIT3 model not available" in str(e):
                logger.warning("🔍 Multi-model BEIT3 model not available - checkpoint file missing. Please download beit3_large_patch16_384_coco_retrieval.pth")
            else:
                logger.warning(f"🔍 Multi-model BEIT3 search failed: {e}")
        except Exception as e:
            logger.warning(f"🔍 Multi-model BEIT3 search failed: {e}")

        # Remove duplicates based on image path and sort by score
        seen_paths = set()
        unique_results = []
        for result in sorted(all_results, key=lambda x: x.score, reverse=True):
            if result.link not in seen_paths:
                seen_paths.add(result.link)
                unique_results.append(result)
                if len(unique_results) >= limit:
                    break

        logger.info(
            "Multi-model search completed",
            query=query,
            results_count=len(unique_results),
        )
        return unique_results

    def _remove_duplicates(
        self, results: List[SearchResult], limit: int
    ) -> List[SearchResult]:
        """Remove duplicate results based on image_id"""
        seen_ids = set()
        unique_results = []

        for result in results:
            if result.image_id not in seen_ids:
                seen_ids.add(result.image_id)
                unique_results.append(result)

                if len(unique_results) >= limit:
                    break

        return unique_results

    async def _enhance_results_with_metadata(
        self, results: List[SearchResult]
    ) -> List[SearchResult]:
        """Enhance search results with detailed metadata"""
        if not self._metadata_service or not self._metadata_service.is_initialized():
            logger.warning("Metadata service not available, returning basic results")
            return results

        enhanced_results = []
        for result in results:
            try:
                # Skip enhancement for BEiT3 results as they don't have metadata
                if result.image_id.startswith("beit3_"):
                    enhanced_results.append(result)
                    continue
                
                # Get detailed metadata for this frame
                metadata = self._metadata_service.get_frame_metadata(result.image_id)

                if metadata:
                    # Enhance the result with metadata
                    enhanced_result = SearchResult(
                        image_id=result.image_id,
                        score=result.score,
                        link=result.link,
                        image_url=result.image_url,
                        watch_url=result.watch_url,
                        ocr_text=result.ocr_text,
                        bbox=result.bbox,
                        video_id=metadata.get("video_info", {}).get("filename", ""),
                        shot_index=metadata.get("keyframe_info", {}).get("shot_index"),
                        frame_stamp=metadata.get("keyframe_info", {}).get("timestamp"),
                        # Add additional metadata fields if needed
                        metadata=metadata,
                    )
                else:
                    enhanced_result = result

                enhanced_results.append(enhanced_result)

            except Exception as e:
                logger.warning(f"Failed to enhance result {result.image_id}: {e}")
                enhanced_results.append(result)

        return enhanced_results

    async def image_search(
        self,
        image_source: Union[str, bytes],
        model_type: ModelType = ModelType.CLIP,
        limit: int = 20,
    ) -> List[SearchResult]:
        """Perform image-based search"""
        await self._ensure_models_loaded()

        if self._faiss_engine is None:
            # Mock response for development
            return self._mock_search_results(limit, "image", "image_query")

        try:
            if model_type == ModelType.ALL:
                # Search across all available models and combine results
                return await self._image_search_all_models(image_source, limit)
            else:
                # Use the specified model
                scores, idxs, image_paths = self._faiss_engine.image_search(
                    k=limit,
                    model_type=model_type.value,
                    image_id=None,
                    image_source=image_source,
                )

                results = []
                for i, (score, idx, path) in enumerate(zip(scores, idxs, image_paths)):
                    if path:
                        # Create proper image URL for frontend display
                        # The path from id2img.json is already in the format "raw/keyframes/Keyframes_L21/keyframes/L21_V001/001.jpg"
                        # So we just need to prepend "/data/" to make it accessible via the static file mount
                        image_url = f"/data/{path}"

                        # Extract folder and filename from the path
                        file_path = None
                        if path:
                            path_parts = path.split("/")
                            if len(path_parts) >= 3:
                                # Get the last two parts: folder and filename
                                file_path = f"{path_parts[-2]}/{path_parts[-1]}"

                        result = SearchResult(
                            image_id=f"{model_type.value}_{idx}",
                            score=float(score),
                            link=path,
                            image_url=image_url,
                            watch_url=None,
                            ocr_text=None,
                            file_path=file_path,
                        )
                        results.append(result)

                # Remove duplicates and return results
                unique_results = self._remove_duplicates(results, limit)

                # Enhance results with metadata
                enhanced_results = await self._enhance_results_with_metadata(
                    unique_results
                )

                return enhanced_results

        except Exception as e:
            logger.error("Image search failed", error=str(e))
            # Fallback to mock results
            return self._mock_search_results(limit, "image", "image_query")

    async def _image_search_all_models(
        self, image_source: Union[str, bytes], limit: int
    ) -> List[SearchResult]:
        """Search across all available models for image search and combine results"""
        all_results = []

        # Search with CLIP
        try:
            scores, idxs, image_paths = self._faiss_engine.image_search(
                k=limit,
                model_type="clip",
                image_id=None,
                image_source=image_source,
            )
            for i, (score, idx, path) in enumerate(zip(scores, idxs, image_paths)):
                if path:
                    image_url = f"/data/{path}"

                    # Extract folder and filename from the path
                    file_path = None
                    if path:
                        path_parts = path.split("/")
                        if len(path_parts) >= 3:
                            # Get the last two parts: folder and filename
                            file_path = f"{path_parts[-2]}/{path_parts[-1]}"

                    result = SearchResult(
                        image_id=f"clip_{idx}",
                        score=float(score),
                        link=path,
                        image_url=image_url,
                        watch_url=None,
                        ocr_text=None,
                        file_path=file_path,
                    )
                    all_results.append(result)
        except Exception as e:
            logger.warning(f"CLIP image search failed: {e}")

        # Search with LongCLIP if available
        try:
            scores, idxs, image_paths = self._faiss_engine.image_search(
                k=limit,
                model_type="longclip",
                image_id=None,
                image_source=image_source,
            )
            for i, (score, idx, path) in enumerate(zip(scores, idxs, image_paths)):
                if path:
                    image_url = f"/data/{path}"

                    # Extract folder and filename from the path
                    file_path = None
                    if path:
                        path_parts = path.split("/")
                        if len(path_parts) >= 3:
                            # Get the last two parts: folder and filename
                            file_path = f"{path_parts[-2]}/{path_parts[-1]}"

                    result = SearchResult(
                        image_id=f"longclip_{idx}",
                        score=float(score),
                        link=path,
                        image_url=image_url,
                        watch_url=None,
                        ocr_text=None,
                        file_path=file_path,
                    )
                    all_results.append(result)
        except Exception as e:
            logger.warning(f"LongCLIP image search failed: {e}")

        # Search with CLIP2Video if available
        try:
            scores, idxs, image_paths = self._faiss_engine.image_search(
                k=limit,
                model_type="clip2video",
                image_id=None,
                image_source=image_source,
            )
            for i, (score, idx, path) in enumerate(zip(scores, idxs, image_paths)):
                if path:
                    image_url = f"/data/{path}"

                    # Extract folder and filename from the path
                    file_path = None
                    if path:
                        path_parts = path.split("/")
                        if len(path_parts) >= 3:
                            # Get the last two parts: folder and filename
                            file_path = f"{path_parts[-2]}/{path_parts[-1]}"

                    result = SearchResult(
                        image_id=f"clip2video_{idx}",
                        score=float(score),
                        link=path,
                        image_url=image_url,
                        watch_url=None,
                        ocr_text=None,
                        file_path=file_path,
                    )
                    all_results.append(result)
        except Exception as e:
            logger.warning(f"CLIP2Video image search failed: {e}")

        # Search with BEIT3 if available
        try:
            scores, idxs, image_paths = self._faiss_engine.image_search(
                k=limit,
                model_type="beit3",
                image_id=None,
                image_source=image_source,
            )
            for i, (score, idx, path) in enumerate(zip(scores, idxs, image_paths)):
                if path:
                    image_url = f"/data/{path}"

                    # Extract folder and filename from the path
                    file_path = None
                    if path:
                        path_parts = path.split("/")
                        if len(path_parts) >= 3:
                            # Get the last two parts: folder and filename
                            file_path = f"{path_parts[-2]}/{path_parts[-1]}"

                    result = SearchResult(
                        image_id=f"beit3_{idx}",
                        score=float(score),
                        link=path,
                        image_url=image_url,
                        watch_url=None,
                        ocr_text=None,
                        file_path=file_path,
                    )
                    all_results.append(result)
        except Exception as e:
            logger.warning(f"BEIT3 image search failed: {e}")

        # Remove duplicates based on image path and sort by score
        seen_paths = set()
        unique_results = []
        for result in sorted(all_results, key=lambda x: x.score, reverse=True):
            if result.link not in seen_paths:
                seen_paths.add(result.link)
                unique_results.append(result)
                if len(unique_results) >= limit:
                    break

        logger.info(
            "Multi-model image search completed", results_count=len(unique_results)
        )
        return unique_results

    async def visual_search(
        self,
        object_list: List[dict],
        logic: SearchLogic = SearchLogic.AND,
        model_type: ModelType = ModelType.LONGCLIP,
        limit: int = 20,
    ) -> List[SearchResult]:
        """Perform visual search with object detection"""
        await self._ensure_models_loaded()

        # For now, return mock results
        # TODO: Implement actual visual search logic
        logger.info("Visual search request", object_count=len(object_list), logic=logic)
        return self._mock_search_results(limit, "visual", f"objects_{len(object_list)}")

    async def neighbor_search(
        self, image_id: str, model_type: ModelType = ModelType.CLIP, limit: int = 20
    ) -> List[SearchResult]:
        """Perform similar image search"""
        await self._ensure_models_loaded()

        if self._faiss_engine is None:
            # Mock response for development
            return self._mock_search_results(limit, "neighbor", image_id)

        try:
            if model_type == ModelType.ALL:
                # Search across all available models and combine results
                return await self._neighbor_search_all_models(image_id, limit)
            else:
                # Use the real FAISS engine
                # Extract numeric ID from image_id
                try:
                    numeric_id = int(image_id.split("_")[-1])
                except (ValueError, IndexError):
                    numeric_id = 0

                scores, idxs, image_paths = self._faiss_engine.image_search(
                    k=limit,
                    model_type=model_type.value,
                    image_id=numeric_id,
                    image_source=None,
                )

                results = []
                for i, (score, idx, path) in enumerate(zip(scores, idxs, image_paths)):
                    if path:
                        # Create proper image URL for frontend display
                        # The path from id2img.json is already in the format "raw/keyframes/Keyframes_L21/keyframes/L21_V001/001.jpg"
                        # So we just need to prepend "/data/" to make it accessible via the static file mount
                        image_url = f"/data/{path}"

                        # Extract folder and filename from the path
                        file_path = None
                        if path:
                            path_parts = path.split("/")
                            if len(path_parts) >= 3:
                                # Get the last two parts: folder and filename
                                file_path = f"{path_parts[-2]}/{path_parts[-1]}"

                        result = SearchResult(
                            image_id=f"{model_type.value}_{idx}",
                            score=float(score),
                            link=path,
                            image_url=image_url,
                            watch_url=None,
                            ocr_text=None,
                            file_path=file_path,
                        )
                        results.append(result)

                logger.info(
                    "Neighbor search completed",
                    image_id=image_id,
                    results_count=len(results),
                )
                return results

        except Exception as e:
            logger.error("Neighbor search failed", image_id=image_id, error=str(e))
            # Fallback to mock results
            return self._mock_search_results(limit, "neighbor", image_id)

    async def _neighbor_search_all_models(
        self, image_id: str, limit: int
    ) -> List[SearchResult]:
        """Search across all available models for neighbor search and combine results"""
        all_results = []

        # Extract numeric ID from image_id
        try:
            numeric_id = int(image_id.split("_")[-1])
        except (ValueError, IndexError):
            numeric_id = 0

        # Search with CLIP
        try:
            scores, idxs, image_paths = self._faiss_engine.image_search(
                k=limit,
                model_type="clip",
                image_id=numeric_id,
                image_source=None,
            )
            for i, (score, idx, path) in enumerate(zip(scores, idxs, image_paths)):
                if path:
                    image_url = f"/data/{path}"

                    # Extract folder and filename from the path
                    file_path = None
                    if path:
                        path_parts = path.split("/")
                        if len(path_parts) >= 3:
                            # Get the last two parts: folder and filename
                            file_path = f"{path_parts[-2]}/{path_parts[-1]}"

                    result = SearchResult(
                        image_id=f"clip_{idx}",
                        score=float(score),
                        link=path,
                        image_url=image_url,
                        watch_url=None,
                        ocr_text=None,
                        file_path=file_path,
                    )
                    all_results.append(result)
        except Exception as e:
            logger.warning(f"CLIP neighbor search failed: {e}")

        # Search with LongCLIP if available
        try:
            scores, idxs, image_paths = self._faiss_engine.image_search(
                k=limit,
                model_type="longclip",
                image_id=numeric_id,
                image_source=None,
            )
            for i, (score, idx, path) in enumerate(zip(scores, idxs, image_paths)):
                if path:
                    image_url = f"/data/{path}"

                    # Extract folder and filename from the path
                    file_path = None
                    if path:
                        path_parts = path.split("/")
                        if len(path_parts) >= 3:
                            # Get the last two parts: folder and filename
                            file_path = f"{path_parts[-2]}/{path_parts[-1]}"

                    result = SearchResult(
                        image_id=f"longclip_{idx}",
                        score=float(score),
                        link=path,
                        image_url=image_url,
                        watch_url=None,
                        ocr_text=None,
                        file_path=file_path,
                    )
                    all_results.append(result)
        except Exception as e:
            logger.warning(f"LongCLIP neighbor search failed: {e}")

        # Search with CLIP2Video if available
        try:
            scores, idxs, image_paths = self._faiss_engine.image_search(
                k=limit,
                model_type="clip2video",
                image_id=numeric_id,
                image_source=None,
            )
            for i, (score, idx, path) in enumerate(zip(scores, idxs, image_paths)):
                if path:
                    image_url = f"/data/{path}"

                    # Extract folder and filename from the path
                    file_path = None
                    if path:
                        path_parts = path.split("/")
                        if len(path_parts) >= 3:
                            # Get the last two parts: folder and filename
                            file_path = f"{path_parts[-2]}/{path_parts[-1]}"

                    result = SearchResult(
                        image_id=f"clip2video_{idx}",
                        score=float(score),
                        link=path,
                        image_url=image_url,
                        watch_url=None,
                        ocr_text=None,
                        file_path=file_path,
                    )
                    all_results.append(result)
        except Exception as e:
            logger.warning(f"CLIP2Video neighbor search failed: {e}")

        # Search with BEIT3 if available
        try:
            scores, idxs, image_paths = self._faiss_engine.image_search(
                k=limit,
                model_type="beit3",
                image_id=numeric_id,
                image_source=None,
            )
            for i, (score, idx, path) in enumerate(zip(scores, idxs, image_paths)):
                if path:
                    image_url = f"/data/{path}"

                    # Extract folder and filename from the path
                    file_path = None
                    if path:
                        path_parts = path.split("/")
                        if len(path_parts) >= 3:
                            # Get the last two parts: folder and filename
                            file_path = f"{path_parts[-2]}/{path_parts[-1]}"

                    result = SearchResult(
                        image_id=f"beit3_{idx}",
                        score=float(score),
                        link=path,
                        image_url=image_url,
                        watch_url=None,
                        ocr_text=None,
                        file_path=file_path,
                    )
                    all_results.append(result)
        except Exception as e:
            logger.warning(f"BEIT3 neighbor search failed: {e}")

        # Remove duplicates based on image path and sort by score
        seen_paths = set()
        unique_results = []
        for result in sorted(all_results, key=lambda x: x.score, reverse=True):
            if result.link not in seen_paths:
                seen_paths.add(result.link)
                unique_results.append(result)
                if len(unique_results) >= limit:
                    break

        logger.info(
            "Multi-model neighbor search completed",
            image_id=image_id,
            results_count=len(unique_results),
        )
        return unique_results

    def _mock_search_results(
        self, limit: int, search_type: str, query: str
    ) -> List[SearchResult]:
        """Generate mock search results for development"""
        results = []
        for i in range(min(limit, 10)):
            result = SearchResult(
                image_id=f"mock_{search_type}_{i}",
                score=0.9 - (i * 0.1),
                link=f"/mock/image_{i}.jpg",
                image_url=f"/mock/image_{i}.jpg",
                watch_url=None,
                ocr_text=None,
                file_path=f"mock_folder_{i}/image_{i}.jpg",
            )
            results.append(result)

        logger.info(
            "Generated mock search results", search_type=search_type, count=len(results)
        )
        return results

    async def cleanup(self):
        """Cleanup resources"""
        logger.info("Cleaning up SearchService")
        self._faiss_engine = None
        self._models_loaded = False
