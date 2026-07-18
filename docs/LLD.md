# Low Level Design (LLD)

## 1. Module Structure

The application logic is broken down into focused modules under `pii_redactor/`:

- `cli.py`: Command-line interface parsing and execution entry point.
- `docx_redaction_service.py`: Application layer coordinating indexing, scanning, and mutation.
- `detection_pipeline.py`: Implements `TieredPipelineScanner`, iterating over registered scanners.
- `structured_recognizers.py`: Implements `RegexDetector`. Uses regex bounds and validation functions (e.g., `luhn_valid` for Credit Cards).
- `context_recognizers.py`: Implements `NerDetector`. Looks for surrounding cue phrases (like "Director:") to find capitalized names.
- `entropy_recognizer.py`: Implements `EntropyDetector`. Scans alphanumeric blocks and calculates Shannon entropy.
- `conflict_resolver.py`: Handles overlapping bounding boxes (e.g., an Email matched inside a larger URL span) by prioritizing longer spans or higher-priority entity types.
- `exclusion_filter.py`: Checks detected spans against configured sets of public organizations and stop words to drop false positives.
- `replacement_generator.py`: Generates fake data using a `stable_index` derived from `hashlib.sha256`.

## 2. Core Data Models (`models.py`)

- **`EntitySpan`**: A dataclass tracking the location and type of a detection.
  - Fields: `entity_type`, `text`, `start`, `end`, `confidence`, `detector`, `context`, `unit_id`, `part`.
- **`TextUnit`**: Represents a block of text (paragraph or table cell) and its constituent run segments.
  - Fields: `id`, `part`, `text`, `run_segments` (list of `RunSegment`).
- **`Replacement`**: Tracks the mapping between an original value and its fake replacement.
  - Fields: `original`, `entity_type`, `fake_value`.

## 3. Control Flow (Redaction Sequence)

1. `DocxRedactionService.redact_docx()` receives file paths.
2. `DocxTextIndexer.index()` returns a list of `TextUnit` objects.
3. For each `TextUnit`:
   - `TieredPipelineScanner.scan_text()` is called.
   - Internal scanners (`RegexDetector`, `EntropyDetector`, `NerDetector`) yield candidate `EntitySpan` objects.
   - `ConflictResolver` prunes overlapping spans.
4. `SpanPropagator` takes exact matches and searches the rest of the document (e.g., finding "John Doe" everywhere if identified once).
5. `ExclusionFilter` removes spans hitting the allow-list.
6. `ReplacementGenerator` maps each surviving `EntitySpan` to a `Replacement`.
7. `RunLevelReplacer` calculates string offsets relative to XML runs and injects fake strings.
8. `Document.save()` writes the mutated XML to the `.docx` archive.

## 4. Extension Points
To add a new PII type (e.g., Vehicle Registration):
1. Create a class implementing `PiiScanner` (or add a regex to `RegexDetector`).
2. Add the fake value strategy to `FakeValueStrategy`.
3. Register the new scanner in `TieredPipelineScanner`.
