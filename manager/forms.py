from django import forms
from django.forms import ModelForm
from .models import CatalogItem, Product, BALANCE_LIMIT, Category


class ProductForm(ModelForm):
    class Meta:
        model = Product
        fields = ["name", "category"]

    def clean(self):
        data = self.cleaned_data

        try:
            Category.objects.get(name=data["category"])
        except:
            raise forms.ValidationError(("Category not found"), code="No_cat")

        return data

    def clean_name(self):
        data = self.cleaned_data
        name = data["name"]
        if len(name) > 20:
            raise forms.ValidationError(("20 characters max"), code="name_len")
        return name

    def __init__(self, *args, **kwargs):
        super(ProductForm, self).__init__(*args, **kwargs)
        for visible in self.visible_fields():
            visible.field.widget.attrs["class"] = "form-control"
            visible.field.widget.attrs["placeholder"] = visible.name.capitalize()


class InsertCatalogItemForm(ModelForm):
    class Meta:
        model = CatalogItem
        # it is always followed by the product form so you can exclude it
        fields = ["quantity", "price"]

    def clean_price(self):
        data = self.cleaned_data
        price = data["price"]
        if price > BALANCE_LIMIT:
            raise forms.ValidationError(
                ("You can't sell at more than price limit!"), code="price_limit"
            )
        return price

    def __init__(self, *args, **kwargs):
        super(InsertCatalogItemForm, self).__init__(*args, **kwargs)
        for visible in self.visible_fields():
            visible.field.widget.attrs["class"] = "form-control"
            visible.field.widget.attrs["placeholder"] = visible.name.capitalize()
            visible.initial = ""
