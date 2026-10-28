import pytest

from swifthire.screening.extractor import ExtractionError, ResumeExtractor
from swifthire.screening.matcher import ResumeMatcher
from swifthire.screening.schemas import CriterionResult, MatchResult


def test_resume_extraction_and_match_schema_validation():
    extractor = ResumeExtractor()
    text_pdf = b'%PDF-1.4\nBT\n/F1 12 Tf\n(John Doe) Tj\n(Lead Product Designer) Tj\nET\n%%EOF'
    assert extractor.extract(text_pdf) == 'John DoeLead Product Designer'

    encrypted_pdf = b'%PDF-1.4\n<< /Encrypt 42 0 R >>\n%%EOF'
    with pytest.raises(ExtractionError):
        extractor.extract(encrypted_pdf)

    valid = MatchResult(
        score=84,
        criteria=[CriterionResult(name='Product leadership', score=84, evidence='Led roadmap planning', reason='Strong strategic fit')],
        summary='Strong fit for the role.',
    )
    assert valid.score == 84
    assert valid.criteria[0].name == 'Product leadership'

    with pytest.raises(ValueError):
        MatchResult(
            score=101,
            criteria=[CriterionResult(name='Product leadership', score=84, evidence='Led roadmap planning', reason='Strong strategic fit')],
            summary='Too high.',
        )

    class FailingProvider:
        def complete(self, *args, **kwargs):
            raise TimeoutError('provider timed out')

    matcher = ResumeMatcher(provider=FailingProvider())
    result = matcher.match('Design product experiences', 'John Doe was a product leader.')
    assert result.status == 'screening_failed'
    assert result.score is None
    assert 'retry' in result.summary.lower()
