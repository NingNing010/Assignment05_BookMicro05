import json
import math
import os
from dataclasses import dataclass
from typing import Dict, List, Optional

import numpy as np


@dataclass
class CustomerBehaviorFeatures:
    customer_id: int
    review_count: float
    avg_rating: float
    rating_std: float
    positive_ratio: float
    negative_ratio: float
    avg_comment_len: float
    recency_days: float

    def as_list(self) -> List[float]:
        return [
            self.review_count,
            self.avg_rating,
            self.rating_std,
            self.positive_ratio,
            self.negative_ratio,
            self.avg_comment_len,
            self.recency_days,
        ]


def _safe_std(values: List[float]) -> float:
    if len(values) <= 1:
        return 0.0
    mean_v = sum(values) / len(values)
    var = sum((v - mean_v) ** 2 for v in values) / len(values)
    return math.sqrt(var)


def _days_since(dt, now_dt) -> float:
    return float(max((now_dt - dt).days, 0))


def _pseudo_label(features: CustomerBehaviorFeatures) -> int:
    # 0: dissatisfaction risk, 1: neutral, 2: loyal/positive
    if features.avg_rating <= 2.8 or features.negative_ratio >= 0.4:
        return 0
    if features.avg_rating >= 4.0 and features.positive_ratio >= 0.6 and features.review_count >= 3:
        return 2
    return 1


def aggregate_customer_features(reviews) -> List[CustomerBehaviorFeatures]:
    from django.utils import timezone

    grouped: Dict[int, List] = {}
    for r in reviews:
        grouped.setdefault(int(r.customer_id), []).append(r)

    now_dt = timezone.now()
    rows: List[CustomerBehaviorFeatures] = []
    for customer_id, items in grouped.items():
        ratings = [float(i.rating or 0) for i in items]
        review_count = float(len(items))
        avg_rating = sum(ratings) / len(ratings)
        rating_std = _safe_std(ratings)
        positive_ratio = sum(1 for x in ratings if x >= 4.0) / len(ratings)
        negative_ratio = sum(1 for x in ratings if x <= 2.0) / len(ratings)
        avg_comment_len = sum(len((i.comment or "").strip()) for i in items) / len(items)
        latest = max(i.created_at for i in items)
        recency_days = _days_since(latest, now_dt)
        rows.append(
            CustomerBehaviorFeatures(
                customer_id=customer_id,
                review_count=review_count,
                avg_rating=avg_rating,
                rating_std=rating_std,
                positive_ratio=positive_ratio,
                negative_ratio=negative_ratio,
                avg_comment_len=avg_comment_len,
                recency_days=recency_days,
            )
        )
    return rows


