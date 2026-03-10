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
