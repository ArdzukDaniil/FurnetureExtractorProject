
from django import forms

class URLExtractionForm(forms.Form):
    url = forms.URLField(
        label='Введите URL страницы товара',
        required=True,
        widget=forms.URLInput(
            attrs={
                'placeholder': 'https://www.example-store.com/product',
                'class': 'form-control' # Для возможной стилизации (Bootstrap)
            }
        )
    )