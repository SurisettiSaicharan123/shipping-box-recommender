from django.contrib import admin, messages
from django.forms.models import BaseInlineFormSet

from .models import Box, Order, OrderItem, Product
from .services.orders import recommend_for_order


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "length", "width", "height", "weight")
    search_fields = ("name",)


@admin.register(Box)
class BoxAdmin(admin.ModelAdmin):
    list_display = ("name", "length", "width", "height", "max_weight", "cost")
    search_fields = ("name",)


class RequireItemsFormSet(BaseInlineFormSet):
    """An order must have at least one item (admin inlines don't enforce min_num on their own)."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.validate_min = True


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    formset = RequireItemsFormSet
    extra = 0
    min_num = 1
    autocomplete_fields = ["product"]


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    """Create an order with its items; the recommended box is calculated on save."""

    inlines = [OrderItemInline]
    list_display = ("__str__", "created_at", "summary", "recommended_box")
    readonly_fields = ("created_at", "summary", "recommended_box", "recommendation_message")
    fields = ("created_at", "summary", "recommended_box", "recommendation_message")
    actions = ["recalculate"]

    @admin.display(description="Order totals")
    def summary(self, obj):
        if not obj or not obj.pk:
            return "-"
        return f"{obj.total_units} unit(s), {obj.total_weight:g} kg"

    def save_related(self, request, form, formsets, change):
        # Items are saved in save_related, so the recommendation must run after it.
        super().save_related(request, form, formsets, change)
        order = form.instance
        result = recommend_for_order(order)
        level = messages.SUCCESS if result else messages.WARNING
        self.message_user(request, f"{order}: {order.recommendation_message}", level)

    @admin.action(description="Recalculate recommended box")
    def recalculate(self, request, queryset):
        for order in queryset:
            result = recommend_for_order(order)
            level = messages.SUCCESS if result else messages.WARNING
            self.message_user(request, f"{order}: {order.recommendation_message}", level)
