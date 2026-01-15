"""Long-term memory system using vector store for persistent context storage."""
import json
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime

from langchain_community.vectorstores import Chroma
from langchain_openai import OpenAIEmbeddings
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter

from novel_agent.config import VECTOR_STORE_DIR, OPENAI_API_KEY


class LongTermMemory:
    """Manages long-term memory storage using vector database for novel writing context."""

    def __init__(self, collection_name: str = "novel_memory", vector_store_dir: Optional[Path] = None):
        """
        Initialize the long-term memory system.

        Args:
            collection_name: Name of the vector store collection
            vector_store_dir: Optional custom directory for vector store (defaults to VECTOR_STORE_DIR from config)
        """
        self.collection_name = collection_name
        self.embeddings = OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY)
        base_dir = vector_store_dir if vector_store_dir is not None else VECTOR_STORE_DIR
        self.vector_store_path = base_dir / collection_name
        self.vector_store_path.mkdir(parents=True, exist_ok=True)

        # Initialize or load vector store
        self.vector_store = Chroma(
            collection_name=collection_name,
            embedding_function=self.embeddings,
            persist_directory=str(self.vector_store_path)
        )

        # Text splitter for large documents
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
            length_function=len
        )

    def store_character(self, character_data: Dict[str, Any]) -> str:
        """
        Store character information in memory.

        Args:
            character_data: Dictionary containing character details

        Returns:
            ID of the stored document
        """
        character_text = self._format_character(character_data)
        metadata = {
            "type": "character",
            "name": character_data.get("name", "Unknown"),
            "timestamp": datetime.now().isoformat()
        }

        doc = Document(page_content=character_text, metadata=metadata)
        ids = self.vector_store.add_documents([doc])
        return ids[0] if ids else None

    def store_plot(self, plot_data: Dict[str, Any]) -> str:
        """
        Store plot information in memory.

        Args:
            plot_data: Dictionary containing plot details

        Returns:
            ID of the stored document
        """
        plot_text = self._format_plot(plot_data)
        metadata = {
            "type": "plot",
            "title": plot_data.get("title", "Untitled"),
            "timestamp": datetime.now().isoformat()
        }

        doc = Document(page_content=plot_text, metadata=metadata)
        ids = self.vector_store.add_documents([doc])
        return ids[0] if ids else None

    def store_chapter(self, chapter_data: Dict[str, Any]) -> str:
        """
        Store chapter content in memory.

        Args:
            chapter_data: Dictionary containing chapter details

        Returns:
            ID of the stored document
        """
        chapter_text = self._format_chapter(chapter_data)
        metadata = {
            "type": "chapter",
            "chapter_number": chapter_data.get("chapter_number", 0),
            "title": chapter_data.get("title", "Untitled"),
            "timestamp": datetime.now().isoformat()
        }

        # Split long chapters into chunks
        chunks = self.text_splitter.split_text(chapter_text)
        docs = [
            Document(page_content=chunk, metadata={**metadata, "chunk_index": i})
            for i, chunk in enumerate(chunks)
        ]

        ids = self.vector_store.add_documents(docs)
        return ids[0] if ids else None

    def store_setting(self, setting_data: Dict[str, Any]) -> str:
        """
        Store world-building and setting information.

        Args:
            setting_data: Dictionary containing setting details

        Returns:
            ID of the stored document
        """
        setting_text = self._format_setting(setting_data)
        metadata = {
            "type": "setting",
            "location": setting_data.get("location", "Unknown"),
            "timestamp": datetime.now().isoformat()
        }

        doc = Document(page_content=setting_text, metadata=metadata)
        ids = self.vector_store.add_documents([doc])
        return ids[0] if ids else None

    def store_outline(self, outline_data: Dict[str, Any]) -> str:
        """
        Store chapter outline information.

        Args:
            outline_data: Dictionary containing outline details

        Returns:
            ID of the stored document
        """
        outline_text = self._format_outline(outline_data)
        metadata = {
            "type": "outline",
            "title": outline_data.get("title", "Untitled"),
            "timestamp": datetime.now().isoformat()
        }

        doc = Document(page_content=outline_text, metadata=metadata)
        ids = self.vector_store.add_documents([doc])
        return ids[0] if ids else None

    def retrieve_context(self, query: str, k: int = 5, filter_type: Optional[str] = None) -> List[Document]:
        """
        Retrieve relevant context from memory.

        Args:
            query: Search query
            k: Number of results to return
            filter_type: Optional filter by document type

        Returns:
            List of relevant documents
        """
        if filter_type:
            results = self.vector_store.similarity_search(
                query,
                k=k,
                filter={"type": filter_type}
            )
        else:
            results = self.vector_store.similarity_search(query, k=k)

        return results

    def retrieve_by_type(self, doc_type: str, k: int = 10) -> List[Document]:
        """
        Retrieve all documents of a specific type.

        Args:
            doc_type: Type of document (character, plot, chapter, etc.)
            k: Maximum number of results

        Returns:
            List of documents of the specified type
        """
        # Use a generic query to get all documents of this type
        results = self.vector_store.similarity_search(
            doc_type,
            k=k,
            filter={"type": doc_type}
        )
        return results

    def get_all_characters(self) -> List[Document]:
        """Retrieve all stored characters."""
        return self.retrieve_by_type("character", k=20)

    def get_plot_summary(self) -> Optional[Document]:
        """Retrieve the main plot summary."""
        results = self.retrieve_by_type("plot", k=1)
        return results[0] if results else None

    def get_all_chapters(self) -> List[Document]:
        """Retrieve all stored chapters."""
        return self.retrieve_by_type("chapter", k=50)

    def clear_memory(self):
        """Clear all stored memory (use with caution)."""
        # Delete and recreate the collection
        self.vector_store.delete_collection()
        self.vector_store = Chroma(
            collection_name=self.collection_name,
            embedding_function=self.embeddings,
            persist_directory=str(self.vector_store_path)
        )

    # Helper methods for formatting data
    def _format_character(self, data: Dict[str, Any]) -> str:
        """Format character data for storage."""
        return f"""Character: {data.get('name', 'Unknown')}
Age: {data.get('age', 'Unknown')}
Role: {data.get('role', 'Unknown')}
Personality: {data.get('personality', 'Not specified')}
Background: {data.get('background', 'Not specified')}
Appearance: {data.get('appearance', 'Not specified')}
Motivations: {data.get('motivations', 'Not specified')}
Relationships: {data.get('relationships', 'Not specified')}
"""

    def _format_plot(self, data: Dict[str, Any]) -> str:
        """Format plot data for storage."""
        return f"""Plot: {data.get('title', 'Untitled')}
Genre: {data.get('genre', 'Not specified')}
Premise: {data.get('premise', 'Not specified')}
Main Conflict: {data.get('conflict', 'Not specified')}
Theme: {data.get('theme', 'Not specified')}
Story Arc: {data.get('arc', 'Not specified')}
"""

    def _format_chapter(self, data: Dict[str, Any]) -> str:
        """Format chapter data for storage."""
        return f"""Chapter {data.get('chapter_number', 0)}: {data.get('title', 'Untitled')}

{data.get('content', '')}

Summary: {data.get('summary', 'No summary available')}
"""

    def _format_setting(self, data: Dict[str, Any]) -> str:
        """Format setting data for storage."""
        return f"""Setting: {data.get('location', 'Unknown')}
Time Period: {data.get('time_period', 'Not specified')}
Description: {data.get('description', 'Not specified')}
Culture: {data.get('culture', 'Not specified')}
Important Locations: {data.get('important_locations', 'Not specified')}
"""

    def _format_outline(self, data: Dict[str, Any]) -> str:
        """Format outline data for storage."""
        chapters = data.get('chapters', [])
        chapter_text = "\n".join([
            f"Chapter {i+1}: {ch.get('title', 'Untitled')} - {ch.get('summary', 'No summary')}"
            for i, ch in enumerate(chapters)
        ])

        return f"""Outline: {data.get('title', 'Untitled')}
Total Chapters: {len(chapters)}

{chapter_text}
"""