class BehaviorNet:
    """Simple MLP (Deep Learning) implemented with numpy.

    Architecture: 7 -> 24 -> 16 -> 3
    Activations: ReLU
    Loss: Cross-entropy
    """

    def __init__(self, input_size: int = 7, hidden_size: int = 24, num_classes: int = 3, seed: int = 42):
        rng = np.random.default_rng(seed)
        self.W1 = rng.normal(0, 0.1, size=(input_size, hidden_size)).astype(np.float64)
        self.b1 = np.zeros((1, hidden_size), dtype=np.float64)
        self.W2 = rng.normal(0, 0.1, size=(hidden_size, 16)).astype(np.float64)
        self.b2 = np.zeros((1, 16), dtype=np.float64)
        self.W3 = rng.normal(0, 0.1, size=(16, num_classes)).astype(np.float64)
        self.b3 = np.zeros((1, num_classes), dtype=np.float64)

    @staticmethod
    def _relu(x):
        return np.maximum(0.0, x)

    @staticmethod
    def _relu_grad(x):
        return (x > 0).astype(np.float64)

    @staticmethod
    def _softmax(z):
        z = z - np.max(z, axis=1, keepdims=True)
        exp = np.exp(z)
        return exp / np.sum(exp, axis=1, keepdims=True)

    def forward(self, x: np.ndarray):
        z1 = x @ self.W1 + self.b1
        a1 = self._relu(z1)
        z2 = a1 @ self.W2 + self.b2
        a2 = self._relu(z2)
        z3 = a2 @ self.W3 + self.b3
        probs = self._softmax(z3)
        cache = (x, z1, a1, z2, a2, z3, probs)
        return probs, cache

    def train_step(self, x: np.ndarray, y: np.ndarray, lr: float = 0.01):
        n = x.shape[0]
        probs, cache = self.forward(x)
        x0, z1, a1, z2, a2, _, _ = cache

        y_onehot = np.zeros_like(probs)
        y_onehot[np.arange(n), y] = 1.0
        loss = -np.sum(y_onehot * np.log(probs + 1e-12)) / n

        dz3 = (probs - y_onehot) / n
        dW3 = a2.T @ dz3
        db3 = np.sum(dz3, axis=0, keepdims=True)

        da2 = dz3 @ self.W3.T
        dz2 = da2 * self._relu_grad(z2)
        dW2 = a1.T @ dz2
        db2 = np.sum(dz2, axis=0, keepdims=True)

        da1 = dz2 @ self.W2.T
        dz1 = da1 * self._relu_grad(z1)
        dW1 = x0.T @ dz1
        db1 = np.sum(dz1, axis=0, keepdims=True)

        self.W3 -= lr * dW3
        self.b3 -= lr * db3
        self.W2 -= lr * dW2
        self.b2 -= lr * db2
        self.W1 -= lr * dW1
        self.b1 -= lr * db1

        pred = np.argmax(probs, axis=1)
        acc = float(np.mean(pred == y))
        return float(loss), acc

    def predict(self, x: np.ndarray):
        probs, _ = self.forward(x)
        pred = np.argmax(probs, axis=1)
        return pred, probs

    def get_state(self) -> Dict[str, List]:
        return {
            "W1": self.W1.tolist(),
            "b1": self.b1.tolist(),
            "W2": self.W2.tolist(),
            "b2": self.b2.tolist(),
            "W3": self.W3.tolist(),
            "b3": self.b3.tolist(),
        }

    def load_state(self, state: Dict[str, List]):
        self.W1 = np.array(state["W1"], dtype=np.float64)
        self.b1 = np.array(state["b1"], dtype=np.float64)
        self.W2 = np.array(state["W2"], dtype=np.float64)
        self.b2 = np.array(state["b2"], dtype=np.float64)
        self.W3 = np.array(state["W3"], dtype=np.float64)
        self.b3 = np.array(state["b3"], dtype=np.float64)


