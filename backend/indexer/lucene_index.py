"""
Lucene index management for text search (with Whoosh fallback)
"""

import json
import os
from typing import Dict, List, Optional, Tuple, Union

import numpy as np
import structlog

logger = structlog.get_logger()

# Try to import Lucene, fallback to Whoosh
try:
    import lucene
    from lucene import (
        DirectoryReader,
        Document,
        Field,
        FieldType,
        IndexSearcher,
        IndexWriter,
        IndexWriterConfig,
        QueryParser,
        SimpleFSDirectory,
        StandardAnalyzer,
        StringField,
        TextField,
    )

    LUCENE_AVAILABLE = True
    logger.info("Lucene indexing available")
except ImportError:
    LUCENE_AVAILABLE = False
    logger.warning("Lucene not available, using Whoosh fallback")
    try:
        from whoosh.analysis import StandardAnalyzer
        from whoosh.fields import ID, KEYWORD, NUMERIC, TEXT, Schema
        from whoosh.index import create_in, open_dir
        from whoosh.qparser import MultifieldParser, QueryParser

        WHOOSH_AVAILABLE = True
        logger.info("Whoosh indexing available as fallback")
    except ImportError:
        WHOOSH_AVAILABLE = False
        logger.error("Neither Lucene nor Whoosh available for text indexing")


