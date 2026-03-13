"""
Transcript ingestion and preprocessing
"""
import os
import re
import logging
from pathlib import Path
from typing import List, Union

logger = logging.getLogger(__name__)


class TranscriptProcessor:
    """Handles loading and preprocessing of transcript files"""

    def __init__(self):
        self.supported_formats = ['.txt', '.md', '.docx', '.pdf']

    async def load_transcript_file(self, file_path: Union[str, Path]) -> str:
        """Load a single transcript file"""

        file_path = Path(file_path)

        if not file_path.exists():
            raise FileNotFoundError(f"Transcript file not found: {file_path}")

        if file_path.suffix.lower() not in self.supported_formats:
            raise ValueError(f"Unsupported file format: {file_path.suffix}")

        logger.info(f"Loading transcript: {file_path.name}")

        if file_path.suffix.lower() == '.txt':
            return await self._load_text_file(file_path)
        elif file_path.suffix.lower() == '.md':
            return await self._load_markdown_file(file_path)
        elif file_path.suffix.lower() == '.docx':
            return await self._load_docx_file(file_path)
        elif file_path.suffix.lower() == '.pdf':
            return await self._load_pdf_file(file_path)
        else:
            raise ValueError(f"Handler not implemented for {file_path.suffix}")

    async def _load_text_file(self, file_path: Path) -> str:
        """Load plain text file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            return content
        except UnicodeDecodeError:
            # Try with different encoding
            with open(file_path, 'r', encoding='latin-1') as f:
                content = f.read()
            return content

    async def _load_markdown_file(self, file_path: Path) -> str:
        """Load markdown file"""
        return await self._load_text_file(file_path)

    async def _load_docx_file(self, file_path: Path) -> str:
        """Load Word document"""
        try:
            from docx import Document
            doc = Document(file_path)
            full_text = []
            for para in doc.paragraphs:
                full_text.append(para.text)
            return '\\n'.join(full_text)
        except ImportError:
            raise ImportError("python-docx package required for .docx files")

    async def _load_pdf_file(self, file_path: Path) -> str:
        """Load PDF file"""
        try:
            import PyPDF2
            with open(file_path, 'rb') as f:
                pdf_reader = PyPDF2.PdfReader(f)
                text = []
                for page in pdf_reader.pages:
                    text.append(page.extract_text())
                return '\\n'.join(text)
        except ImportError:
            raise ImportError("PyPDF2 package required for .pdf files")

    async def preprocess_transcripts(self, raw_transcripts: List[str]) -> str:
        """Clean and combine multiple transcript contents"""

        logger.info(f"Preprocessing {len(raw_transcripts)} transcripts")

        processed_transcripts = []

        for i, transcript in enumerate(raw_transcripts):
            cleaned = await self._clean_transcript_content(transcript)

            # Add source markers
            processed = f"\\n\\n=== TRANSCRIPT {i+1} ===\\n{cleaned}\\n=== END TRANSCRIPT {i+1} ===\\n"
            processed_transcripts.append(processed)

        # Combine all transcripts
        combined = "\\n\\n".join(processed_transcripts)

        logger.info(f"Preprocessed transcript length: {len(combined)} characters")
        return combined

    async def _clean_transcript_content(self, content: str) -> str:
        """Clean individual transcript content"""

        # Remove excessive whitespace
        content = re.sub(r'\\n\\s*\\n', '\\n\\n', content)
        content = re.sub(r'[ \\t]+', ' ', content)

        # Remove common transcript artifacts
        content = re.sub(r'\\[inaudible\\]', '[INAUDIBLE]', content, flags=re.IGNORECASE)
        content = re.sub(r'\\[crosstalk\\]', '[CROSSTALK]', content, flags=re.IGNORECASE)
        content = re.sub(r'\\[silence\\]', '[SILENCE]', content, flags=re.IGNORECASE)

        # Clean speaker labels (e.g., "Speaker 1:", "John:", etc.)
        content = re.sub(r'^(Speaker \\d+|[A-Z][a-z]+ [A-Z][a-z]+|[A-Z][a-z]+):\\s*',
                        r'\\1: ', content, flags=re.MULTILINE)

        # Remove timestamps (various formats)
        content = re.sub(r'\\[?\\d{1,2}:\\d{2}(:\\d{2})?\\]?', '', content)
        content = re.sub(r'\\(\\d{1,2}:\\d{2}(:\\d{2})?\\)', '', content)

        # Remove excessive punctuation
        content = re.sub(r'[.]{3,}', '...', content)
        content = re.sub(r'[-]{3,}', '---', content)

        # Fix common speech-to-text errors (you can expand this)
        content = re.sub(r'\\buh\\b', '', content, flags=re.IGNORECASE)
        content = re.sub(r'\\bum\\b', '', content, flags=re.IGNORECASE)
        content = re.sub(r'\\ber\\b', '', content, flags=re.IGNORECASE)

        # Clean up any double spaces created
        content = re.sub(r' +', ' ', content)

        return content.strip()

    def extract_speakers(self, content: str) -> List[str]:
        """Extract unique speaker names from transcript"""

        # Find speaker patterns
        speaker_pattern = r'^([A-Z][a-z]+ ?[A-Z]?[a-z]*|Speaker \\d+):'
        speakers = set()

        for match in re.finditer(speaker_pattern, content, re.MULTILINE):
            speaker = match.group(1).strip()
            speakers.add(speaker)

        return sorted(list(speakers))

    def get_transcript_stats(self, content: str) -> dict:
        """Get basic statistics about the transcript"""

        lines = content.split('\\n')
        words = content.split()
        speakers = self.extract_speakers(content)

        return {
            "total_lines": len(lines),
            "total_words": len(words),
            "total_characters": len(content),
            "unique_speakers": len(speakers),
            "speaker_names": speakers,
            "estimated_minutes": len(words) // 150  # Rough estimate: 150 words/minute
        }