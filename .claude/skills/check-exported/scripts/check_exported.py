#!/usr/bin/env python3
"""
Validate exported markdown files for the Italian Renaissance Art project.

Usage:
    python check_exported.py                    # Check all directories
    python check_exported.py artists            # Check only artists/
    python check_exported.py --json             # JSON output
    python check_exported.py --skip-images      # Skip image URL validation
"""
import os
import re
import json
import argparse
import urllib.request
import urllib.error
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Set
from dataclasses import dataclass, field
from collections import defaultdict


@dataclass
class ValidationResult:
    """Result of validating a single file."""
    filepath: str
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        return len(self.errors) == 0


@dataclass
class DirectoryResult:
    """Aggregated results for a directory."""
    directory: str
    total: int = 0
    valid: int = 0
    error_count: int = 0
    warning_count: int = 0
    file_results: List[ValidationResult] = field(default_factory=list)


class ExportedFileValidator:
    """Validates exported markdown files for structural integrity and cross-references."""

    DIRECTORIES = ['artists', 'artworks', 'locations', 'biblestories']

    def __init__(self, base_path: str, skip_images: bool = False):
        self.base_path = Path(base_path)
        self.skip_images = skip_images
        self.url_cache: Dict[str, bool] = {}

        # Cross-reference maps (populated during validation)
        self.artwork_to_artist: Dict[str, str] = {}  # artwork filename -> artist filename
        self.artwork_to_location: Dict[str, str] = {}  # artwork filename -> location filename
        self.artwork_to_biblestory: Dict[str, Set[str]] = defaultdict(set)  # artwork -> set of bible stories
        self.artist_artworks: Dict[str, Set[str]] = defaultdict(set)  # artist filename -> set of artwork filenames
        self.location_artworks: Dict[str, Set[str]] = defaultdict(set)  # location filename -> set of artwork filenames
        self.biblestory_artworks: Dict[str, Set[str]] = defaultdict(set)  # bible story filename -> set of artwork filenames

    def validate_all(self, directory: Optional[str] = None) -> Dict[str, DirectoryResult]:
        """Validate all files or a specific directory."""
        results: Dict[str, DirectoryResult] = {}

        dirs_to_check = [directory] if directory and directory != 'terms' else self.DIRECTORIES

        # First pass: validate individual files and build cross-reference maps
        for dir_name in dirs_to_check:
            dir_path = self.base_path / dir_name
            if not dir_path.exists():
                continue

            dir_result = DirectoryResult(directory=dir_name)
            md_files = sorted(dir_path.glob('*.md'))
            dir_result.total = len(md_files)

            for filepath in md_files:
                result = self._validate_file(filepath, dir_name)
                dir_result.file_results.append(result)
                if result.is_valid:
                    dir_result.valid += 1
                dir_result.error_count += len(result.errors)
                dir_result.warning_count += len(result.warnings)

            results[dir_name] = dir_result

        # Validate terms.md if checking all or specifically terms
        if directory is None or directory == 'terms':
            terms_result = self._validate_terms()
            if terms_result:
                results['terms'] = DirectoryResult(
                    directory='terms',
                    total=1,
                    valid=1 if terms_result.is_valid else 0,
                    error_count=len(terms_result.errors),
                    warning_count=len(terms_result.warnings),
                    file_results=[terms_result]
                )

        # Second pass: check cross-references
        if directory is None or directory in ['artworks', 'artists', 'locations', 'biblestories']:
            cross_ref_warnings = self._check_cross_references()
            # Add cross-reference warnings to appropriate directories
            for warning in cross_ref_warnings:
                if warning.startswith('artists/'):
                    if 'artists' in results:
                        # Find or create a result for cross-ref issues
                        self._add_crossref_warning(results['artists'], warning)
                elif warning.startswith('locations/'):
                    if 'locations' in results:
                        self._add_crossref_warning(results['locations'], warning)
                elif warning.startswith('biblestories/'):
                    if 'biblestories' in results:
                        self._add_crossref_warning(results['biblestories'], warning)

        return results

    def _add_crossref_warning(self, dir_result: DirectoryResult, warning: str):
        """Add a cross-reference warning to the appropriate file result."""
        # Extract filename from warning
        parts = warning.split(': ', 1)
        if len(parts) == 2:
            filepath = parts[0]
            message = parts[1]
            filename = Path(filepath).name

            # Find the file result
            for result in dir_result.file_results:
                if Path(result.filepath).name == filename:
                    result.warnings.append(message)
                    dir_result.warning_count += 1
                    if result.is_valid:
                        # Still valid (no errors), but now has warnings
                        pass
                    return

    def _validate_file(self, filepath: Path, dir_name: str) -> ValidationResult:
        """Validate a single file based on its directory type."""
        result = ValidationResult(filepath=str(filepath))

        try:
            content = filepath.read_text(encoding='utf-8')
        except Exception as e:
            result.errors.append(f"Cannot read file: {e}")
            return result

        # Common validations
        self._check_h1_heading(content, result)
        self._check_wikipedia_link(content, result)
        self._check_filename_format(filepath, result)
        self._check_images(content, filepath, result)

        # Type-specific validations
        if dir_name == 'artists':
            self._validate_artist(content, filepath, result)
        elif dir_name == 'artworks':
            self._validate_artwork(content, filepath, result)
        elif dir_name == 'locations':
            self._validate_location(content, filepath, result)
        elif dir_name == 'biblestories':
            self._validate_biblestory(content, filepath, result)

        return result

    def _check_h1_heading(self, content: str, result: ValidationResult):
        """Check for H1 heading at start of file."""
        if not re.match(r'^# .+', content):
            result.errors.append("Missing H1 heading")

    def _check_wikipedia_link(self, content: str, result: ValidationResult):
        """Check for Wikipedia link."""
        if not re.search(r'\[Wikipedia\]\(https?://[^\)]+wikipedia[^\)]+\)', content, re.IGNORECASE):
            # Also check for plain Wikipedia URLs
            if not re.search(r'https?://[^\s\)]+wikipedia\.org[^\s\)]*', content):
                result.warnings.append("Missing Wikipedia link")

    def _check_filename_format(self, filepath: Path, result: ValidationResult):
        """Check filename is PascalCase with no special characters."""
        stem = filepath.stem
        # PascalCase: starts with uppercase, no spaces or special chars (except for allowed patterns)
        if not re.match(r'^[A-Z][a-zA-Z0-9]*$', stem):
            # Allow some common patterns like "AndreaDaFirenze" or names with numbers
            if ' ' in stem or any(c in stem for c in '!@#$%^&*()+=[]{}|;:\'",<>?/\\'):
                result.warnings.append(f"Filename should be PascalCase: {stem}")

    def _check_images(self, content: str, filepath: Path, result: ValidationResult):
        """Check all image references."""
        # Find markdown image syntax: ![alt](url)
        image_pattern = r'!\[[^\]]*\]\(([^\)]+)\)'

        for match in re.finditer(image_pattern, content):
            image_url = match.group(1)

            if image_url.startswith('../img/') or image_url.startswith('img/'):
                # Local image
                self._check_local_image(image_url, filepath, result)
            elif image_url.startswith('http://') or image_url.startswith('https://'):
                # External image
                if not self.skip_images:
                    self._check_external_image(image_url, result)

    def _check_local_image(self, image_path: str, source_file: Path, result: ValidationResult):
        """Check if local image file exists."""
        resolved_path = (source_file.parent / image_path).resolve()
        if not resolved_path.exists():
            result.errors.append(f"Local image not found: {image_path}")

    def _check_external_image(self, url: str, result: ValidationResult):
        """Check if external image URL is valid."""
        if url in self.url_cache:
            if not self.url_cache[url]:
                result.warnings.append(f"Image URL invalid: {url[:60]}...")
            return

        try:
            req = urllib.request.Request(url, method='HEAD')
            req.add_header('User-Agent', 'Mozilla/5.0 (compatible; MarkdownValidator/1.0)')
            with urllib.request.urlopen(req, timeout=10) as response:
                self.url_cache[url] = True
        except (urllib.error.URLError, urllib.error.HTTPError, Exception) as e:
            self.url_cache[url] = False
            result.warnings.append(f"Image URL invalid ({type(e).__name__}): {url[:60]}...")

    def _validate_artist(self, content: str, filepath: Path, result: ValidationResult):
        """Validate artist-specific requirements."""
        # Check for Born/Died fields
        if not re.search(r'\*\*Born\*\*:', content) and not re.search(r'Born:', content):
            result.warnings.append("Missing Born field")
        if not re.search(r'\*\*Died\*\*:', content) and not re.search(r'Died:', content):
            result.warnings.append("Missing Died field")

        # Check for ## Artworks section
        if not re.search(r'^## Artworks', content, re.MULTILINE):
            result.errors.append("Missing ## Artworks section")

        # Build cross-reference map: extract artworks listed
        artworks_section = re.search(r'^## Artworks\s*\n(.*?)(?=^## |\Z)', content, re.MULTILINE | re.DOTALL)
        if artworks_section:
            # Find links to artworks: [Name](../artworks/File.md)
            for match in re.finditer(r'\[([^\]]+)\]\(\.\./artworks/([^)]+)\.md\)', artworks_section.group(1)):
                artwork_file = match.group(2) + '.md'
                self.artist_artworks[filepath.stem + '.md'].add(artwork_file)

    def _validate_artwork(self, content: str, filepath: Path, result: ValidationResult):
        """Validate artwork-specific requirements."""
        # Required fields
        required_fields = ['Artist', 'Location', 'Medium', 'Date']
        for field_name in required_fields:
            if not re.search(rf'\*\*{field_name}\*\*:', content):
                result.errors.append(f"Missing required field: {field_name}")

        # Check for ## Description section
        if not re.search(r'^## Description', content, re.MULTILINE):
            result.errors.append("Missing ## Description section")

        # Check Artist link exists
        artist_match = re.search(r'\*\*Artist\*\*:.*?\[([^\]]+)\]\(\.\./artists/([^)]+)\.md\)', content)
        if artist_match:
            artist_file = artist_match.group(2) + '.md'
            artist_path = self.base_path / 'artists' / artist_file
            if not artist_path.exists():
                result.errors.append(f"Artist file not found: {artist_file}")
            else:
                self.artwork_to_artist[filepath.stem + '.md'] = artist_file

        # Check Location link exists
        location_match = re.search(r'\*\*Location\*\*:.*?\[([^\]]+)\]\(\.\./locations/([^)]+)\.md\)', content)
        if location_match:
            location_file = location_match.group(2) + '.md'
            location_path = self.base_path / 'locations' / location_file
            if not location_path.exists():
                result.errors.append(f"Location file not found: {location_file}")
            else:
                self.artwork_to_location[filepath.stem + '.md'] = location_file

        # Check Biblical Context links
        biblical_section = re.search(r'\*\*Biblical Context\*\*:(.*?)(?=\*\*|\n\n|$)', content, re.DOTALL)
        if biblical_section:
            for match in re.finditer(r'\[([^\]]+)\]\(\.\./biblestories/([^)]+)\.md\)', biblical_section.group(1)):
                biblestory_file = match.group(2) + '.md'
                self.artwork_to_biblestory[filepath.stem + '.md'].add(biblestory_file)

    def _validate_location(self, content: str, filepath: Path, result: ValidationResult):
        """Validate location-specific requirements."""
        # Check for GoogleMap link
        if not re.search(r'\[GoogleMap\]\(https?://[^\)]+\)', content) and not re.search(r'google.*maps', content, re.IGNORECASE):
            result.warnings.append("Missing GoogleMap link")

        # Check for City line
        if not re.search(r'\*\*City\*\*:', content) and not re.search(r'^City:', content, re.MULTILINE):
            result.warnings.append("Missing City field")

        # Check for Type field
        if not re.search(r'\*\*Type\*\*:', content):
            result.warnings.append("Missing Type field")

        # Check for ## Artworks section
        if not re.search(r'^## Artworks', content, re.MULTILINE):
            result.errors.append("Missing ## Artworks section")

        # Build cross-reference map: extract artworks listed
        artworks_section = re.search(r'^## Artworks\s*\n(.*?)(?=^## |\Z)', content, re.MULTILINE | re.DOTALL)
        if artworks_section:
            for match in re.finditer(r'\[([^\]]+)\]\(\.\./artworks/([^)]+)\.md\)', artworks_section.group(1)):
                artwork_file = match.group(2) + '.md'
                self.location_artworks[filepath.stem + '.md'].add(artwork_file)

    def _validate_biblestory(self, content: str, filepath: Path, result: ValidationResult):
        """Validate bible story-specific requirements."""
        # Required sections
        required_sections = ['## Summary', '## Biblical Reference', '## Artworks Depicting This Story']
        for section in required_sections:
            if not re.search(rf'^{re.escape(section)}', content, re.MULTILINE):
                result.errors.append(f"Missing {section} section")

        # Build cross-reference map: extract artworks listed
        artworks_section = re.search(r'^## Artworks Depicting This Story\s*\n(.*?)(?=^## |\Z)', content, re.MULTILINE | re.DOTALL)
        if artworks_section:
            for match in re.finditer(r'\[([^\]]+)\]\(\.\./artworks/([^)]+)\.md\)', artworks_section.group(1)):
                artwork_file = match.group(2) + '.md'
                self.biblestory_artworks[filepath.stem + '.md'].add(artwork_file)

    def _validate_terms(self) -> Optional[ValidationResult]:
        """Validate terms.md file."""
        terms_path = self.base_path / 'terms.md'
        if not terms_path.exists():
            return None

        result = ValidationResult(filepath=str(terms_path))

        try:
            content = terms_path.read_text(encoding='utf-8')
        except Exception as e:
            result.errors.append(f"Cannot read file: {e}")
            return result

        # Check for H1 heading
        if not re.match(r'^# .+', content):
            result.errors.append("Missing H1 heading")

        # Check for at least some term definitions (## headings)
        term_count = len(re.findall(r'^## ', content, re.MULTILINE))
        if term_count == 0:
            result.warnings.append("No term definitions found (expected ## headings)")

        return result

    def _check_cross_references(self) -> List[str]:
        """Check bidirectional cross-references."""
        warnings = []

        # Check: artwork->artist means artist should list artwork
        for artwork, artist in self.artwork_to_artist.items():
            if artist in self.artist_artworks:
                if artwork not in self.artist_artworks[artist]:
                    warnings.append(f"artists/{artist}: Missing artwork backlink to {artwork}")
            # If artist file wasn't validated (not in map), skip this check

        # Check: artwork->location means location should list artwork
        for artwork, location in self.artwork_to_location.items():
            if location in self.location_artworks:
                if artwork not in self.location_artworks[location]:
                    warnings.append(f"locations/{location}: Missing artwork backlink to {artwork}")

        # Check: artwork->biblestory means biblestory should list artwork
        for artwork, biblestories in self.artwork_to_biblestory.items():
            for biblestory in biblestories:
                if biblestory in self.biblestory_artworks:
                    if artwork not in self.biblestory_artworks[biblestory]:
                        warnings.append(f"biblestories/{biblestory}: Missing artwork backlink to {artwork}")

        return warnings