class LuceneIndex:
    """Text index management for video metadata and surrogate text"""

    def __init__(self, index_path: str):
        self.index_path = index_path
        self.index = None
        self.searcher = None
        self.writer = None
        self.use_lucene = LUCENE_AVAILABLE
        self.use_whoosh = WHOOSH_AVAILABLE

        if not self.use_lucene and not self.use_whoosh:
            raise RuntimeError("No text indexing backend available")

        os.makedirs(index_path, exist_ok=True)

    def create_schema(self) -> None:
        """Create index schema"""
        if self.use_lucene:
            self._create_lucene_schema()
        elif self.use_whoosh:
            self._create_whoosh_schema()

    def _create_lucene_schema(self) -> None:
        """Create Lucene index schema"""
        if not LUCENE_AVAILABLE:
            return

        # Initialize Lucene
        lucene.initVM()

        # Create directory and analyzer
        directory = SimpleFSDirectory(os.path.abspath(self.index_path))
        analyzer = StandardAnalyzer()

        # Configure index writer
        config = IndexWriterConfig(analyzer)
        self.writer = IndexWriter(directory, config)

        logger.info("Created Lucene index schema")

    def _create_whoosh_schema(self) -> None:
        """Create Whoosh index schema"""
        if not WHOOSH_AVAILABLE:
            return

        # Define schema
        schema = Schema(
            id=ID(stored=True),
            video_id=ID(stored=True),
            frame_id=ID(stored=True),
            shot_id=NUMERIC(stored=True),
            aladin_text=TEXT,
            gem_text=TEXT,
            object_classes=KEYWORD(stored=True),
            bbox_text=TEXT,
            metadata=TEXT,
        )

        # Create index
        self.index = create_in(self.index_path, schema)
        logger.info("Created Whoosh index schema")

    def add_document(
        self,
        doc_id: str,
        video_id: str,
        frame_id: str,
        shot_id: int,
        aladin_text: str = "",
        gem_text: str = "",
        object_classes: List[str] = None,
        bbox_text: str = "",
        metadata: Dict = None,
    ) -> None:
        """Add a document to the index"""
        if self.use_lucene:
            self._add_lucene_document(
                doc_id,
                video_id,
                frame_id,
                shot_id,
                aladin_text,
                gem_text,
                object_classes,
                bbox_text,
                metadata,
            )
        elif self.use_whoosh:
            self._add_whoosh_document(
                doc_id,
                video_id,
                frame_id,
                shot_id,
                aladin_text,
                gem_text,
                object_classes,
                bbox_text,
                metadata,
            )

    def _add_lucene_document(
        self,
        doc_id: str,
        video_id: str,
        frame_id: str,
        shot_id: int,
        aladin_text: str,
        gem_text: str,
        object_classes: List[str],
        bbox_text: str,
        metadata: Dict,
    ) -> None:
        """Add document to Lucene index"""
        if not LUCENE_AVAILABLE or self.writer is None:
            return

        # Create document
        doc = Document()

        # Add fields
        doc.add(StringField("id", doc_id, Field.Store.YES))
        doc.add(StringField("video_id", video_id, Field.Store.YES))
        doc.add(StringField("frame_id", frame_id, Field.Store.YES))
        doc.add(StringField("shot_id", str(shot_id), Field.Store.YES))

        if aladin_text:
            doc.add(TextField("aladin_text", aladin_text, Field.Store.NO))
        if gem_text:
            doc.add(TextField("gem_text", gem_text, Field.Store.NO))
        if object_classes:
            doc.add(
                TextField("object_classes", " ".join(object_classes), Field.Store.NO)
            )
        if bbox_text:
            doc.add(TextField("bbox_text", bbox_text, Field.Store.NO))
        if metadata:
            doc.add(TextField("metadata", json.dumps(metadata), Field.Store.NO))

        # Add to index
        self.writer.addDocument(doc)

    def _add_whoosh_document(
        self,
        doc_id: str,
        video_id: str,
        frame_id: str,
        shot_id: int,
        aladin_text: str,
        gem_text: str,
        object_classes: List[str],
        bbox_text: str,
        metadata: Dict,
    ) -> None:
        """Add document to Whoosh index"""
        if not WHOOSH_AVAILABLE or self.index is None:
            return

        # Get writer
        writer = self.index.writer()

        # Prepare document data
        doc_data = {
            "id": doc_id,
            "video_id": video_id,
            "frame_id": frame_id,
            "shot_id": shot_id,
        }

        if aladin_text:
            doc_data["aladin_text"] = aladin_text
        if gem_text:
            doc_data["gem_text"] = gem_text
        if object_classes:
            doc_data["object_classes"] = " ".join(object_classes)
        if bbox_text:
            doc_data["bbox_text"] = bbox_text
        if metadata:
            doc_data["metadata"] = json.dumps(metadata)

        # Add document
        writer.add_document(**doc_data)
        writer.commit()

    def commit(self) -> None:
        """Commit pending changes"""
        if self.use_lucene and self.writer:
            self.writer.commit()
            logger.info("Committed Lucene index changes")
        elif self.use_whoosh:
            # Whoosh commits automatically
            pass

    def close(self) -> None:
        """Close index resources"""
        if self.use_lucene and self.writer:
            self.writer.close()
        elif self.use_whoosh and self.index:
            self.index.close()

    def search(
        self, query: str, fields: List[str] = None, limit: int = 20, offset: int = 0
    ) -> List[Dict]:
        """Search the index"""
        if self.use_lucene:
            return self._search_lucene(query, fields, limit, offset)
        elif self.use_whoosh:
            return self._search_whoosh(query, fields, limit, offset)
        else:
            return []

    def _search_lucene(
        self, query: str, fields: List[str], limit: int, offset: int
    ) -> List[Dict]:
        """Search Lucene index"""
        if not LUCENE_AVAILABLE:
            return []

        try:
            # Open searcher
            directory = SimpleFSDirectory(os.path.abspath(self.index_path))
            reader = DirectoryReader.open(directory)
            searcher = IndexSearcher(reader)

            # Parse query
            if not fields:
                fields = ["aladin_text", "gem_text", "bbox_text", "metadata"]

            analyzer = StandardAnalyzer()
            query_parser = QueryParser(fields[0], analyzer)
            parsed_query = query_parser.parse(query)

            # Search
            top_docs = searcher.search(parsed_query, limit + offset)

            # Process results
            results = []
            for i in range(offset, min(offset + limit, len(top_docs.scoreDocs))):
                doc = searcher.doc(top_docs.scoreDocs[i].doc)
                results.append(
                    {
                        "id": doc.get("id"),
                        "video_id": doc.get("video_id"),
                        "frame_id": doc.get("frame_id"),
                        "shot_id": int(doc.get("shot_id")),
                        "score": top_docs.scoreDocs[i].score,
                    }
                )

            reader.close()
            return results

        except Exception as e:
            logger.error(f"Lucene search error: {e}")
            return []

    def _search_whoosh(
        self, query: str, fields: List[str], limit: int, offset: int
    ) -> List[Dict]:
        """Search Whoosh index"""
        if not WHOOSH_AVAILABLE or self.index is None:
            return []

        try:
            # Open searcher
            searcher = self.index.searcher()

            # Parse query
            if not fields:
                fields = ["aladin_text", "gem_text", "bbox_text", "metadata"]

            query_parser = MultifieldParser(fields, self.index.schema)
            parsed_query = query_parser.parse(query)

            # Search
            results = searcher.search(parsed_query, limit=limit + offset)

            # Process results
            processed_results = []
            for i, result in enumerate(results[offset : offset + limit]):
                processed_results.append(
                    {
                        "id": result["id"],
                        "video_id": result["video_id"],
                        "frame_id": result["frame_id"],
                        "shot_id": result["shot_id"],
                        "score": result.score,
                    }
                )

            searcher.close()
            return processed_results

        except Exception as e:
            logger.error(f"Whoosh search error: {e}")
            return []

    def search_by_class(self, class_name: str, limit: int = 20) -> List[Dict]:
        """Search by object class"""
        return self.search(f'object_classes:"{class_name}"', ["object_classes"], limit)

    def search_by_color(self, color_name: str, limit: int = 20) -> List[Dict]:
        """Search by color in bbox text"""
        return self.search(f'bbox_text:"{color_name}"', ["bbox_text"], limit)

    def get_stats(self) -> Dict:
        """Get index statistics"""
        stats = {
            "backend": "lucene" if self.use_lucene else "whoosh",
            "index_path": self.index_path,
        }

        if self.use_lucene:
            try:
                directory = SimpleFSDirectory(os.path.abspath(self.index_path))
                reader = DirectoryReader.open(directory)
                stats["total_documents"] = reader.numDocs()
                reader.close()
            except:
                stats["total_documents"] = "unknown"
        elif self.use_whoosh and self.index:
            try:
                searcher = self.index.searcher()
                stats["total_documents"] = searcher.doc_count()
                searcher.close()
            except:
                stats["total_documents"] = "unknown"

        return stats


