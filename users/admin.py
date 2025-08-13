from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from .models import User

# Import models from other apps
from payments.models import Subscription
from plans.models import Plan
from classes.models import SavedClass



class UserAdmin(BaseUserAdmin):
    model = User
    list_display = ('email', 'username', 'is_staff', 'is_superuser')
    list_filter = ('is_staff', 'is_superuser', 'is_active')
    search_fields = ('email', 'username')
    ordering = ('email',)

    fieldsets = (
        (None, {'fields': ('email', 'username', 'password')}),
        (_('Permissions'), {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        (_('Reset Info'), {'fields': ('reset_code', 'reset_code_created')}),
        (_('Important dates'), {'fields': ('last_login',)}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'username', 'password1', 'password2', 'is_staff', 'is_superuser', 'is_active')}
        ),
    )


admin.site.register(User, UserAdmin)


# Register other models here

@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('user', 'plan', 'plan_type', 'is_active', 'current_period_end')
    list_filter = ('plan', 'plan_type', 'is_active')
    search_fields = ('user__email', 'stripe_customer_id', 'stripe_subscription_id')
    readonly_fields = ('stripe_customer_id', 'stripe_subscription_id', 'current_period_end')

@admin.register(Plan)
class PlanAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'is_saved', 'pinned_date', 'created_at', 'updated_at')
    list_filter = ('is_saved', 'pinned_date', 'created_at')
    search_fields = ('title', 'user__email')
    readonly_fields = ('created_at', 'updated_at')

@admin.register(SavedClass)
class SavedClassAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'pinned_date', 'created_at')
    search_fields = ('title', 'user__email')
    list_filter = ('pinned_date',)
    readonly_fields = ('created_at',)
