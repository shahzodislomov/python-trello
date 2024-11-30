from django.contrib import admin
from .models import User, ToDo


class TodoAdmin(admin.ModelAdmin):
    list_display = ('title', 'status', 'due_date', 'created_at')
    search_fields = ('title',)
    list_filter = ('status',)


admin.site.register(User)
admin.site.register(ToDo, TodoAdmin)
