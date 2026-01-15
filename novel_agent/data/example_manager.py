"""Manager for handling good and bad novel examples for training and learning."""
import json
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

from novel_agent.config import EXAMPLES_DIR


class ExampleManager:
    """Manages storage and retrieval of good and bad novel examples."""

    def __init__(self):
        """Initialize the example manager."""
        self.examples_dir = EXAMPLES_DIR
        self.examples_dir.mkdir(parents=True, exist_ok=True)

        # Separate directories for good and bad examples
        self.good_examples_dir = self.examples_dir / "good"
        self.bad_examples_dir = self.examples_dir / "bad"

        self.good_examples_dir.mkdir(exist_ok=True)
        self.bad_examples_dir.mkdir(exist_ok=True)

        # Index files
        self.good_index_file = self.examples_dir / "good_index.json"
        self.bad_index_file = self.examples_dir / "bad_index.json"

        # Load or initialize indices
        self.good_index = self._load_index(self.good_index_file)
        self.bad_index = self._load_index(self.bad_index_file)

    def _load_index(self, index_file: Path) -> List[Dict[str, Any]]:
        """Load index from file or create empty index."""
        if index_file.exists():
            with open(index_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return []

    def _save_index(self, index_file: Path, index: List[Dict[str, Any]]):
        """Save index to file."""
        with open(index_file, 'w', encoding='utf-8') as f:
            json.dump(index, f, indent=2, ensure_ascii=False)

    def add_good_example(
        self,
        content: str,
        category: str,
        description: str = "",
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Add a good novel example.

        Args:
            content: The novel content/excerpt
            category: Category (plot, dialogue, description, character, etc.)
            description: Description of why this is a good example
            metadata: Additional metadata

        Returns:
            ID of the added example
        """
        return self._add_example(
            content, category, description, metadata,
            self.good_examples_dir, self.good_index, self.good_index_file
        )

    def add_bad_example(
        self,
        content: str,
        category: str,
        description: str = "",
        issues: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Add a bad novel example.

        Args:
            content: The novel content/excerpt
            category: Category (plot, dialogue, description, character, etc.)
            description: Description of what makes this a bad example
            issues: List of specific issues
            metadata: Additional metadata

        Returns:
            ID of the added example
        """
        if metadata is None:
            metadata = {}
        metadata["issues"] = issues or []

        return self._add_example(
            content, category, description, metadata,
            self.bad_examples_dir, self.bad_index, self.bad_index_file
        )

    def _add_example(
        self,
        content: str,
        category: str,
        description: str,
        metadata: Optional[Dict[str, Any]],
        examples_dir: Path,
        index: List[Dict[str, Any]],
        index_file: Path
    ) -> str:
        """Internal method to add an example."""
        # Generate unique ID
        example_id = f"{category}_{datetime.now().strftime('%Y%m%d_%H%M%S_%f')}"
        file_path = examples_dir / f"{example_id}.txt"

        # Save content
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)

        # Update index
        index_entry = {
            "id": example_id,
            "category": category,
            "description": description,
            "file_path": str(file_path),
            "timestamp": datetime.now().isoformat(),
            "metadata": metadata or {}
        }
        index.append(index_entry)
        self._save_index(index_file, index)

        return example_id

    def get_good_examples(
        self,
        category: Optional[str] = None,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get good examples, optionally filtered by category.

        Args:
            category: Optional category filter
            limit: Maximum number of examples to return

        Returns:
            List of example dictionaries with content
        """
        return self._get_examples(self.good_index, category, limit)

    def get_bad_examples(
        self,
        category: Optional[str] = None,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        Get bad examples, optionally filtered by category.

        Args:
            category: Optional category filter
            limit: Maximum number of examples to return

        Returns:
            List of example dictionaries with content
        """
        return self._get_examples(self.bad_index, category, limit)

    def _get_examples(
        self,
        index: List[Dict[str, Any]],
        category: Optional[str],
        limit: Optional[int]
    ) -> List[Dict[str, Any]]:
        """Internal method to get examples."""
        # Filter by category if specified
        examples = index if category is None else [
            ex for ex in index if ex["category"] == category
        ]

        # Apply limit
        if limit is not None:
            examples = examples[:limit]

        # Load content for each example
        result = []
        for ex in examples:
            try:
                with open(ex["file_path"], 'r', encoding='utf-8') as f:
                    content = f.read()
                result.append({
                    **ex,
                    "content": content
                })
            except FileNotFoundError:
                continue

        return result

    def get_example_by_id(self, example_id: str, is_good: bool = True) -> Optional[Dict[str, Any]]:
        """
        Get a specific example by ID.

        Args:
            example_id: The example ID
            is_good: Whether to look in good (True) or bad (False) examples

        Returns:
            Example dictionary with content, or None if not found
        """
        index = self.good_index if is_good else self.bad_index

        for ex in index:
            if ex["id"] == example_id:
                try:
                    with open(ex["file_path"], 'r', encoding='utf-8') as f:
                        content = f.read()
                    return {**ex, "content": content}
                except FileNotFoundError:
                    return None
        return None

    def remove_example(self, example_id: str, is_good: bool = True) -> bool:
        """
        Remove an example.

        Args:
            example_id: The example ID
            is_good: Whether to look in good (True) or bad (False) examples

        Returns:
            True if removed, False if not found
        """
        index = self.good_index if is_good else self.bad_index
        index_file = self.good_index_file if is_good else self.bad_index_file

        for i, ex in enumerate(index):
            if ex["id"] == example_id:
                # Remove file
                try:
                    Path(ex["file_path"]).unlink()
                except FileNotFoundError:
                    pass

                # Remove from index
                index.pop(i)
                self._save_index(index_file, index)
                return True

        return False

    def get_categories(self, is_good: bool = True) -> List[str]:
        """
        Get all unique categories.

        Args:
            is_good: Whether to look in good (True) or bad (False) examples

        Returns:
            List of unique categories
        """
        index = self.good_index if is_good else self.bad_index
        return list(set(ex["category"] for ex in index))

    def get_statistics(self) -> Dict[str, Any]:
        """
        Get statistics about stored examples.

        Returns:
            Dictionary with statistics
        """
        return {
            "good_examples": {
                "total": len(self.good_index),
                "by_category": self._count_by_category(self.good_index)
            },
            "bad_examples": {
                "total": len(self.bad_index),
                "by_category": self._count_by_category(self.bad_index)
            }
        }

    def _count_by_category(self, index: List[Dict[str, Any]]) -> Dict[str, int]:
        """Count examples by category."""
        counts = {}
        for ex in index:
            category = ex["category"]
            counts[category] = counts.get(category, 0) + 1
        return counts

    def create_comparison_prompt(self, category: str, num_examples: int = 3) -> str:
        """
        Create a prompt comparing good and bad examples for learning.

        Args:
            category: Category to compare
            num_examples: Number of examples to include

        Returns:
            Formatted prompt string
        """
        good_examples = self.get_good_examples(category, num_examples)
        bad_examples = self.get_bad_examples(category, num_examples)

        prompt_parts = [
            f"=== Examples of {category.upper()} ===\n",
            "GOOD EXAMPLES (What to emulate):\n"
        ]

        for i, ex in enumerate(good_examples, 1):
            prompt_parts.append(f"\nGood Example {i}:")
            prompt_parts.append(f"Why it's good: {ex['description']}")
            prompt_parts.append(f"Content:\n{ex['content']}\n")

        prompt_parts.append("\nBAD EXAMPLES (What to avoid):\n")

        for i, ex in enumerate(bad_examples, 1):
            prompt_parts.append(f"\nBad Example {i}:")
            prompt_parts.append(f"Why it's bad: {ex['description']}")
            if "issues" in ex.get("metadata", {}):
                prompt_parts.append(f"Issues: {', '.join(ex['metadata']['issues'])}")
            prompt_parts.append(f"Content:\n{ex['content']}\n")

        return "\n".join(prompt_parts)
