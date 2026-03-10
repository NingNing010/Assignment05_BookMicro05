from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Manager
from .serializers import ManagerSerializer
import requests

STAFF_SERVICE_URL = "http://staff-service:8000"


class ManagerListCreate(APIView):
    def get(self, request):
        managers = Manager.objects.all()
        serializer = ManagerSerializer(managers, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = ManagerSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ManagerDetail(APIView):
    def get_object(self, pk):
        try:
            return Manager.objects.get(pk=pk)
        except Manager.DoesNotExist:
            return None

    def get(self, request, pk):
        manager = self.get_object(pk)
        if not manager:
            return Response({"error": "Manager not found"}, status=status.HTTP_404_NOT_FOUND)
        return Response(ManagerSerializer(manager).data)

    def put(self, request, pk):
        manager = self.get_object(pk)
        if not manager:
            return Response({"error": "Manager not found"}, status=status.HTTP_404_NOT_FOUND)
        serializer = ManagerSerializer(manager, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, pk):
        manager = self.get_object(pk)
        if not manager:
            return Response({"error": "Manager not found"}, status=status.HTTP_404_NOT_FOUND)
        serializer = ManagerSerializer(manager, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        manager = self.get_object(pk)
        if not manager:
            return Response({"error": "Manager not found"}, status=status.HTTP_404_NOT_FOUND)
        manager.delete()
        return Response({"message": f"Manager #{pk} deleted."}, status=status.HTTP_204_NO_CONTENT)


class ManagerViewStaff(APIView):
    """Manager can view all staff"""

    def get(self, request):
        r = requests.get(f"{STAFF_SERVICE_URL}/staff/")
        return Response(r.json())
