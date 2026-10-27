from django.db.models.deletion import ProtectedError
from django.utils.dateparse import parse_date
from rest_framework import status
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from .exceptions import Conflict
from .models import Genre, Hall, Movie, Seat, Session
from .serializers import (
    GenreSerializer,
    HallSerializer,
    MovieListSerializer,
    MovieSerializer,
    SeatSerializer,
    SessionSeatSerializer,
    SessionSerializer,
)


class BaseAPIView(APIView):
    def get_object(self, queryset, pk):
        try:
            return queryset.get(pk=pk)
        except queryset.model.DoesNotExist as exc:
            raise NotFound() from exc

    def delete_object(self, instance, resource_name):
        try:
            instance.delete()
        except ProtectedError as exc:
            raise Conflict(
                f"Cannot delete this {resource_name} because related records exist."
            ) from exc
        return Response(status=status.HTTP_204_NO_CONTENT)


class GenreListView(BaseAPIView):
    def get(self, request):
        return Response(GenreSerializer(Genre.objects.all(), many=True).data)

    def post(self, request):
        serializer = GenreSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class GenreDetailView(BaseAPIView):
    def get(self, request, pk):
        genre = self.get_object(Genre.objects.all(), pk)
        return Response(GenreSerializer(genre).data)

    def patch(self, request, pk):
        genre = self.get_object(Genre.objects.all(), pk)
        serializer = GenreSerializer(genre, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def delete(self, request, pk):
        return self.delete_object(self.get_object(Genre.objects.all(), pk), "genre")


class MovieListView(BaseAPIView):
    def get(self, request):
        movies = Movie.objects.select_related("genre").all()
        search = request.query_params.get("search")
        genre_id = request.query_params.get("genre_id")
        ordering = request.query_params.get("ordering")

        if search:
            movies = movies.filter(title__icontains=search)
        if genre_id:
            if not genre_id.isdigit():
                raise ValidationError({"genre_id": ["Must be a positive integer."]})
            movies = movies.filter(genre_id=genre_id)
        if ordering:
            if ordering not in {"title", "-title", "rating", "-rating"}:
                raise ValidationError(
                    {"ordering": ["Use title, -title, rating, or -rating."]}
                )
            movies = movies.order_by(ordering)
        return Response(MovieListSerializer(movies, many=True).data)

    def post(self, request):
        serializer = MovieSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class MovieDetailView(BaseAPIView):
    def get(self, request, pk):
        movie = self.get_object(Movie.objects.select_related("genre"), pk)
        return Response(MovieSerializer(movie).data)

    def patch(self, request, pk):
        movie = self.get_object(Movie.objects.all(), pk)
        serializer = MovieSerializer(movie, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def delete(self, request, pk):
        return self.delete_object(self.get_object(Movie.objects.all(), pk), "movie")


class HallListView(BaseAPIView):
    def get(self, request):
        return Response(HallSerializer(Hall.objects.all(), many=True).data)

    def post(self, request):
        serializer = HallSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class HallDetailView(BaseAPIView):
    def get(self, request, pk):
        hall = self.get_object(Hall.objects.all(), pk)
        return Response(HallSerializer(hall).data)

    def patch(self, request, pk):
        hall = self.get_object(Hall.objects.all(), pk)
        serializer = HallSerializer(hall, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def delete(self, request, pk):
        return self.delete_object(self.get_object(Hall.objects.all(), pk), "hall")


class HallSeatsView(BaseAPIView):
    def get(self, request, pk):
        hall = self.get_object(Hall.objects.all(), pk)
        seats = hall.seats.all()
        return Response(SeatSerializer(seats, many=True).data)


class SeatListView(BaseAPIView):
    def get(self, request):
        return Response(SeatSerializer(Seat.objects.select_related("hall"), many=True).data)

    def post(self, request):
        serializer = SeatSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class SeatDetailView(BaseAPIView):
    def get(self, request, pk):
        seat = self.get_object(Seat.objects.select_related("hall"), pk)
        return Response(SeatSerializer(seat).data)

    def patch(self, request, pk):
        seat = self.get_object(Seat.objects.all(), pk)
        serializer = SeatSerializer(seat, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def delete(self, request, pk):
        return self.delete_object(self.get_object(Seat.objects.all(), pk), "seat")


class SessionListView(BaseAPIView):
    def get(self, request):
        sessions = Session.objects.select_related("movie", "hall").all()
        movie_id = request.query_params.get("movie_id")
        date_value = request.query_params.get("date")

        if movie_id:
            if not movie_id.isdigit():
                raise ValidationError({"movie_id": ["Must be a positive integer."]})
            sessions = sessions.filter(movie_id=movie_id)
        if date_value:
            date = parse_date(date_value)
            if date is None:
                raise ValidationError({"date": ["Use ISO format YYYY-MM-DD."]})
            sessions = sessions.filter(start_time__date=date)
        return Response(SessionSerializer(sessions, many=True).data)

    def post(self, request):
        serializer = SessionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class SessionDetailView(BaseAPIView):
    def get(self, request, pk):
        session = self.get_object(Session.objects.select_related("movie", "hall"), pk)
        return Response(SessionSerializer(session).data)

    def patch(self, request, pk):
        session = self.get_object(Session.objects.all(), pk)
        serializer = SessionSerializer(session, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def delete(self, request, pk):
        return self.delete_object(self.get_object(Session.objects.all(), pk), "session")


class SessionSeatsView(BaseAPIView):
    def get(self, request, pk):
        session = self.get_object(Session.objects.select_related("hall"), pk)
        return Response(SessionSeatSerializer(session.hall.seats.all(), many=True).data)
