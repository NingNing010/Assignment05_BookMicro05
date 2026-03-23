from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Payment
from .serializers import PaymentSerializer


class PaymentListCreate(APIView):
    def get(self, request):
        payments = Payment.objects.all()
        serializer = PaymentSerializer(payments, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = PaymentSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors)


class PaymentDetail(APIView):
    def get(self, request, payment_id):
        try:
            payment = Payment.objects.get(id=payment_id)
        except Payment.DoesNotExist:
            return Response({"error": "Payment not found"}, status=404)
        serializer = PaymentSerializer(payment)
        return Response(serializer.data)

    def put(self, request, payment_id):
        try:
            payment = Payment.objects.get(id=payment_id)
        except Payment.DoesNotExist:
            return Response({"error": "Payment not found"}, status=404)
        serializer = PaymentSerializer(payment, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors)

    def delete(self, request, payment_id):
        try:
            payment = Payment.objects.get(id=payment_id)
        except Payment.DoesNotExist:
            return Response({"error": "Payment not found"}, status=404)
        payment.delete()
        return Response({"message": f"Payment #{payment_id} deleted."}, status=status.HTTP_204_NO_CONTENT)


class PaymentReserve(APIView):
    """Saga command: reserve payment amount for an order."""

    def post(self, request):
        order_id = request.data.get("order_id")
        amount = request.data.get("amount", 0)
        method = request.data.get("method", "credit_card")
        if not order_id:
            return Response({"error": "order_id is required"}, status=status.HTTP_400_BAD_REQUEST)

        payment = Payment.objects.create(
            order_id=order_id,
            amount=amount,
            method=method,
            status='reserved',
        )
        return Response(PaymentSerializer(payment).data, status=status.HTTP_201_CREATED)


class PaymentRelease(APIView):
    """Saga compensation: release payment reservation."""

    def post(self, request):
        order_id = request.data.get("order_id")
        if not order_id:
            return Response({"error": "order_id is required"}, status=status.HTTP_400_BAD_REQUEST)

        payment = Payment.objects.filter(order_id=order_id).order_by('-id').first()
        if not payment:
            return Response({"error": "Payment not found"}, status=status.HTTP_404_NOT_FOUND)

        payment.status = 'released'
        payment.save(update_fields=['status'])
        return Response(PaymentSerializer(payment).data)


class HealthLiveView(APIView):
    def get(self, request):
        return Response({"status": "live", "service": "pay-service"})


class HealthReadyView(APIView):
    def get(self, request):
        Payment.objects.count()
        return Response({"status": "ready", "service": "pay-service"})