def build_lucene_index_from_hdf5(
    hdf5_path: str, output_dir: str, use_lucene: bool = True
) -> LuceneIndex:
    """Build Lucene/Whoosh index from HDF5 file"""
    import h5py

    if not os.path.exists(hdf5_path):
        raise FileNotFoundError(f"HDF5 file not found: {hdf5_path}")

    os.makedirs(output_dir, exist_ok=True)

    # Create index
    index = LuceneIndex(output_dir)
    index.create_schema()

    # Load data from HDF5
    with h5py.File(hdf5_path, "r") as f:
        meta_group = f["meta"]
        bboxes_group = f["bboxes"]

        total_frames = meta_group["video_ids"].shape[0]

        # Index each frame
        for i in range(total_frames):
            video_id = (
                meta_group["video_ids"][i].decode()
                if isinstance(meta_group["video_ids"][i], bytes)
                else meta_group["video_ids"][i]
            )
            frame_id = (
                meta_group["frame_ids"][i].decode()
                if isinstance(meta_group["frame_ids"][i], bytes)
                else meta_group["frame_ids"][i]
            )
            shot_id = int(meta_group["shot_ids"][i])

            # Get bboxes for this frame
            frame_bbox_indices = np.where(bboxes_group["frame_index"][:] == i)[0]

            object_classes = []
            bbox_texts = []

            for idx in frame_bbox_indices:
                class_id = int(bboxes_group["class"][idx])
                color_name = (
                    bboxes_group["color_name"][idx].decode()
                    if isinstance(bboxes_group["color_name"][idx], bytes)
                    else bboxes_group["color_name"][idx]
                )

                # Convert class ID to name (simplified)
                class_name = f"class_{class_id}"
                object_classes.append(class_name)

                # Create bbox text representation
                bbox = bboxes_group["indices"][idx]
                bbox_text = f"{class_name} {color_name} at {bbox[0]:.2f},{bbox[1]:.2f}"
                bbox_texts.append(bbox_text)

            # Add document to index
            index.add_document(
                doc_id=f"{video_id}_{frame_id}",
                video_id=video_id,
                frame_id=frame_id,
                shot_id=shot_id,
                aladin_text=f"Frame from {video_id} showing {', '.join(object_classes)}",
                gem_text=f"Visual content: {', '.join(bbox_texts)}",
                object_classes=object_classes,
                bbox_text=" ".join(bbox_texts),
                metadata={"frame_index": i, "bbox_count": len(object_classes)},
            )

            if (i + 1) % 100 == 0:
                logger.info(f"Indexed {i + 1}/{total_frames} frames")

    # Commit and close
    index.commit()
    index.close()

    logger.info(f"Built text index with {total_frames} documents")
    return index
