import unicodedata
from typing import Dict, List, Optional

from .knowledge_base import KnowledgeBaseManager
from .model_behavior import BehaviorModelService

try:
    from sklearn.feature_extraction.text import TfidfVectorizer
except Exception:  # pragma: no cover
    TfidfVectorizer = None


class BehaviorRAGAdvisor:
    def __init__(self):
        self.kb = KnowledgeBaseManager()
        self.behavior = BehaviorModelService()

    @staticmethod
    def _normalize_text(text: str) -> str:
        text = unicodedata.normalize("NFKD", text or "")
        text = "".join(ch for ch in text if not unicodedata.combining(ch))
        return text.lower()

    @staticmethod
    def _build_dynamic_docs(reviews, customer_id: Optional[int]) -> List[Dict]:
        docs: List[Dict] = []

        # Global summary from reviews
        all_reviews = list(reviews)
        if all_reviews:
            avg_rating = sum(float(r.rating or 0) for r in all_reviews) / len(all_reviews)
            docs.append(
                {
                    "id": "dynamic-global-reviews",
                    "title": "Tổng quan review hệ thống",
                    "content": f"Tổng số review: {len(all_reviews)}. Điểm trung bình toàn hệ thống: {avg_rating:.2f}.",
                    "tags": ["dynamic", "reviews", "global"],
                }
            )

        # Customer-specific summary
        if customer_id is not None:
            customer_reviews = [r for r in all_reviews if int(r.customer_id) == int(customer_id)]
            if customer_reviews:
                avg_rating_c = sum(float(r.rating or 0) for r in customer_reviews) / len(customer_reviews)
                avg_len = sum(len((r.comment or "").strip()) for r in customer_reviews) / len(customer_reviews)
                docs.append(
                    {
                        "id": f"dynamic-customer-{customer_id}",
                        "title": f"Tóm tắt hành vi customer {customer_id}",
                        "content": (
                            f"Customer {customer_id} có {len(customer_reviews)} review, "
                            f"điểm trung bình {avg_rating_c:.2f}, độ dài comment trung bình {avg_len:.1f} ký tự."
                        ),
                        "tags": ["dynamic", "customer", "behavior"],
                    }
                )
        return docs

    @staticmethod
    def _retrieve(question: str, docs: List[Dict], top_k: int = 4) -> List[Dict]:
        if not docs:
            return []

        if TfidfVectorizer is None:
            q = (question or "").lower().split()
            scored = []
            for d in docs:
                txt = f"{d.get('title', '')} {d.get('content', '')}".lower()
                score = sum(1 for token in q if token in txt)
                scored.append((score, d))
            scored.sort(key=lambda x: x[0], reverse=True)
            return [x[1] for x in scored[:top_k]]

        corpus = [f"{d.get('title', '')}. {d.get('content', '')}" for d in docs]
        vectorizer = TfidfVectorizer(ngram_range=(1, 2), max_features=1500)
        matrix = vectorizer.fit_transform(corpus)
        q_vec = vectorizer.transform([question or ""])
        scores = (matrix @ q_vec.T).toarray().ravel()
        ranked = sorted(enumerate(scores), key=lambda x: x[1], reverse=True)
        return [docs[i] for i, _ in ranked[:top_k]]

    @staticmethod
    def _generate_answer(question: str, retrieved_docs: List[Dict], behavior_context: Optional[Dict]) -> str:
        question_lc = BehaviorRAGAdvisor._normalize_text(question or "")

        complaint_keywords = [
            "ghet",
            "that vong",
            "khong hai long",
            "bo di",
            "roi bo",
            "te",
            "xau",
            "uc che",
            "khong thich",
            "phuc tap",
            "loi",
        ]
        purchase_keywords = [
            "mua",
            "sach",
            "goi y",
            "de xuat",
            "nen chon",
            "chon gi",
            "gioi thieu",
            "tu van mua",
        ]
        positive_keywords = [
            "thich",
            "hay",
            "tuyet",
            "hai long",
            "yeu",
            "rat tot",
            "on",
        ]

        is_complaint = any(k in question_lc for k in complaint_keywords)
        is_buy_intent = any(k in question_lc for k in purchase_keywords)
        is_positive = any(k in question_lc for k in positive_keywords)

        if behavior_context and behavior_context.get("found"):
            segment = (behavior_context.get("segment") or "").strip()
            advice_list = behavior_context.get("service_advice", [])

            if advice_list:
                concise_advice = "; ".join(str(item).strip(" -.*\n\t") for item in advice_list[:2])
            else:
                concise_advice = "ưu tiên chăm sóc theo hành vi gần đây"

            if is_complaint or segment == "dissatisfaction_risk":
                if is_buy_intent:
                    return (
                        "Khách đang có cảm xúc tiêu cực với cuốn sách này, nên ưu tiên xin lỗi, ghi nhận góp ý và đề xuất một lựa chọn an toàn hơn. "
                        f"Gợi ý cụ thể: {concise_advice}."
                    )
                return (
                    "Khách này đang không hài lòng. Nên xin lỗi chủ động, giải thích ngắn gọn và đưa ra phương án hỗ trợ ngay. "
                    f"Cụ thể: {concise_advice}."
                )

            if is_buy_intent:
                if segment == "loyal_positive" or is_positive:
                    return (
                        "Khách này phù hợp gợi ý sách cùng chủ đề hoặc bản mới nổi bật. "
                        f"Đề xuất cụ thể: {concise_advice}."
                    )
                if segment == "neutral":
                    return (
                        "Khách này đang cần gợi ý mua sách, nên chọn 1-2 tựa dễ đọc, top-rated và có thể mua kèm combo nhỏ. "
                        f"Đề xuất cụ thể: {concise_advice}."
                    )
                return (
                    "Khách này có xu hướng trung thành. Nên đẩy mạnh VIP/pre-order và đề xuất bộ sách liên quan, "
                    f"cụ thể: {concise_advice}."
                )

            if is_positive or segment == "loyal_positive":
                return (
                    "Khách này đang phản hồi tích cực, có thể ghi nhận cảm xúc tốt và gợi ý thêm sách cùng chủ đề để tăng giá trị đơn hàng. "
                    f"Đề xuất: {concise_advice}."
                )

            if question_lc.strip():
                return (
                    "Tư vấn ngắn gọn: nên ưu tiên câu trả lời bám sát nhu cầu hiện tại của khách và giữ giọng điệu thân thiện, rõ ràng. "
                    f"Gợi ý: {concise_advice}."
                )

            return f"Tư vấn cho khách này: {concise_advice}."

        if retrieved_docs:
            top_doc = retrieved_docs[0]
            return f"{top_doc.get('content', 'Nên ưu tiên chăm sóc khách hàng dựa trên lịch sử đánh giá.')}"

        return "Bạn nên cung cấp thêm mã khách hàng để hệ thống đưa ra tư vấn chính xác hơn."

    def ask(self, question: str, reviews, customer_id: Optional[int] = None) -> Dict:
        if not question:
            return {"error": "question là bắt buộc"}

        review_items = list(reviews)
        kb_docs = self.kb.load_documents()
        dynamic_docs = self._build_dynamic_docs(reviews=review_items, customer_id=customer_id)
        graph = self.kb.build_behavior_graph(review_items)
        graph_docs = self.kb.graph_to_documents(graph)
        all_docs = kb_docs + dynamic_docs + graph_docs
        retrieved = self._retrieve(question=question, docs=all_docs, top_k=4)

        behavior_context = None
        if customer_id is not None:
            try:
                behavior_context = self.behavior.predict_customer(customer_id=customer_id, reviews=review_items)
            except Exception as exc:
                behavior_context = {"found": False, "message": str(exc)}

        answer = self._generate_answer(question=question, retrieved_docs=retrieved, behavior_context=behavior_context)

        return {
            "question": question,
            "customer_id": customer_id,
            "answer": answer,
            "retrieved_chunks": [
                {
                    "id": d.get("id"),
                    "title": d.get("title"),
                    "content": d.get("content"),
                }
                for d in retrieved
            ],
            "behavior_context": behavior_context,
            "graph_meta": graph.get("meta", {}),
            "model": "RAG-TFIDF+model_behavior",
        }
