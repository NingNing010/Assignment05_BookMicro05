import json
import os
from typing import Dict, List


DEFAULT_KB_DOCS = [
    {
        "id": "policy-01",
        "title": "Chiến lược giải quyết khách hàng không hài lòng",
        "content": "Nếu khách hàng có dấu hiệu không hài lòng, ưu tiên xin lỗi, gửi voucher nhỏ 10-15%, và gợi ý sách đúng thể loại khách đã tương tác.",
        "tags": ["retention", "service", "negative"],
    },
    {
        "id": "policy-02",
        "title": "Chiến lược tăng giá trị đơn hàng",
        "content": "Với khách trung lập ở mức trung tính, đề xuất combo 2-3 sách cùng chủ đề, khuyến khích review sau mua, và gợi ý sách top-rated.",
        "tags": ["upsell", "cross-sell", "neutral"],
    },
    {
        "id": "policy-03",
        "title": "Chương trình chăm sóc khách trung thành",
        "content": "Với khách trung thành, áp dụng VIP tier, ưu tiên pre-order, quyền tiếp cận bộ sưu tập mới sớm, và referral bonus.",
        "tags": ["vip", "loyalty", "positive"],
    },
    {
        "id": "policy-04",
        "title": "Gợi ý nguyên tắc tư vấn dựa trên review",
        "content": "Nếu khách đánh giá thấp liên tiếp, ưu tiên tìm nguyên nhân về chất lượng nội dung hoặc giá. Nếu đánh giá cao và ổn định, ưu tiên mở rộng danh mục gợi ý.",
        "tags": ["review", "advisor", "behavior"],
    },
]


class KnowledgeBaseManager:
    def __init__(self):
        base_dir = os.path.dirname(os.path.dirname(__file__))
        self.kb_dir = os.path.join(base_dir, "kb")
        os.makedirs(self.kb_dir, exist_ok=True)
        self.kb_file = os.path.join(self.kb_dir, "behavior_advisory_kb.json")

    def ensure_seeded(self) -> None:
        if os.path.exists(self.kb_file):
            return
        with open(self.kb_file, "w", encoding="utf-8") as f:
            json.dump(DEFAULT_KB_DOCS, f, ensure_ascii=True, indent=2)

    def load_documents(self) -> List[Dict]:
        self.ensure_seeded()
        with open(self.kb_file, "r", encoding="utf-8") as f:
            docs = json.load(f)
        if not isinstance(docs, list):
            return []
        return docs

    def rebuild(self, extra_docs: List[Dict]) -> Dict:
        self.ensure_seeded()
        merged = []
        seen = set()
        for doc in DEFAULT_KB_DOCS + (extra_docs or []):
            doc_id = str(doc.get("id") or "")
            if not doc_id or doc_id in seen:
                continue
            seen.add(doc_id)
            merged.append(
                {
                    "id": doc_id,
                    "title": str(doc.get("title") or "No title"),
                    "content": str(doc.get("content") or ""),
                    "tags": list(doc.get("tags") or []),
                }
            )
        with open(self.kb_file, "w", encoding="utf-8") as f:
            json.dump(merged, f, ensure_ascii=True, indent=2)
        return {
            "kb_file": self.kb_file,
            "documents": len(merged),
            "message": "Knowledge Base đã được cập nhật.",
        }
