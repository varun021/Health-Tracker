from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.utils.translation import gettext_lazy as _

User = get_user_model()


@admin.register(User)
class CustomUserAdmin(DjangoUserAdmin):
    """Admin for custom User model with extra fields"""
    list_display = ('id', 'username', 'email', 'is_verified', 'is_staff', 'is_active', 'created_at')
    list_filter = ('is_staff', 'is_active', 'is_verified')
    search_fields = ('username', 'email', 'phone_number')
    ordering = ('-created_at',)
    readonly_fields = ('created_at', 'updated_at',)

    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        (_('Personal info'), {'fields': ('first_name', 'last_name', 'email', 'bio', 'profile_image')}),
        (_('Contact & extra'), {'fields': ('phone_number', 'date_of_birth')}),
        (_('Permissions'), {'fields': ('is_active', 'is_staff', 'is_superuser', 'is_verified', 'groups', 'user_permissions')}),
        (_('Important dates'), {'fields': ('last_login', 'created_at', 'updated_at')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2'),
        }),
    )
