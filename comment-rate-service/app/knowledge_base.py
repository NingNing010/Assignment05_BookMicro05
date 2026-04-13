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
        self.graph_file = os.path.join(self.kb_dir, "behavior_graph_kb.json")

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

    @staticmethod
    def _sentiment_from_rating(rating: float) -> str:
        if rating >= 4:
            return "positive"
        if rating <= 2:
            return "negative"
        return "neutral"

    @staticmethod
    def _segment_from_avg_rating(avg_rating: float) -> str:
        if avg_rating <= 2.8:
            return "dissatisfaction_risk"
        if avg_rating >= 4.0:
            return "loyal_positive"
        return "neutral"

    def build_behavior_graph(self, reviews) -> Dict:
        review_items = list(reviews)

        customer_stats: Dict[int, Dict] = {}
        product_stats: Dict[int, Dict] = {}
        customer_product_stats: Dict[tuple, Dict] = {}

        for item in review_items:
            customer_id = int(item.customer_id)
            product_id = int(item.book_id)
            rating = float(item.rating or 0)
            comment = (item.comment or "").strip()
            sentiment = self._sentiment_from_rating(rating)

            c_stat = customer_stats.setdefault(
                customer_id,
                {
                    "count": 0,
                    "rating_sum": 0.0,
                    "positive": 0,
                    "neutral": 0,
                    "negative": 0,
                    "comment_len_sum": 0,
                },
            )
            c_stat["count"] += 1
            c_stat["rating_sum"] += rating
            c_stat[sentiment] += 1
            c_stat["comment_len_sum"] += len(comment)

            p_stat = product_stats.setdefault(
                product_id,
                {
                    "count": 0,
                    "rating_sum": 0.0,
                    "positive": 0,
                    "neutral": 0,
                    "negative": 0,
                },
            )
            p_stat["count"] += 1
            p_stat["rating_sum"] += rating
            p_stat[sentiment] += 1

            cp_key = (customer_id, product_id)
            cp_stat = customer_product_stats.setdefault(
                cp_key,
                {
                    "count": 0,
                    "rating_sum": 0.0,
                    "last_rating": rating,
                    "positive": 0,
                    "neutral": 0,
                    "negative": 0,
                },
            )
            cp_stat["count"] += 1
            cp_stat["rating_sum"] += rating
            cp_stat["last_rating"] = rating
            cp_stat[sentiment] += 1

        nodes: List[Dict] = []
        edges: List[Dict] = []

        segment_set = set()
        for customer_id, stat in customer_stats.items():
            avg_rating = stat["rating_sum"] / stat["count"] if stat["count"] else 0.0
            avg_comment_len = stat["comment_len_sum"] / stat["count"] if stat["count"] else 0.0
            dominant_sentiment = max(
                ["positive", "neutral", "negative"],
                key=lambda s: stat.get(s, 0),
            )
            segment = self._segment_from_avg_rating(avg_rating)
            segment_set.add(segment)

            nodes.append(
                {
                    "id": f"customer:{customer_id}",
                    "type": "customer",
                    "label": f"Customer #{customer_id}",
                    "attributes": {
                        "customer_id": customer_id,
                        "review_count": stat["count"],
                        "avg_rating": round(avg_rating, 4),
                        "avg_comment_len": round(avg_comment_len, 2),
                        "dominant_sentiment": dominant_sentiment,
                    },
                }
            )
            edges.append(
                {
                    "source": f"customer:{customer_id}",
                    "target": f"segment:{segment}",
                    "type": "belongs_to_segment",
                    "weight": round(avg_rating, 4),
                }
            )

        for product_id, stat in product_stats.items():
            avg_rating = stat["rating_sum"] / stat["count"] if stat["count"] else 0.0
            nodes.append(
                {
                    "id": f"product:{product_id}",
                    "type": "product",
                    "label": f"Product #{product_id}",
                    "attributes": {
                        "product_id": product_id,
                        "review_count": stat["count"],
                        "avg_rating": round(avg_rating, 4),
                        "positive": stat["positive"],
                        "neutral": stat["neutral"],
                        "negative": stat["negative"],
                    },
                }
            )

        for segment in sorted(segment_set):
            nodes.append(
                {
                    "id": f"segment:{segment}",
                    "type": "segment",
                    "label": segment,
                    "attributes": {},
                }
            )

        for (customer_id, product_id), stat in customer_product_stats.items():
            avg_rating = stat["rating_sum"] / stat["count"] if stat["count"] else 0.0
            edges.append(
                {
                    "source": f"customer:{customer_id}",
                    "target": f"product:{product_id}",
                    "type": "reviewed",
                    "weight": stat["count"],
                    "attributes": {
                        "review_count": stat["count"],
                        "avg_rating": round(avg_rating, 4),
                        "last_rating": round(float(stat["last_rating"]), 4),
                        "positive": stat["positive"],
                        "neutral": stat["neutral"],
                        "negative": stat["negative"],
                    },
                }
            )

        total_reviews = len(review_items)
        avg_rating_all = (
            round(sum(float(item.rating or 0) for item in review_items) / total_reviews, 4)
            if total_reviews
            else 0.0
        )

        graph = {
            "meta": {
                "description": "Behavior knowledge graph built from review database",
                "total_reviews": total_reviews,
                "avg_rating": avg_rating_all,
                "customer_nodes": len(customer_stats),
                "product_nodes": len(product_stats),
                "segment_nodes": len(segment_set),
                "edge_count": len(edges),
            },
            "nodes": nodes,
            "edges": edges,
        }
        return graph

    def save_behavior_graph(self, reviews) -> Dict:
        graph = self.build_behavior_graph(reviews)
        with open(self.graph_file, "w", encoding="utf-8") as f:
            json.dump(graph, f, ensure_ascii=True, indent=2)
        return {
            "graph_file": self.graph_file,
            "meta": graph.get("meta", {}),
            "message": "Behavior knowledge graph has been rebuilt.",
        }

    def load_behavior_graph(self) -> Dict:
        if not os.path.exists(self.graph_file):
            return {}
        with open(self.graph_file, "r", encoding="utf-8") as f:
            graph = json.load(f)
        return graph if isinstance(graph, dict) else {}

    def graph_to_documents(self, graph: Dict, max_docs: int = 8) -> List[Dict]:
        nodes = list(graph.get("nodes") or [])
        edges = list(graph.get("edges") or [])
        meta = graph.get("meta") or {}
        if not nodes:
            return []

        docs: List[Dict] = [
            {
                "id": "graph-summary",
                "title": "Tổng quan behavior graph",
                "content": (
                    f"Graph có {meta.get('customer_nodes', 0)} khách hàng, "
                    f"{meta.get('product_nodes', 0)} sản phẩm, "
                    f"{meta.get('edge_count', len(edges))} liên kết và "
                    f"điểm trung bình {meta.get('avg_rating', 0)}."
                ),
                "tags": ["graph", "summary", "behavior"],
            }
        ]

        customer_nodes = [n for n in nodes if n.get("type") == "customer"]
        customer_nodes.sort(
            key=lambda n: float((n.get("attributes") or {}).get("review_count", 0)),
            reverse=True,
        )
        for node in customer_nodes[: max(0, max_docs - 1)]:
            attrs = node.get("attributes") or {}
            customer_id = attrs.get("customer_id")
            docs.append(
                {
                    "id": f"graph-customer-{customer_id}",
                    "title": f"Hành vi khách hàng #{customer_id}",
                    "content": (
                        f"Khách #{customer_id}: {attrs.get('review_count', 0)} review, "
                        f"điểm TB {attrs.get('avg_rating', 0)}, "
                        f"sentiment trội: {attrs.get('dominant_sentiment', 'neutral')}."
                    ),
                    "tags": ["graph", "customer", "behavior"],
                }
            )

        return docs[:max_docs]