class BehaviorModelService:
    LABELS = {
        0: "dissatisfaction_risk",
        1: "neutral",
        2: "loyal_positive",
    }

    ADVICE_MAP = {
        "dissatisfaction_risk": [
            "Gửi voucher xin lỗi 10-15% cho đơn tiếp theo.",
            "Ưu tiên CSKH chủ động và đề xuất sách đúng thể loại đã mua.",
            "Gửi email hỏi thăm lý do đánh giá thấp để cải thiện.",
        ],
        "neutral": [
            "Gợi ý sách top-rated theo thể loại đã tương tác.",
            "Tạo combo nhỏ để tăng tần suất mua (cross-sell).",
            "Nhắc review sau khi giao hàng để tăng dữ liệu hành vi.",
        ],
        "loyal_positive": [
            "Đưa vào chương trình VIP/early access.",
            "Đề xuất pre-order, bộ sưu tập mới và combo premium.",
            "Tặng điểm thưởng và referral bonus.",
        ],
    }

    def __init__(self):
        base_dir = os.path.dirname(os.path.dirname(__file__))
        self.artifact_dir = os.path.join(base_dir, "artifacts")
        os.makedirs(self.artifact_dir, exist_ok=True)
        self.model_path = os.path.join(self.artifact_dir, "model_behavior.json")
        self.scaler_path = os.path.join(self.artifact_dir, "model_behavior_scaler.json")
        self.model: Optional[BehaviorNet] = None
        self.scaler: Optional[Dict[str, List[float]]] = None

    @staticmethod
    def _fit_scaler(matrix: List[List[float]]) -> Dict[str, List[float]]:
        cols = list(zip(*matrix))
        means = [sum(c) / len(c) for c in cols]
        stds = []
        for idx, c in enumerate(cols):
            mean_v = means[idx]
            var = sum((v - mean_v) ** 2 for v in c) / len(c)
            stds.append(math.sqrt(var) if var > 0 else 1.0)
        return {"means": means, "stds": stds}

    @staticmethod
    def _transform(matrix: List[List[float]], scaler: Dict[str, List[float]]) -> List[List[float]]:
        means = scaler["means"]
        stds = scaler["stds"]
        transformed = []
        for row in matrix:
            transformed.append([(row[i] - means[i]) / stds[i] for i in range(len(row))])
        return transformed

    def train(self, reviews, epochs: int = 120, lr: float = 0.01) -> Dict:
        rows = aggregate_customer_features(reviews)
        if len(rows) < 3:
            return {
                "trained": False,
                "message": "Cần ít nhất 3 khách hàng có review để train model_behavior.",
                "samples": len(rows),
            }

        X = [r.as_list() for r in rows]
        y = [_pseudo_label(r) for r in rows]

        scaler = self._fit_scaler(X)
        Xn = self._transform(X, scaler)

        x_arr = np.array(Xn, dtype=np.float64)
        y_arr = np.array(y, dtype=np.int64)

        model = BehaviorNet(input_size=len(X[0]), hidden_size=24, num_classes=3)
        train_acc = 0.0
        for _ in range(max(1, int(epochs))):
            _, train_acc = model.train_step(x_arr, y_arr, lr=lr)

        with open(self.model_path, "w", encoding="utf-8") as f:
            json.dump(model.get_state(), f, ensure_ascii=True)
        with open(self.scaler_path, "w", encoding="utf-8") as f:
            json.dump(scaler, f, ensure_ascii=True)

        self.model = model
        self.scaler = scaler

        return {
            "trained": True,
            "samples": len(rows),
            "epochs": int(epochs),
            "learning_rate": lr,
            "train_accuracy": round(train_acc, 4),
            "model_path": self.model_path,
        }

    def _load_if_needed(self):
        if self.model is not None and self.scaler is not None:
            return
        if not os.path.exists(self.model_path) or not os.path.exists(self.scaler_path):
            raise FileNotFoundError("Chưa có model_behavior. Hãy gọi endpoint train trước.")

        with open(self.scaler_path, "r", encoding="utf-8") as f:
            scaler = json.load(f)

        with open(self.model_path, "r", encoding="utf-8") as f:
            model_state = json.load(f)

        model = BehaviorNet(input_size=7, hidden_size=24, num_classes=3)
        model.load_state(model_state)

        self.model = model
        self.scaler = scaler

    def predict_customer(self, customer_id: int, reviews) -> Dict:
        self._load_if_needed()
        rows = aggregate_customer_features(reviews)
        target = next((r for r in rows if int(r.customer_id) == int(customer_id)), None)
        if not target:
            return {
                "found": False,
                "message": f"Không tìm thấy dữ liệu review cho customer_id={customer_id}",
            }

        x = [target.as_list()]
        xn = self._transform(x, self.scaler)
        x_arr = np.array(xn, dtype=np.float64)
        pred, probs = self.model.predict(x_arr)
        pred_idx = int(pred[0])
        probs_list = probs[0].tolist()

        label = self.LABELS[pred_idx]
        return {
            "found": True,
            "customer_id": customer_id,
            "segment": label,
            "confidence": round(float(probs_list[pred_idx]), 4),
            "probabilities": {
                self.LABELS[i]: round(float(probs_list[i]), 4) for i in range(3)
            },
            "features": {
                "review_count": target.review_count,
                "avg_rating": round(target.avg_rating, 4),
                "rating_std": round(target.rating_std, 4),
                "positive_ratio": round(target.positive_ratio, 4),
                "negative_ratio": round(target.negative_ratio, 4),
                "avg_comment_len": round(target.avg_comment_len, 4),
                "recency_days": round(target.recency_days, 4),
            },
            "service_advice": self.ADVICE_MAP[label],
            "model_name": "model_behavior",
            "model_type": "DeepLearning-MLP",
        }
