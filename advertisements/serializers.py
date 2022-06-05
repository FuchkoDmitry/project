from django.contrib.auth.models import User
from rest_framework import serializers
from rest_framework.exceptions import ValidationError

from advertisements.models import Advertisement, FavoriteAdvertisement


class UserSerializer(serializers.ModelSerializer):
    """Serializer для пользователя."""

    class Meta:
        model = User
        fields = ('id', 'username', 'first_name',
                  'last_name',)


class AdvertisementSerializer(serializers.ModelSerializer):
    """Serializer для объявления."""

    # creator = UserSerializer(read_only=True)
    creator = serializers.ReadOnlyField(source='creator.username')

    class Meta:
        model = Advertisement
        fields = ('id', 'title', 'description', 'creator',
                  'status', 'created_at', )

    def create(self, validated_data):
        """Метод для создания"""

        # Простановка значения поля создатель по-умолчанию.
        # Текущий пользователь является создателем объявления
        # изменить или переопределить его через API нельзя.
        # обратите внимание на `context` – он выставляется автоматически
        # через методы ViewSet.
        # само поле при этом объявляется как `read_only=True`
        validated_data["creator"] = self.context["request"].user
        return super().create(validated_data)

    def validate(self, data):
        """Метод для валидации. Вызывается при создании и обновлении."""
        opened_advertisements = Advertisement.objects.filter(
            creator=self.context['request'].user,
            status__in=('OPEN', 'Открыто')).count()

        if self.context['request'].method == 'POST' and opened_advertisements >= 10:
            if data.get('status', False) not in ('CLOSED', 'DRAFT'):
                raise ValidationError('нельзя иметь более 10 открытых объявлений')
        elif data.get('status', False) == 'OPEN':
            if data['status'] == self.instance.status:
                raise ValidationError('ваше объявление уже открыто')
            elif opened_advertisements >= 10:
                raise ValidationError('нельзя иметь более 10 открытых объявлений')

        return data


class FavoriteAdvertisementSerializer(serializers.ModelSerializer):
    favorite_advertisement = AdvertisementSerializer(read_only=True, many=True)
    # user = UserSerializer(read_only=True)
    user = serializers.ReadOnlyField(source='user.username')

    class Meta:
        model = FavoriteAdvertisement
        fields = ['user', 'favorite_advertisement']

    def create(self, validated_data):
        validated_data["user"] = self.context["request"].user
        return super().create(validated_data)

    def validate(self, attrs):
        attrs['user'] = self.initial_data['user']
        if self.initial_data.get('method', False):
            attrs['favorite_advertisement'] = Advertisement.objects.filter(
                in_favorites_to__user=attrs['user']
            )
        else:
            advertisement = self.initial_data['advertisement']
            advertisements = Advertisement.objects.filter(creator=attrs['user'])
            if advertisement in advertisements:
                raise ValidationError('нельзя добавить в избранное своё объявление')
            elif advertisement.in_favorites_to.filter(user=attrs['user']).exists():
                raise ValidationError('Объявление уже у вас в избранном')
            attrs['favorite_advertisement'] = Advertisement.objects.filter(id=advertisement.id)
        return attrs
