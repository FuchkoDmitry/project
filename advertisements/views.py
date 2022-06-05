from django.contrib.auth.models import User
from django.db.models import Q
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from advertisements.filters import AdvertisementFilter
from advertisements.models import Advertisement, FavoriteAdvertisement
from advertisements.permissions import IsOwnerOrStaff
from advertisements.serializers import AdvertisementSerializer, FavoriteAdvertisementSerializer


class AdvertisementViewSet(ModelViewSet):
    """ViewSet для объявлений."""

    queryset = Advertisement.objects.all()
    serializer_class = AdvertisementSerializer
    filterset_class = AdvertisementFilter
    filter_backends = [DjangoFilterBackend]

    def perform_create(self, serializer):
        serializer.save(creator=self.request.user)
        serializer.save(user=self.request.user)

    def get_permissions(self):
        """Получение прав для действий."""
        if self.action in ['update', 'partial_update', 'destroy']:
            return [IsOwnerOrStaff()]
        elif self.action in ['create', 'addfavorites', 'getfavorites']:
            return [IsAuthenticated()]
        return [AllowAny()]

    @action(detail=True, methods=['post'])
    def addfavorites(self, request, pk=None):
        data = {
            'user': request.user,
            'advertisement': self.get_object()
        }
        serializer = FavoriteAdvertisementSerializer(data=data)
        if serializer.is_valid():
            FavoriteAdvertisement.objects.create(
                user=request.user,
                favorite_advertisement=data['advertisement']
            )
            return Response(serializer.data,
                            status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors,
                            status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'])
    def getfavorites(self, request):
        data = {
            'user': request.user,
            'method': request.method
        }
        serializer = FavoriteAdvertisementSerializer(data=data)
        if serializer.is_valid():
            return Response(serializer.data,
                            status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors,
                            status=status.HTTP_400_BAD_REQUEST)

    def get_queryset(self):
        '''
        формирование списка объявлений в зависимости от
        пользователя, сделавшего запрос.
        '''
        if self.request.user.is_anonymous:
            return super().get_queryset().exclude(status='DRAFT')
        else:
            queryset = super().get_queryset().filter(Q(creator=self.request.user) |
                                                     Q(status__in=['OPEN', 'CLOSED'])
                                                     ).distinct()
            return queryset
