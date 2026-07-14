from django.core.exceptions import ValidationError

from .constants import MAX_IMAGE_SIZE


def validator_cooking_time(value):
    if value < 1:
        raise ValidationError(
            'Время приготовления не может быть меньше 1 минуты.'
        )


def validator_image_size(value):
    if value.size > MAX_IMAGE_SIZE:
        raise ValidationError('Файл слишком большой (макс. 5 МБ)')
    return value
