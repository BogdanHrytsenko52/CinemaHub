from datetime import timedelta

from rest_framework import serializers

from .exceptions import Conflict
from .models import Genre, Hall, Movie, Seat, Session


class GenreSerializer(serializers.ModelSerializer):
    class Meta:
        model = Genre
        fields = ["id", "name"]

    def validate_name(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Name cannot be empty.")
        return value


class MovieListSerializer(serializers.ModelSerializer):
    genre_id = serializers.PrimaryKeyRelatedField(source="genre", read_only=True)

    class Meta:
        model = Movie
        fields = ["id", "title", "genre_id", "duration", "rating"]


class MovieSerializer(serializers.ModelSerializer):
    genre_id = serializers.PrimaryKeyRelatedField(source="genre", queryset=Genre.objects.all())

    class Meta:
        model = Movie
        fields = [
            "id",
            "title",
            "description",
            "genre_id",
            "duration",
            "rating",
            "age_rating",
        ]

    def validate_title(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Title cannot be empty.")
        return value

    def validate_age_rating(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Age rating cannot be empty.")
        return value


class HallSerializer(serializers.ModelSerializer):
    class Meta:
        model = Hall
        fields = ["id", "name"]

    def validate_name(self, value):
        value = value.strip()
        if not value:
            raise serializers.ValidationError("Name cannot be empty.")
        return value


class SeatSerializer(serializers.ModelSerializer):
    hall_id = serializers.PrimaryKeyRelatedField(source="hall", queryset=Hall.objects.all())

    class Meta:
        model = Seat
        fields = ["id", "hall_id", "row", "number"]


class SessionSerializer(serializers.ModelSerializer):
    movie_id = serializers.PrimaryKeyRelatedField(source="movie", queryset=Movie.objects.all())
    hall_id = serializers.PrimaryKeyRelatedField(source="hall", queryset=Hall.objects.all())

    class Meta:
        model = Session
        fields = ["id", "movie_id", "hall_id", "start_time", "price"]

    def validate(self, attrs):
        instance = self.instance
        movie = attrs.get("movie", getattr(instance, "movie", None))
        hall = attrs.get("hall", getattr(instance, "hall", None))
        start_time = attrs.get("start_time", getattr(instance, "start_time", None))

        if movie is None or hall is None or start_time is None:
            return attrs

        new_end = start_time + timedelta(minutes=movie.duration)
        existing_sessions = Session.objects.filter(hall=hall).select_related("movie")
        if instance:
            existing_sessions = existing_sessions.exclude(pk=instance.pk)

        for existing in existing_sessions:
            existing_end = existing.start_time + timedelta(minutes=existing.movie.duration)
            if start_time < existing_end and existing.start_time < new_end:
                raise Conflict(
                    "The hall already has a session that overlaps this time interval."
                )
        return attrs


class SessionSeatSerializer(SeatSerializer):
    is_available = serializers.SerializerMethodField()

    class Meta(SeatSerializer.Meta):
        fields = ["id", "row", "number", "is_available"]

    def get_is_available(self, seat):
        # Bookings are deliberately outside the current project scope.
        return True
