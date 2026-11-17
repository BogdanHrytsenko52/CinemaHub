import logging

from django.db.models.deletion import ProtectedError
from django.utils.dateparse import parse_date
from drf_spectacular.utils import (
    OpenApiExample,
    OpenApiResponse,
    extend_schema,
    extend_schema_view,
)
from rest_framework import status
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.permissions import BasePermission
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

logger = logging.getLogger("cinema")


class ReadOnlyOrStaff(BasePermission):
    def has_permission(self, request, view):
        if request.method in ("GET", "HEAD", "OPTIONS"):
            return True
        return bool(
            request.user and request.user.is_authenticated and request.user.is_staff
        )


class BaseAPIView(APIView):
    permission_classes = [ReadOnlyOrStaff]

    def get_object(self, queryset, pk):
        try:
            return queryset.get(pk=pk)
        except queryset.model.DoesNotExist as exc:
            raise NotFound() from exc

    def delete_object(self, instance, resource_name):
        try:
            instance.delete()
        except ProtectedError as exc:
            logger.warning(
                "Deletion blocked for %s id=%s because related records exist",
                resource_name,
                instance.pk,
            )
            raise Conflict(
                f"Cannot delete this {resource_name} because related records exist."
            ) from exc
        return Response(status=status.HTTP_204_NO_CONTENT)


@extend_schema_view(
    get=extend_schema(
        summary="List genres",
        auth=[],
        responses={200: GenreSerializer(many=True)},
    ),
    post=extend_schema(
        summary="Create a genre (staff only)",
        request=GenreSerializer,
        responses={
            201: GenreSerializer,
            400: OpenApiResponse(description="Invalid data"),
            401: OpenApiResponse(description="Authentication required"),
            403: OpenApiResponse(description="Staff permission required"),
        },
        examples=[
            OpenApiExample("Genre request", value={"name": "Drama"}, request_only=True)
        ],
    ),
)
class GenreListView(BaseAPIView):
    def get(self, request):
        return Response(GenreSerializer(Genre.objects.all(), many=True).data)

    def post(self, request):
        serializer = GenreSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        logger.info(
            "Genre created id=%s by user_id=%s", serializer.instance.pk, request.user.pk
        )
        return Response(serializer.data, status=status.HTTP_201_CREATED)


@extend_schema_view(
    get=extend_schema(
        summary="Retrieve a genre",
        auth=[],
        responses={
            200: GenreSerializer,
            404: OpenApiResponse(description="Genre not found"),
        },
    ),
    patch=extend_schema(
        summary="Update a genre (staff only)",
        request=GenreSerializer,
        responses={
            200: GenreSerializer,
            400: OpenApiResponse(description="Invalid data"),
            401: OpenApiResponse(description="Authentication required"),
            403: OpenApiResponse(description="Staff permission required"),
            404: OpenApiResponse(description="Genre not found"),
        },
    ),
    delete=extend_schema(
        summary="Delete a genre (staff only)",
        responses={
            204: None,
            401: OpenApiResponse(description="Authentication required"),
            403: OpenApiResponse(description="Staff permission required"),
            404: OpenApiResponse(description="Genre not found"),
            409: OpenApiResponse(description="Genre has related movies"),
        },
    ),
)
class GenreDetailView(BaseAPIView):
    def get(self, request, pk):
        genre = self.get_object(Genre.objects.all(), pk)
        return Response(GenreSerializer(genre).data)

    def patch(self, request, pk):
        genre = self.get_object(Genre.objects.all(), pk)
        serializer = GenreSerializer(genre, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        logger.info("Genre updated id=%s by user_id=%s", genre.pk, request.user.pk)
        return Response(serializer.data)

    def delete(self, request, pk):
        genre = self.get_object(Genre.objects.all(), pk)
        response = self.delete_object(genre, "genre")
        logger.info("Genre deleted id=%s by user_id=%s", pk, request.user.pk)
        return response


@extend_schema_view(get=extend_schema(operation_id="movies_list", auth=[]))
class MovieListView(BaseAPIView):
    serializer_class = MovieSerializer

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


@extend_schema_view(get=extend_schema(operation_id="movies_retrieve", auth=[]))
class MovieDetailView(BaseAPIView):
    serializer_class = MovieSerializer

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


@extend_schema_view(get=extend_schema(operation_id="halls_list", auth=[]))
class HallListView(BaseAPIView):
    serializer_class = HallSerializer

    def get(self, request):
        return Response(HallSerializer(Hall.objects.all(), many=True).data)

    def post(self, request):
        serializer = HallSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


@extend_schema_view(get=extend_schema(operation_id="halls_retrieve", auth=[]))
class HallDetailView(BaseAPIView):
    serializer_class = HallSerializer

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


@extend_schema_view(get=extend_schema(auth=[]))
class HallSeatsView(BaseAPIView):
    serializer_class = SeatSerializer

    def get(self, request, pk):
        hall = self.get_object(Hall.objects.all(), pk)
        seats = hall.seats.all()
        return Response(SeatSerializer(seats, many=True).data)


@extend_schema_view(get=extend_schema(operation_id="seats_list", auth=[]))
class SeatListView(BaseAPIView):
    serializer_class = SeatSerializer

    def get(self, request):
        return Response(
            SeatSerializer(Seat.objects.select_related("hall"), many=True).data
        )

    def post(self, request):
        serializer = SeatSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)


@extend_schema_view(get=extend_schema(operation_id="seats_retrieve", auth=[]))
class SeatDetailView(BaseAPIView):
    serializer_class = SeatSerializer

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


@extend_schema_view(get=extend_schema(operation_id="sessions_list", auth=[]))
class SessionListView(BaseAPIView):
    serializer_class = SessionSerializer

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


@extend_schema_view(get=extend_schema(operation_id="sessions_retrieve", auth=[]))
class SessionDetailView(BaseAPIView):
    serializer_class = SessionSerializer

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


@extend_schema_view(get=extend_schema(auth=[]))
class SessionSeatsView(BaseAPIView):
    serializer_class = SessionSeatSerializer

    def get(self, request, pk):
        session = self.get_object(Session.objects.select_related("hall"), pk)
        return Response(SessionSeatSerializer(session.hall.seats.all(), many=True).data)
