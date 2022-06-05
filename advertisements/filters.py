from django_filters import rest_framework as filters

from advertisements.models import Advertisement


class AdvertisementFilter(filters.FilterSet):
    """Фильтры для объявлений."""

    created_at = filters.DateFromToRangeFilter()
    creator = filters.NumberFilter(field_name='creator__id')

    class Meta:
        model = Advertisement
        fields = ('created_at', 'status', 'creator')
