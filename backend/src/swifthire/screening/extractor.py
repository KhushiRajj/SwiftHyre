from __future__ import annotations

import re


class ExtractionError(RuntimeError):
    pass


class ResumeExtractor:
    def extract(self, pdf_bytes: bytes) -> str:
        if not pdf_bytes:
            raise ExtractionError('PDF is empty')
        text = pdf_bytes.decode('latin-1', errors='ignore')
        if 'Encrypt' in text or '/Encrypt' in text:
            raise ExtractionError('PDF is encrypted and cannot be read')
        matches = re.findall(r'\((.*?)\)\s*Tj', text, flags=re.DOTALL)
        if not matches:
            return text.strip()
        return ''.join(matches)
