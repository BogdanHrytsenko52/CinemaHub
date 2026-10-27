from django.contrib import admin

from .models import Genre, Hall, Movie, Seat, Session


admin.site.register([Genre, Movie, Hall, Seat, Session])
