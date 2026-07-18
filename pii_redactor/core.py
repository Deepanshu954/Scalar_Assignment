# backward compat facade - everything is in the submodules now

from .cli import build_parser, main
from .docx_redaction_service import DocxRedactionService, DocxRedactor
from .evaluator import RedactionEvaluator
from .indexer import DocxTextIndexer
from .models import EntitySpan, MetricResult, PipelineMode, Replacement, RunSegment, TextUnit
from .recognizers import ConflictResolver, DetectionPipeline, PiiRecognizer, RedactionRules
from .replacement_generator import FakeValueGenerator, ReplacementGenerator
from .scanners import EntropyDetector, ExclusionFilter, NerDetector, PiiScanner, RegexDetector, TieredPipelineScanner
from .utils import luhn_valid, normalize_entity, normalize_space, span_context, stable_index

__all__ = [
    "ConflictResolver",
    "DetectionPipeline",
    "DocxRedactionService",
    "DocxRedactor",
    "DocxTextIndexer",
    "EntitySpan",
    "EntropyDetector",
    "ExclusionFilter",
    "FakeValueGenerator",
    "MetricResult",
    "NerDetector",
    "PipelineMode",
    "PiiRecognizer",
    "PiiScanner",
    "RedactionEvaluator",
    "RedactionRules",
    "RegexDetector",
    "Replacement",
    "ReplacementGenerator",
    "RunSegment",
    "TextUnit",
    "TieredPipelineScanner",
    "build_parser",
    "luhn_valid",
    "main",
    "normalize_entity",
    "normalize_space",
    "span_context",
    "stable_index",
]
