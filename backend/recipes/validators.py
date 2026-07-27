from django.core.exceptions import ValidationError

from .constants import MAX_IMAGE_SIZE


def validator_image_size(value):
    if value.size > MAX_IMAGE_SIZE:
        raise ValidationError('Файл слишком большой (макс. 5 МБ)')
    return value


def validator_ingredients(ingredients):
    if not ingredients:
        raise ValidationError('Добавьте хотя бы один ингредиент')
    ingredient_ids = [ingredient['id'] for ingredient in ingredients]
    if len(ingredient_ids) != len(set(ingredient_ids)):
        raise ValidationError('Ингредиенты не должны повторяться')
    return ingredients


def validator_tags(tags):
    if not tags:
        raise ValidationError('Добавьте хотя бы один тег')
    if len(tags) != len(set(tags)):
        raise ValidationError('Теги не должны повторяться')
    return tags
