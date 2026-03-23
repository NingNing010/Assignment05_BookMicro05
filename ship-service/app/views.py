from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Shipment
from .serializers import ShipmentSerializer


class ShipmentListCreate(APIView):
    def get(self, request):
        shipments = Shipment.objects.all()
        serializer = ShipmentSerializer(shipments, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = ShipmentSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors)


class ShipmentDetail(APIView):
    def get(self, request, shipment_id):
        try:
            shipment = Shipment.objects.get(id=shipment_id)
        except Shipment.DoesNotExist:
            return Response({"error": "Shipment not found"}, status=404)
        serializer = ShipmentSerializer(shipment)
        return Response(serializer.data)

    def put(self, request, shipment_id):
        try:
            shipment = Shipment.objects.get(id=shipment_id)
        except Shipment.DoesNotExist:
            return Response({"error": "Shipment not found"}, status=404)
        serializer = ShipmentSerializer(shipment, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors)

    def delete(self, request, shipment_id):
        try:
            shipment = Shipment.objects.get(id=shipment_id)
        except Shipment.DoesNotExist:
            return Response({"error": "Shipment not found"}, status=404)
        shipment.delete()
        return Response({"message": f"Shipment #{shipment_id} deleted."}, status=status.HTTP_204_NO_CONTENT)


class ShipmentReserve(APIView):
    """Saga command: reserve shipment for order."""

    def post(self, request):
        order_id = request.data.get("order_id")
        customer_id = request.data.get("customer_id")
        method = request.data.get("method", "standard")
        if not order_id or not customer_id:
            return Response({"error": "order_id and customer_id are required"}, status=status.HTTP_400_BAD_REQUEST)

        shipment = Shipment.objects.create(
            order_id=order_id,
            customer_id=customer_id,
            method=method,
            status='reserved',
        )
        return Response(ShipmentSerializer(shipment).data, status=status.HTTP_201_CREATED)


class ShipmentRelease(APIView):
    """Saga compensation: cancel reserved shipment."""

    def post(self, request):
        order_id = request.data.get("order_id")
        if not order_id:
            return Response({"error": "order_id is required"}, status=status.HTTP_400_BAD_REQUEST)

        shipment = Shipment.objects.filter(order_id=order_id).order_by('-id').first()
        if not shipment:
            return Response({"error": "Shipment not found"}, status=status.HTTP_404_NOT_FOUND)

        shipment.status = 'cancelled'
        shipment.save(update_fields=['status'])
        return Response(ShipmentSerializer(shipment).data)


class HealthLiveView(APIView):
    def get(self, request):
        return Response({"status": "live", "service": "ship-service"})


class HealthReadyView(APIView):
    def get(self, request):
        Shipment.objects.count()
        return Response({"status": "ready", "service": "ship-service"})
