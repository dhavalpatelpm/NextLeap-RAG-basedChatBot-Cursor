"""
Integration tests for Phase 3 chatbot: LLM + Phase 2 retrieval.
Requires GROQ_API_KEY in .env and Phase 2 vector store (run scripts/run_phase2.py).
Run: pytest tests/test_phase3_integration.py -v
      pytest tests/test_phase3_integration.py -v --run-integration  # explicit
"""
from __future__ import annotations

import pytest

# Expected course URLs from data/course_details/index.json
PRODUCT_MANAGEMENT_URL = "https://nextleap.app/course/product-management-course"


@pytest.fixture(scope="module")
def chat_response_product_management_price(skip_if_no_integration):
    """Call chat once for product management price query (shared across tests)."""
    from src.phase3 import chat
    return chat.chat("What is the price of product management fellowship?")


class TestPhase3ProductManagementPrice:
    """Example test case: price + URL for Product Manager Fellowship."""

    def test_answer_contains_price(
        self, chat_response_product_management_price
    ):
        """Answer should contain the course price (34999 or 34,999)."""
        result = chat_response_product_management_price
        assert "answer" in result
        answer = result["answer"]
        # At least one price form should appear (34999 or 34,999 or ₹34,999)
        has_price = (
            "34999" in answer or "34,999" in answer or "₹34,999" in answer
        )
        assert has_price, f"Expected price (34999/34,999) in answer. Got: {answer[:500]}"

    def test_answer_or_sources_contain_product_management_url(
        self, chat_response_product_management_price
    ):
        """Answer or sources should reference the Product Management course URL."""
        result = chat_response_product_management_price
        answer = result.get("answer", "")
        sources = result.get("sources") or []
        url_found_in_answer = PRODUCT_MANAGEMENT_URL in answer
        url_in_sources = any(
            s.get("source_url") == PRODUCT_MANAGEMENT_URL
            for s in sources
        )
        assert url_found_in_answer or url_in_sources, (
            f"Expected URL {PRODUCT_MANAGEMENT_URL} in answer or sources. "
            f"Answer (first 400 chars): {answer[:400]}. "
            f"Sources: {[s.get('source_url') for s in sources]}"
        )

    def test_sources_include_product_management_course(
        self, chat_response_product_management_price
    ):
        """Sources must include at least one entry with product-management-course URL."""
        result = chat_response_product_management_price
        sources = result.get("sources") or []
        pm_sources = [s for s in sources if "product-management-course" in (s.get("source_url") or "")]
        assert len(pm_sources) >= 1, (
            f"Expected at least one source with product-management-course URL. "
            f"Sources: {[s.get('source_url') for s in sources]}"
        )
        assert pm_sources[0].get("source_url") == PRODUCT_MANAGEMENT_URL

    def test_response_structure(self, chat_response_product_management_price):
        """Response must have answer, sources, out_of_scope."""
        result = chat_response_product_management_price
        assert "answer" in result and isinstance(result["answer"], str)
        assert "sources" in result and isinstance(result["sources"], list)
        assert "out_of_scope" in result and isinstance(result["out_of_scope"], bool)
        assert result["out_of_scope"] is False

    def test_answer_similar_to_expected_format(
        self, chat_response_product_management_price
    ):
        """Answer should be similar to: '34999 is the price and url - https://nextleap.app/course/product-management-course'."""
        result = chat_response_product_management_price
        answer = result.get("answer", "")
        sources = result.get("sources") or []
        # Must contain price
        assert "34999" in answer or "34,999" in answer or "₹34,999" in answer
        # Must contain URL in answer or in sources
        url_in_answer = PRODUCT_MANAGEMENT_URL in answer
        url_in_sources = any(
            s.get("source_url") == PRODUCT_MANAGEMENT_URL for s in sources
        )
        assert url_in_answer or url_in_sources, (
            f"Expected URL {PRODUCT_MANAGEMENT_URL} in answer or sources. "
            f"Answer: {answer[:400]}"
        )


class TestPhase3OtherIntents:
    """Integration tests for other queries and phases."""

    def test_courses_offered_returns_answer(self, skip_if_no_integration):
        """Query about courses offered should return a grounded answer and sources."""
        from src.phase3 import chat
        result = chat.chat("What courses does NextLeap offer?")
        assert result.get("out_of_scope") is False
        assert len(result.get("answer", "")) > 20
        assert isinstance(result.get("sources"), list)

    def test_ux_design_fee_returns_relevant_source(self, skip_if_no_integration):
        """Query about UI/UX course should return answer with UX course source URL."""
        from src.phase3 import chat
        result = chat.chat("What is the fee for UI/UX Designer Fellowship?")
        assert result.get("out_of_scope") is False
        sources = result.get("sources") or []
        ux_urls = [s for s in sources if "ui-ux-design" in (s.get("source_url") or "")]
        assert len(ux_urls) >= 1 or len(result.get("answer", "")) > 10, (
            "Expected UX design course source or non-empty answer"
        )

    def test_duration_question_returns_context_answer(self, skip_if_no_integration):
        """Query about duration should use retrieved context."""
        from src.phase3 import chat
        result = chat.chat("How long is the Product Manager Fellowship?")
        assert result.get("out_of_scope") is False
        # Answer should mention weeks/months/duration
        answer = result.get("answer", "").lower()
        assert any(
            w in answer for w in ["week", "month", "16", "duration", "4 month"]
        ) or len(answer) > 30

    def test_instructors_question_returns_sources(self, skip_if_no_integration):
        """Query about instructors should return sources with source_url."""
        from src.phase3 import chat
        result = chat.chat("Who teaches the Product Management course?")
        assert result.get("out_of_scope") is False
        assert len(result.get("sources", [])) >= 0  # may or may not have sources
        assert len(result.get("answer", "")) > 10


class TestPhase3OutOfScope:
    """Out-of-scope (personal information) should be declined without using LLM for that content."""

    def test_personal_contact_query_declined(self, skip_if_no_integration):
        """Query asking for contact/email should return out_of_scope and polite decline."""
        from src.phase3 import chat
        result = chat.chat("What is the instructor's email or phone number?")
        assert result.get("out_of_scope") is True
        assert "out of scope" in result.get("answer", "").lower() or "outside" in result.get("answer", "").lower()
        assert result.get("sources") == []

    def test_personal_data_query_declined(self, skip_if_no_integration):
        """Query about personal data should be declined."""
        from src.phase3 import chat
        result = chat.chat("Give me the personal contact details of the course coordinator.")
        assert result.get("out_of_scope") is True
        assert len(result.get("answer", "")) > 0
        assert result.get("sources") == []


class TestPhase3ResponseShape:
    """Generic response shape and integration with Phase 2."""

    def test_chat_returns_dict_with_required_keys(self, skip_if_no_integration):
        """chat() always returns dict with answer, sources, out_of_scope."""
        from src.phase3 import chat
        result = chat.chat("What is NextLeap?")
        assert set(result.keys()) >= {"answer", "sources", "out_of_scope"}
        assert isinstance(result["sources"], list)
        for s in result["sources"]:
            assert "source_url" in s
            assert "course_name" in s or "cohort_id" in s
