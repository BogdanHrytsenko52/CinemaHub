from datetime import datetime
from decimal import Decimal

from django.utils import timezone
from rest_framework import status
from rest_framework.test import APITestCase

from .models import Genre, Hall, Movie, Seat, Session


class CinemaApiTests(APITestCase):
    def setUp(self):
        self.genre = Genre.objects.create(name="Science fiction")
        self.hall = Hall.objects.create(name="Hall 1")
        self.movie = self.make_movie(title="Interstellar", duration=169, rating="8.7")

    def make_movie(self, **overrides):
        data = {
            "title": "Arrival",
            "description": "A science-fiction film.",
            "genre": self.genre,
            "duration": 120,
            "rating": Decimal("7.5"),
            "age_rating": "12+",
        }
        data.update(overrides)
        return Movie.objects.create(**data)

    def session_payload(self, **overrides):
        data = {
            "movie_id": self.movie.id,
            "hall_id": self.hall.id,
            "start_time": "2026-10-20T18:00:00Z",
            "price": "200.00",
        }
        data.update(overrides)
        return data

    def assert_api_error(self, response, expected_status, expected_code):
        self.assertEqual(response.status_code, expected_status)
        self.assertEqual(response.data["error"]["code"], expected_code)
        self.assertIn("message", response.data["error"])
        self.assertIn("details", response.data["error"])

    def test_genre_crud_and_not_found(self):
        create = self.client.post("/api/genres/", {"name": "Drama"}, format="json")
        self.assertEqual(create.status_code, status.HTTP_201_CREATED)
        genre_id = create.data["id"]

        listing = self.client.get("/api/genres/")
        self.assertEqual(listing.status_code, status.HTTP_200_OK)
        self.assertEqual(len(listing.data), 2)
        self.assertEqual(self.client.get(f"/api/genres/{genre_id}/").data["name"], "Drama")

        update = self.client.patch(
            f"/api/genres/{genre_id}/", {"name": "Comedy"}, format="json"
        )
        self.assertEqual(update.status_code, status.HTTP_200_OK)
        self.assertEqual(update.data["name"], "Comedy")
        self.assertEqual(self.client.delete(f"/api/genres/{genre_id}/").status_code, 204)

        self.assert_api_error(self.client.get("/api/genres/9999/"), 404, "not_found")

    def test_genre_validation_and_related_delete_conflict(self):
        invalid = self.client.post("/api/genres/", {"name": "   "}, format="json")
        self.assert_api_error(invalid, 400, "bad_request")

        duplicate = self.client.post(
            "/api/genres/", {"name": "Science fiction"}, format="json"
        )
        self.assert_api_error(duplicate, 400, "bad_request")
        self.assert_api_error(self.client.delete(f"/api/genres/{self.genre.id}/"), 409, "conflict")

    def test_movie_crud_search_filter_and_ordering(self):
        drama = Genre.objects.create(name="Drama")
        create = self.client.post(
            "/api/movies/",
            {
                "title": "Dune",
                "description": "Desert epic.",
                "genre_id": drama.id,
                "duration": 155,
                "rating": "8.0",
                "age_rating": "12+",
            },
            format="json",
        )
        self.assertEqual(create.status_code, 201)
        movie_id = create.data["id"]
        self.assertEqual(self.client.get(f"/api/movies/{movie_id}/").data["title"], "Dune")

        update = self.client.patch(
            f"/api/movies/{movie_id}/", {"rating": "8.5"}, format="json"
        )
        self.assertEqual(update.status_code, 200)
        self.assertEqual(update.data["rating"], "8.5")

        self.make_movie(title="Inception", rating="9.0")
        filtered = self.client.get(f"/api/movies/?search=inter&genre_id={self.genre.id}")
        self.assertEqual([movie["title"] for movie in filtered.data], ["Interstellar"])
        ordered = self.client.get("/api/movies/?ordering=-rating")
        self.assertEqual(ordered.data[0]["title"], "Inception")
        self.assert_api_error(
            self.client.get("/api/movies/?ordering=duration"), 400, "bad_request"
        )

        self.assertEqual(self.client.delete(f"/api/movies/{movie_id}/").status_code, 204)

    def test_movie_validation_and_delete_with_session_conflict(self):
        invalid = self.client.post(
            "/api/movies/",
            {
                "title": "Broken movie",
                "description": "Invalid duration.",
                "genre_id": self.genre.id,
                "duration": 0,
                "rating": "5.0",
                "age_rating": "12+",
            },
            format="json",
        )
        self.assert_api_error(invalid, 400, "bad_request")

        Session.objects.create(
            movie=self.movie,
            hall=self.hall,
            start_time=timezone.make_aware(datetime(2026, 10, 20, 18, 0)),
            price=Decimal("200.00"),
        )
        self.assert_api_error(self.client.delete(f"/api/movies/{self.movie.id}/"), 409, "conflict")

    def test_hall_and_seat_crud_duplicate_and_related_delete(self):
        create_hall = self.client.post("/api/halls/", {"name": "Hall 2"}, format="json")
        self.assertEqual(create_hall.status_code, 201)
        hall_id = create_hall.data["id"]
        self.assertEqual(self.client.get(f"/api/halls/{hall_id}/").data["name"], "Hall 2")
        self.assertEqual(
            self.client.patch(f"/api/halls/{hall_id}/", {"name": "Small hall"}, format="json").status_code,
            200,
        )

        seat = self.client.post(
            "/api/seats/", {"hall_id": self.hall.id, "row": 1, "number": 1}, format="json"
        )
        self.assertEqual(seat.status_code, 201)
        seat_id = seat.data["id"]
        self.assertEqual(self.client.get(f"/api/seats/{seat_id}/").data["number"], 1)
        self.assertEqual(
            self.client.patch(f"/api/seats/{seat_id}/", {"number": 2}, format="json").status_code,
            200,
        )
        hall_seats = self.client.get(f"/api/halls/{self.hall.id}/seats/")
        self.assertEqual(hall_seats.status_code, 200)
        self.assertEqual(len(hall_seats.data), 1)
        all_seats = self.client.get("/api/seats/")
        self.assertEqual(all_seats.status_code, 200)
        self.assertEqual(len(all_seats.data), 1)
        self.assert_api_error(self.client.delete(f"/api/halls/{self.hall.id}/"), 409, "conflict")
        self.assertEqual(self.client.delete(f"/api/seats/{seat_id}/").status_code, 204)
        self.assertEqual(self.client.delete(f"/api/halls/{hall_id}/").status_code, 204)

        Seat.objects.create(hall=self.hall, row=1, number=3)
        duplicate = self.client.post(
            "/api/seats/", {"hall_id": self.hall.id, "row": 1, "number": 3}, format="json"
        )
        self.assert_api_error(duplicate, 400, "bad_request")

    def test_session_crud_filters_conflict_and_session_seats(self):
        Seat.objects.create(hall=self.hall, row=1, number=1)
        create = self.client.post("/api/sessions/", self.session_payload(), format="json")
        self.assertEqual(create.status_code, 201)
        session_id = create.data["id"]
        self.assertEqual(self.client.get(f"/api/sessions/{session_id}/").status_code, 200)
        update = self.client.patch(
            f"/api/sessions/{session_id}/", {"price": "250.00"}, format="json"
        )
        self.assertEqual(update.status_code, 200)
        self.assertEqual(update.data["price"], "250.00")

        filtered = self.client.get(
            f"/api/sessions/?movie_id={self.movie.id}&date=2026-10-20"
        )
        self.assertEqual(len(filtered.data), 1)
        seats = self.client.get(f"/api/sessions/{session_id}/seats/")
        self.assertEqual(seats.data[0]["is_available"], True)

        other_movie = self.make_movie(title="Short film", duration=90)
        conflict = self.client.post(
            "/api/sessions/",
            self.session_payload(movie_id=other_movie.id, start_time="2026-10-20T19:00:00Z"),
            format="json",
        )
        self.assert_api_error(conflict, 409, "conflict")
        self.assert_api_error(
            self.client.get("/api/sessions/?date=20-10-2026"), 400, "bad_request"
        )
        self.assertEqual(self.client.delete(f"/api/sessions/{session_id}/").status_code, 204)

    def test_session_invalid_foreign_key_and_cors(self):
        invalid = self.client.post(
            "/api/sessions/", self.session_payload(movie_id=9999), format="json"
        )
        self.assert_api_error(invalid, 400, "bad_request")

        allowed = self.client.get(
            "/api/genres/", HTTP_ORIGIN="http://localhost:5173"
        )
        self.assertEqual(allowed["Access-Control-Allow-Origin"], "http://localhost:5173")
        disallowed = self.client.get("/api/genres/", HTTP_ORIGIN="http://localhost:3000")
        self.assertNotIn("Access-Control-Allow-Origin", disallowed)

    def test_missing_detail_resources_return_consistent_404(self):
        for path in [
            "/api/movies/9999/",
            "/api/halls/9999/",
            "/api/seats/9999/",
            "/api/sessions/9999/",
        ]:
            with self.subTest(path=path):
                self.assert_api_error(self.client.get(path), 404, "not_found")
