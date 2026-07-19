from django.core.validators import RegexValidator


username_validator = RegexValidator(
    regex=r'^[\w.@+-]+\Z',
    message='Username может содержать латинские буквы, цифры и символы _.@+-'
)