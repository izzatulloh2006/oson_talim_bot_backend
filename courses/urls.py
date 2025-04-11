from django.urls import path, include
from .views import BotUserApiView, FeedbackApiView
from . import views
from .views import CourseViewSet, CourseVideoViewSet, CourseVideosByNameView, ActiveJobList, ActiveFreelanceProjectList, InstituteView, StartupView, CourseAuthorsView, AuthorVideosView
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register(r'courses', CourseViewSet)
router.register(r'videos', CourseVideoViewSet)


urlpatterns = [
    path('', include(router.urls)),
    path("courses/<str:course_name>/videos/", CourseVideosByNameView.as_view(), name="course-videos-by-name"),
    path('jobs/', ActiveJobList.as_view(), name='active-jobs'),
    path('institute/<str:institute_id>/', InstituteView.as_view(), name='institute_detail'),
    path('startups/', StartupView.as_view(), name='startups-list'),
    path('freelance/', ActiveFreelanceProjectList.as_view(), name='active-freelance'),
    path('courses/<int:course_id>/authors/', CourseAuthorsView.as_view()),
    path('authors/<int:author_id>/videos/', AuthorVideosView.as_view(), name='get_author_videos'),
    path('bot-users/', BotUserApiView.as_view(), name='bot-users'),
    path('feedback/', FeedbackApiView.as_view(), name='feedback'),
]