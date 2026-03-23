from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import Clothes
from .serializers import ClothesSerializer


class ClothesListCreate(APIView):
    def get(self, request):
        clothes = Clothes.objects.all()
        return Response(ClothesSerializer(clothes, many=True).data)

    def post(self, request):
        serializer = ClothesSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class ClothesDetail(APIView):
    def get_object(self, pk):
        try:
            return Clothes.objects.get(pk=pk)
        except Clothes.DoesNotExist:
            return None

    def get(self, request, pk):
        clothes = self.get_object(pk)
        if not clothes:
            return Response({'error': 'Clothes not found'}, status=status.HTTP_404_NOT_FOUND)
        return Response(ClothesSerializer(clothes).data)

    def put(self, request, pk):
        clothes = self.get_object(pk)
        if not clothes:
            return Response({'error': 'Clothes not found'}, status=status.HTTP_404_NOT_FOUND)
        serializer = ClothesSerializer(clothes, data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def patch(self, request, pk):
        clothes = self.get_object(pk)
        if not clothes:
            return Response({'error': 'Clothes not found'}, status=status.HTTP_404_NOT_FOUND)
        serializer = ClothesSerializer(clothes, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, pk):
        clothes = self.get_object(pk)
        if not clothes:
            return Response({'error': 'Clothes not found'}, status=status.HTTP_404_NOT_FOUND)
        clothes.delete()
        return Response({'message': f'Clothes #{pk} deleted.'}, status=status.HTTP_204_NO_CONTENT)


class HealthLiveView(APIView):
    def get(self, request):
        return Response({'status': 'live', 'service': 'clothes-service'})


class HealthReadyView(APIView):
    def get(self, request):
        Clothes.objects.count()
        return Response({'status': 'ready', 'service': 'clothes-service'})
