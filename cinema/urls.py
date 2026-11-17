from django.urls import path

from . import views

urlpatterns = [
    path("genres/", views.GenreListView.as_view()),
    path("genres/<int:pk>/", views.GenreDetailView.as_view()),
    path("movies/", views.MovieListView.as_view()),
    path("movies/<int:pk>/", views.MovieDetailView.as_view()),
    path("halls/", views.HallListView.as_view()),
    path("halls/<int:pk>/", views.HallDetailView.as_view()),
    path("halls/<int:pk>/seats/", views.HallSeatsView.as_view()),
    path("seats/", views.SeatListView.as_view()),
    path("seats/<int:pk>/", views.SeatDetailView.as_view()),
    path("sessions/", views.SessionListView.as_view()),
    path("sessions/<int:pk>/", views.SessionDetailView.as_view()),
    path("sessions/<int:pk>/seats/", views.SessionSeatsView.as_view()),
]