def format_human_output(results: Dict[str, DirectoryResult]) -> str:
    """Format results for human-readable output."""
    lines = ["Checking exported files...", ""]

    total_files = 0
    total_errors = 0
    total_warnings = 0

    for dir_name, dir_result in results.items():
        total_files += dir_result.total
        total_errors += dir_result.error_count
        total_warnings += dir_result.warning_count

        if dir_name == 'terms':
            # Special handling for single file
            if dir_result.total == 0:
                lines.append("terms.md: not found")
            elif dir_result.error_count == 0 and dir_result.warning_count == 0:
                lines.append("terms.md: ✓ valid")
            else:
                lines.append(f"terms.md:")
                for fr in dir_result.file_results:
                    for err in fr.errors:
                        lines.append(f"  ✗ {err}")
                    for warn in fr.warnings:
                        lines.append(f"  ⚠ {warn}")
        else:
            lines.append(f"{dir_name}/: {dir_result.total} files")
            lines.append(f"  ✓ {dir_result.valid} valid")

            if dir_result.error_count > 0:
                lines.append(f"  ✗ {dir_result.error_count} errors")
                for fr in dir_result.file_results:
                    for err in fr.errors:
                        lines.append(f"    - {Path(fr.filepath).name}: {err}")

            if dir_result.warning_count > 0:
                lines.append(f"  ⚠ {dir_result.warning_count} warnings")
                for fr in dir_result.file_results:
                    for warn in fr.warnings:
                        lines.append(f"    - {Path(fr.filepath).name}: {warn}")

        lines.append("")

    lines.append(f"Summary: {total_files} files checked, {total_errors} errors, {total_warnings} warnings")

    return "\n".join(lines)


