from django.urls import path, include
from rest_framework.routers import DefaultRouter

from api.views import ReviewViewSet, CommentViewSet

app_name = 'api'


v1_router = DefaultRouter()
v1_router.register(
    r'titles/(?P<title_id>\d+)/reviews',
    ReviewViewSet,
    basename='reviews'
)
v1_router.register(
    r'titles/(?P<title_id>\d+)/reviews/(?P<review_id>\d+)/comments',
    CommentViewSet,
    basename='comments'
)

urlpatterns = [
    path('v1/', include(v1_router.urls)),
    path('', include(v1_router.urls)),

]
