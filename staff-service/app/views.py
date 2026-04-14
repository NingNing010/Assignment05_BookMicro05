from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Staff
from .serializers import StaffSerializer
import requests

BOOK_SERVICE_URL = "http://product-service:8000"


class StaffListCreate(APIView):
    def get(self, request):
        staff = Staff.objects.all()
        serializer = StaffSerializer(staff, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = StaffSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class StaffDetail(APIView):
    def get_object(self, pk):
        try:
            return Staff.objects.get(pk=pk)
        except Staff.DoesNotExist:
            return None

    def get(self, request, pk):
        staff = self.get_object(pk)
        if not staff:
            return Response({"error": "Staff not found"}, status=status.HTTP_404_NOT_FOUND)
        return Response(StaffSerializer(staff).data)

    def put(self, request, pk):
        staff = self.get_object(pk)
        if not staff:
            return Response({"error": "Staff not found"}, status=status.HTTP_404_NOT_FOUND)
        serializer = StaffSerializer(staff, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, pk):
        staff = self.get_object(pk)
        if not staff:
            return Response({"error": "Staff not found"}, status=status.HTTP_404_NOT_FOUND)
        serializer = StaffSerializer(staff, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        staff = self.get_object(pk)
        if not staff:
            return Response({"error": "Staff not found"}, status=status.HTTP_404_NOT_FOUND)
        staff.delete()
        return Response({"message": f"Staff #{pk} deleted."}, status=status.HTTP_204_NO_CONTENT)


class StaffManageBooks(APIView):
    """Staff manages books via book-service"""

    def get(self, request):
        r = requests.get(f"{BOOK_SERVICE_URL}/books/")
        return Response(r.json())

    def post(self, request):
        r = requests.post(f"{BOOK_SERVICE_URL}/books/", json=request.data)
        return Response(r.json(), status=r.status_code)

    def put(self, request):
        """Update a book via book-service. Body must include 'book_id'."""
        book_id = request.data.get('book_id')
        if not book_id:
            return Response({"error": "book_id required"}, status=status.HTTP_400_BAD_REQUEST)
        r = requests.put(f"{BOOK_SERVICE_URL}/books/{book_id}/", json=request.data)
        return Response(r.json(), status=r.status_code)

    def patch(self, request):
        """Partial update a book. Body must include 'book_id'."""
        book_id = request.data.get('book_id')
        if not book_id:
            return Response({"error": "book_id required"}, status=status.HTTP_400_BAD_REQUEST)
        r = requests.patch(f"{BOOK_SERVICE_URL}/books/{book_id}/", json=request.data)
        return Response(r.json(), status=r.status_code)

    def delete(self, request):
        """Delete a book. Query param: ?book_id=1"""
        book_id = request.query_params.get('book_id')
        if not book_id:
            return Response({"error": "book_id query param required"}, status=status.HTTP_400_BAD_REQUEST)
        r = requests.delete(f"{BOOK_SERVICE_URL}/books/{book_id}/")
        return Response({"message": f"Book #{book_id} deleted."}, status=r.status_code)
