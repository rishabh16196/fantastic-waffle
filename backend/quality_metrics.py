"""
Quality metrics computation for AI-generated examples.
"""

import re
from dataclasses import dataclass
from itertools import combinations
from typing import List, Set


@dataclass
class QualityMetrics:
    """Result of quality metrics computation."""
    examples_count: int
    avg_length_chars: int
    avg_length_words: int
    action_verb_count: int
    artifact_term_count: int
    generic_phrase_count: int
    uniqueness_score: float
    # Normalized metrics (per example averages)
    action_verb_density: float  # action verbs per 100 words
    artifact_density: float  # artifact terms per example
    generic_density: float  # generic phrases per example

    def to_dict(self) -> dict:
        """Convert to dictionary for DB storage."""
        return {
            "examples_count": self.examples_count,
            "avg_length_chars": self.avg_length_chars,
            "avg_length_words": self.avg_length_words,
            "action_verb_count": self.action_verb_count,
            "artifact_term_count": self.artifact_term_count,
            "generic_phrase_count": self.generic_phrase_count,
            "uniqueness_score": self.uniqueness_score,
        }


class QualityMetricsCalculator:
    def __init__(
        self,
        action_verbs: Set[str],
        artifact_terms: Set[str],
        generic_phrases: Set[str]
    ) -> None:
        self.action_verbs = action_verbs
        self.artifact_terms = artifact_terms
        self.generic_phrases = generic_phrases

    @classmethod
    def default(cls) -> "QualityMetricsCalculator":
        """Create calculator with default word lists."""
        return cls(
            action_verbs=ACTION_VERBS,
            artifact_terms=ARTIFACT_TERMS,
            generic_phrases=GENERIC_PHRASES
        )

    @staticmethod
    def _tokenize_words(text: str) -> List[str]:
        return re.findall(r"\b\w+\b", text.lower())

    @staticmethod
    def _count_phrase_occurrences(text: str, phrases: Set[str]) -> int:
        """Count phrase occurrences with word boundary awareness."""
        lowered = text.lower()
        count = 0
        for phrase in phrases:
            # Use word boundary regex for single-word terms
            if " " not in phrase:
                count += len(re.findall(rf"\b{re.escape(phrase)}\b", lowered))
            else:
                count += lowered.count(phrase)
        return count

    def _compute_uniqueness_score(self, examples: List[str]) -> float:
        if len(examples) <= 1:
            return 1.0

        gram_sets = []
        for example in examples:
            words = self._tokenize_words(example)
            if len(words) >= 3:
                grams = {" ".join(words[i:i + 3]) for i in range(len(words) - 2)}
            else:
                grams = set(words)
            gram_sets.append(grams)

        similarities = []
        for a, b in combinations(gram_sets, 2):
            if not a and not b:
                similarities.append(1.0)
                continue
            union = a | b
            similarity = (len(a & b) / len(union)) if union else 0.0
            similarities.append(similarity)

        avg_similarity = sum(similarities) / len(similarities)
        return max(0.0, min(1.0, 1.0 - avg_similarity))

    def compute(self, examples: List[str]) -> QualityMetrics:
        """Compute quality metrics for a list of examples."""
        if not examples:
            return QualityMetrics(
                examples_count=0,
                avg_length_chars=0,
                avg_length_words=0,
                action_verb_count=0,
                artifact_term_count=0,
                generic_phrase_count=0,
                uniqueness_score=0.0,
                action_verb_density=0.0,
                artifact_density=0.0,
                generic_density=0.0
            )

        total_chars = 0
        total_words = 0
        action_verb_count = 0
        artifact_term_count = 0
        generic_phrase_count = 0

        for example in examples:
            tokens = self._tokenize_words(example)
            total_chars += len(example)
            total_words += len(tokens)
            action_verb_count += sum(1 for t in tokens if t in self.action_verbs)
            artifact_term_count += self._count_phrase_occurrences(example, self.artifact_terms)
            generic_phrase_count += self._count_phrase_occurrences(example, self.generic_phrases)

        count = len(examples)
        avg_words = total_words / count if count > 0 else 0

        return QualityMetrics(
            examples_count=count,
            avg_length_chars=int(round(total_chars / count)),
            avg_length_words=int(round(avg_words)),
            action_verb_count=action_verb_count,
            artifact_term_count=artifact_term_count,
            generic_phrase_count=generic_phrase_count,
            uniqueness_score=self._compute_uniqueness_score(examples),
            # Normalized metrics
            action_verb_density=round((action_verb_count / total_words * 100), 2) if total_words > 0 else 0.0,
            artifact_density=round(artifact_term_count / count, 2) if count > 0 else 0.0,
            generic_density=round(generic_phrase_count / count, 2) if count > 0 else 0.0
        )


ACTION_VERBS = {
    "build", "create", "design", "implement", "lead", "review", "mentor", "write",
    "present", "analyze", "improve", "optimize", "deliver", "launch", "own",
    "coordinate", "document", "automate", "debug", "refactor", "test"
}

ARTIFACT_TERMS = {
    "pr", "pull request", "design doc", "doc", "documentation", "dashboard",
    "postmortem", "incident review", "runbook", "spec", "proposal", "report",
    "roadmap", "meeting", "presentation", "analysis"
}

GENERIC_PHRASES = {
    "shows leadership",
    "drives impact",
    "demonstrates ownership",
    "takes initiative",
    "collaborates effectively",
    "communicates clearly"
}
