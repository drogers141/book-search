from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin

from .forms import BookSearchUserCreationForm, BookSearchUserChangeForm

BookSearchUser = get_user_model()


class BookSearchUserAdmin(UserAdmin):
    add_form = BookSearchUserCreationForm
    form = BookSearchUserChangeForm
    model = BookSearchUser
    list_display = ['email', 'username']


admin.site.register(BookSearchUser, BookSearchUserAdmin)