def format_json_output(results: Dict[str, DirectoryResult]) -> str:
    """Format results as JSON."""
    output = {
        "directories": {},
        "summary": {
            "total_files": 0,
            "total_errors": 0,
            "total_warnings": 0
        }
    }

    for dir_name, dir_result in results.items():
        output["summary"]["total_files"] += dir_result.total
        output["summary"]["total_errors"] += dir_result.error_count
        output["summary"]["total_warnings"] += dir_result.warning_count

        dir_output = {
            "total": dir_result.total,
            "valid": dir_result.valid,
            "errors": dir_result.error_count,
            "warnings": dir_result.warning_count,
            "files": []
        }

        for fr in dir_result.file_results:
            if fr.errors or fr.warnings:
                dir_output["files"].append({
                    "filename": Path(fr.filepath).name,
                    "errors": fr.errors,
                    "warnings": fr.warnings
                })

        output["directories"][dir_name] = dir_output

    return json.dumps(output, indent=2)


def main():
    parser = argparse.ArgumentParser(
        description="Validate exported markdown files for the Italian Renaissance Art project."
    )
    parser.add_argument(
        'directory',
        nargs='?',
        choices=['artists', 'artworks', 'locations', 'biblestories', 'terms'],
        help="Specific directory to check (omit for all)"
    )
    parser.add_argument(
        '--json',
        action='store_true',
        help="Output results as JSON"
    )
    parser.add_argument(
        '--skip-images',
        action='store_true',
        help="Skip image URL validation"
    )
    parser.add_argument(
        '--base-path',
        default=None,
        help="Base path to the project (default: auto-detect)"
    )

    args = parser.parse_args()

    # Auto-detect base path
    if args.base_path:
        base_path = Path(args.base_path)
    else:
        # Try to find the project root by looking for known directories
        current = Path.cwd()
        while current != current.parent:
            if (current / 'artists').exists() and (current / 'artworks').exists():
                base_path = current
                break
            # Also check if we're in the site/ subdirectory
            if (current / 'site' / 'artists').exists():
                base_path = current / 'site'
                break
            current = current.parent
        else:
            # Default to current directory
            base_path = Path.cwd()
            # Check if site/ subdirectory exists
            if (base_path / 'site' / 'artists').exists():
                base_path = base_path / 'site'

    validator = ExportedFileValidator(base_path, skip_images=args.skip_images)
    results = validator.validate_all(args.directory)

    if args.json:
        print(format_json_output(results))
    else:
        print(format_human_output(results))

    # Exit with error code if there are errors
    total_errors = sum(r.error_count for r in results.values())
    exit(1 if total_errors > 0 else 0)


if __name__ == '__main__':
    main()
