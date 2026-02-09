# Tune these numbers however you want.
# Format: (limit, window_seconds)

RULES = {
    # Auth
    "auth:signup_ip": (5, 60),         # 5 signups/min per IP
    "auth:login_ip": (5, 60),         # 10 login attempts/min per IP
    "auth:login_email": (5, 60),       # 5 login attempts/min per email (optional)

    # Topics
    "topics:create_user": (5, 60),     # 5 topics/min per user
    "topics:subscribe_user": (10, 60), # 20 subscribes/min per user
    "topics:unsubscribe_user": (10, 60),

    # Posts
    "posts:create_user": (5, 60),     # 10 posts/min per user
    "posts:update_user": (10, 60),
    "posts:delete_user": (10, 60),

    # Comments
    "comments:create_user": (10, 60),  # 30 comments/min per user
    "comments:update_user": (10, 60),
    "comments:delete_user": (10, 60),

    # Interactions
    "upvotes:toggle_user": (30, 60),   # 60/min per user
    "bookmarks:toggle_user": (30, 60),
}
