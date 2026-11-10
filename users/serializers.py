from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    role = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ["id", "username", "email", "first_name", "last_name", "role"]
        read_only_fields = ["id", "username", "role"]

    def get_role(self, user):
        return "admin" if user.is_staff else "user"

    def validate_email(self, value):
        value = value.strip().lower()
        if (
            User.objects.filter(email__iexact=value)
            .exclude(pk=self.instance.pk if self.instance else None)
            .exists()
        ):
            raise serializers.ValidationError("A user with this email already exists.")
        return value


class RegisterSerializer(UserSerializer):
    password = serializers.CharField(write_only=True, trim_whitespace=False)
    password_confirmation = serializers.CharField(
        write_only=True, trim_whitespace=False
    )

    class Meta(UserSerializer.Meta):
        fields = UserSerializer.Meta.fields + ["password", "password_confirmation"]
        read_only_fields = ["id", "role"]
        extra_kwargs = {
            "username": {"required": True},
            "email": {"required": True, "allow_blank": False},
            "first_name": {"required": False, "allow_blank": True},
            "last_name": {"required": False, "allow_blank": True},
        }

    def validate_username(self, value):
        if User.objects.filter(username__iexact=value).exists():
            raise serializers.ValidationError(
                "A user with this username already exists."
            )
        return value

    def validate(self, attrs):
        if attrs["password"] != attrs["password_confirmation"]:
            raise serializers.ValidationError(
                {"password_confirmation": "Passwords do not match."}
            )
        validate_password(attrs["password"], user=User(username=attrs["username"]))
        return attrs

    def create(self, validated_data):
        validated_data.pop("password_confirmation")
        password = validated_data.pop("password")
        return User.objects.create_user(password=password, **validated_data)


class ProfileSerializer(UserSerializer):
    class Meta(UserSerializer.Meta):
        read_only_fields = ["id", "username", "role"]
        extra_kwargs = {
            "email": {"required": False},
            "first_name": {"required": False, "allow_blank": True},
            "last_name": {"required": False, "allow_blank": True},
        }
