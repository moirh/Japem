from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import User


class UserAdmin(BaseUserAdmin):
    fieldsets = BaseUserAdmin.fieldsets + (("JAPEM", {"fields": ("name", "role")}),)
    add_fieldsets = BaseUserAdmin.add_fieldsets + (("JAPEM", {"fields": ("name", "role")}),)
    list_display = ("username", "name", "email", "role", "is_staff")
    list_filter = BaseUserAdmin.list_filter + ("role",)


admin.site.register(User, UserAdmin)
