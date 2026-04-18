import time
from rest_framework.authtoken.models import Token
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db.models import Q  # Added back for specific queries if needed
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from allauth.account.models import EmailAddress

# Ensure all your models are imported. If any of these are NOT in your community/models.py,
# you MUST comment them out, or Django will crash.
from community.models import (
    Follow,
    Group,
    StatusPost,
    Poll,
    PollOption,
    UserProfile,
    Skill,  # Explicitly keeping Skill for deep cleanup
    SkillCategory,  # Explicitly keeping SkillCategory for deep cleanup
    Education,  # Explicitly keeping Education for deep cleanup
    Experience,  # Explicitly keeping Experience for deep cleanup
    Comment,
    Like,  # Explicitly keeping Like for potential usage and cleanup
)

User = get_user_model()


def create_verified_user(user):
    """
    Bypasses mandatory email verification for Cypress test users.
    Ensures an EmailAddress record exists and is marked as verified.
    """
    EmailAddress.objects.update_or_create(
        user=user, email=user.email, defaults={"primary": True, "verified": True}
    )


class TestSetupAPIView(APIView):
    """
    A secure 'Backdoor' for E2E testing.
    Allows Cypress to manipulate the database directly in non-production environments.
    """

    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        # SECURITY SWITCH: Physically disable this entire view in production
        if getattr(settings, "ENVIRONMENT", "local") == "production":
            return Response(
                {"error": "Test utilities are disabled in production."},
                status=status.HTTP_404_NOT_FOUND,
            )

        action = request.data.get("action")
        data = request.data.get("data", {})

        try:
            with transaction.atomic():
                # --- ACTION: Create a single verified user (Handles prefix or explicit username) ---
                if action == "create_user":
                    if "username_prefix" in data:
                        username = f"{data.get('username_prefix')}_{int(time.time())}"
                    else:
                        username = data.get("username")

                    password = data.get("password", "Airtel@123")
                    email = data.get("email", f"{username}@cypresstest.com")

                    user, created = User.objects.get_or_create(
                        username=username, defaults={"email": email}
                    )
                    if created:
                        user.set_password(password)
                        user.save()

                    create_verified_user(user)
                    token, _ = Token.objects.get_or_create(user=user)

                    return Response(
                        {
                            "username": user.username,
                            "token": token.key,
                        },
                        status=status.HTTP_201_CREATED,
                    )

                # --- ACTION: Create an unverified user (for specific auth tests) ---
                elif action == "create_unverified_user":
                    username = data.get("username")
                    password = data.get("password")
                    email = data.get("email")

                    if not all([username, password, email]):
                        return Response(
                            {
                                "error": "Missing username, password, or email for unverified user."
                            },
                            status=status.HTTP_400_BAD_REQUEST,
                        )
                    user = User.objects.create_user(
                        username=username, email=email, password=password
                    )
                    # Do NOT call create_verified_user here
                    return Response(
                        {"message": f"Unverified user '{username}' created."},
                        status=status.HTTP_201_CREATED,
                    )

                # --- ACTION: Create two users (e.g., for Follow/Chat tests) ---
                elif action == "create_two_users":
                    uA_data, uB_data = data.get("userA", {}), data.get("userB", {})

                    user_a, _ = User.objects.get_or_create(
                        username=uA_data.get("username"),
                        defaults={
                            "email": f'{uA_data.get("username")}@cypresstest.com'
                        },
                    )
                    user_a.set_password(uA_data.get("password", "Airtel@123"))
                    user_a.save()
                    create_verified_user(user_a)

                    user_b, _ = User.objects.get_or_create(
                        username=uB_data.get("username"),
                        defaults={
                            "email": f'{uB_data.get("username")}@cypresstest.com'
                        },
                    )
                    user_b.set_password(uB_data.get("password", "Airtel@123"))
                    user_b.save()
                    create_verified_user(user_b)

                    return Response(
                        {"user_a_id": user_a.id, "user_b_id": user_b.id},
                        status=status.HTTP_201_CREATED,
                    )

                # --- ACTION: Create a user and a post immediately ---
                elif action == "create_user_and_post":
                    user_data, post_data = data.get("user", {}), data.get("post", {})
                    user, created = User.objects.get_or_create(
                        username=user_data.get("username"),
                        defaults={
                            "email": f'{user_data.get("username")}@cypresstest.com'
                        },
                    )
                    if created:
                        user.set_password(user_data.get("password", "Airtel@123"))
                        user.save()
                    create_verified_user(user)

                    if user_data.get("with_picture", False):
                        dummy_image = SimpleUploadedFile(
                            name="test_avatar.gif",
                            content=b"\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x80\x00\x00\xff\xff\xff\x00\x00\x00\x21\xf9\x04\x01\x00\x00\x00\x00\x2c\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02\x44\x01\x00\x3b",
                            content_type="image/gif",
                        )
                        profile, _ = UserProfile.objects.get_or_create(user=user)
                        profile.picture.save("test_avatar.gif", dummy_image, save=True)

                    StatusPost.objects.create(
                        author=user,
                        content=post_data.get("content", "Test Post Content"),
                    )
                    return Response(
                        {"message": "User and post created"},
                        status=status.HTTP_201_CREATED,
                    )

                # --- ACTION: Create User with Multiple Posts ---
                elif action == "create_user_with_posts":
                    username = data.get("username")
                    num_posts = data.get("num_posts", 10)
                    user, created = User.objects.get_or_create(
                        username=username,
                        defaults={"email": f"{username}@cypresstest.com"},
                    )
                    user.set_password("Airtel@123")
                    user.save()
                    create_verified_user(user)
                    UserProfile.objects.update_or_create(
                        user=user, defaults={"bio": "Scroll tester"}
                    )
                    for i in range(num_posts):
                        StatusPost.objects.create(
                            author=user, content=f"Test post {i+1} for {username}."
                        )
                    token, _ = Token.objects.get_or_create(user=user)
                    return Response(
                        {"username": user.username, "token": token.key},
                        status=status.HTTP_201_CREATED,
                    )

                # --- ACTION: Create a Single Post ---
                elif action == "create_post":
                    author = get_object_or_404(User, username=data.get("username"))
                    post = StatusPost.objects.create(
                        author=author, content=data.get("content")
                    )
                    return Response(
                        {"message": "Post created.", "post_id": post.id},
                        status=status.HTTP_201_CREATED,
                    )

                # --- ACTION: Create Follow Relationship ---
                elif action == "create_follow":
                    follower = get_object_or_404(User, username=data.get("follower"))
                    following = get_object_or_404(User, username=data.get("following"))
                    Follow.objects.get_or_create(follower=follower, following=following)
                    return Response(
                        {"message": "Follow created."}, status=status.HTTP_201_CREATED
                    )

                # --- ACTION: Create a Group ---
                elif action == "create_group":
                    # Uses creator_username to link to an already created user
                    creator = get_object_or_404(
                        User, username=data.get("creator_username")
                    )
                    group = Group.objects.create(
                        name=f"{data.get('name', 'Default Group')}-{int(time.time())}",  # Ensure default name
                        creator=creator,
                        privacy_level=data.get(
                            "privacy_level", "public"
                        ),  # Use provided or default to public
                    )
                    group.members.add(creator)
                    return Response(
                        {"slug": group.slug, "name": group.name},
                        status=status.HTTP_201_CREATED,
                    )

                # --- ACTION: Create a Post with a Poll ---
                elif action == "create_post_with_poll":
                    author = get_object_or_404(User, username=data.get("username"))
                    post = StatusPost.objects.create(
                        author=author,
                        content=data.get("poll_question", "Default Poll Question"),
                    )
                    poll = Poll.objects.create(
                        post=post,
                        question=data.get("poll_question", "Default Poll Question"),
                    )
                    for option_text in data["poll_options"]:
                        PollOption.objects.create(poll=poll, text=option_text)
                    return Response(
                        {"message": "Poll created"}, status=status.HTTP_201_CREATED
                    )

                # --- ACTION: Instant Password Reset Link (Replaces old 'mail.outbox' method) ---
                # This action now handles both 'get_password_reset_link' and 'get_last_email' for compatibility
                # --- ACTION: Instant Password Reset Link ---
                # --- ACTION: Instant Password Reset Link ---
                elif action in ["get_password_reset_link", "get_last_email"]:
                    email = data.get("email")
                    if not email:
                        return Response(
                            {"error": "Email is required for password reset link"},
                            status=status.HTTP_400_BAD_REQUEST,
                        )

                    user = get_object_or_404(User, email=email)

                    # ALIGNMENT: Use the exact same generator and encoder as serializers.py
                    from allauth.account.forms import default_token_generator
                    from allauth.account.utils import user_pk_to_url_str

                    uid = user_pk_to_url_str(user)
                    token = default_token_generator.make_token(user)

                    # Get FRONTEND_URL and ensure it doesn't have a double slash
                    frontend_url = getattr(settings, "FRONTEND_URL", "").rstrip("/")

                    # Construct the URL to match the Vue Router exactly
                    reset_link = f"{frontend_url}/auth/reset-password/{uid}/{token}/"

                    return Response({"link": reset_link}, status=status.HTTP_200_OK)

                # --- ACTION: Deep Cleanup (The Janitor) ---
                elif action == "cleanup":
                    # 1. Identify users by specific Cypress domain ONLY
                    users_to_delete = User.objects.filter(
                        Q(email__endswith="@cypresstest.com")
                        | Q(username__startswith="unverified_user_")
                    ).exclude(
                        is_superuser=True
                    )  # Exclude superusers for safety

                    # 2. Explicitly delete associated data to avoid ghost records
                    # Django's CASCADE will handle StatusPost, Comment, UserProfile for deleted users,
                    # but explicit deletion is good for related objects that might not cascade perfectly

                    # Delete objects linked to UserProfile
                    SkillCategory.objects.filter(
                        user_profile__user__in=users_to_delete
                    ).delete()
                    Skill.objects.filter(
                        category__user_profile__user__in=users_to_delete
                    ).delete()
                    Education.objects.filter(
                        user_profile__user__in=users_to_delete
                    ).delete()
                    Experience.objects.filter(
                        user_profile__user__in=users_to_delete
                    ).delete()

                    # Delete Comments and StatusPosts directly if they don't cascade (though they usually do)
                    Comment.objects.filter(author__in=users_to_delete).delete()
                    StatusPost.objects.filter(author__in=users_to_delete).delete()

                    # Delete Groups created by these users
                    Group.objects.filter(creator__in=users_to_delete).delete()

                    # 3. Finally, delete the test users (Triggers CASCADE for Profiles, Tokens, etc.)
                    users_deleted_count, _ = users_to_delete.delete()

                    return Response(
                        {
                            "status": "success",
                            "message": "Deep cleanup complete. Only test data removed.",
                            "users_deleted": users_deleted_count,
                        },
                        status=status.HTTP_200_OK,
                    )

            return Response(
                {"error": f"Action '{action}' is unknown or not supported."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception as e:
            # Enhanced error reporting for debugging Cypress tests
            return Response(
                {"error": str(e), "action": action, "data": data},
                status=status.HTTP_400_BAD_REQUEST,
            )
