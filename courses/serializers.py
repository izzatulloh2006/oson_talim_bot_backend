from .models import  (
    BotUser, FeedBack, Course, CourseVideo,
    Test, Job, FreelanceProject, Institute, Startup, Author)
from rest_framework.serializers import ModelSerializer


class BotUserSerializer(ModelSerializer):
    class Meta:
        model = BotUser
        fields = ('name', "username", "user_id", "created_at")

class AuthorSerializer(ModelSerializer):
    class Meta:
        model = Author
        fields = '__all__'

class FeedbackSerializer(ModelSerializer):
    class Meta:
        model = FeedBack
        fields = ("user_id", "create_at", "body")


class CourseSerializer(ModelSerializer):
    class Meta:
        model = Course
        fields = ["id", "name", "lesson_count"]


class CourseVideoSerializer(ModelSerializer):
    class Meta:
        model = CourseVideo
        fields = ['id', 'module_name', 'video_file_id', 'uploaded_at']


class JobSerializer(ModelSerializer):
    class Meta:
        model = Job
        fields = ['id', 'title', 'description', 'salary', 'contact_info', ]

class FreelanceProjectSerializer(ModelSerializer):
    class Meta:
        model = FreelanceProject
        fields = ['id', 'title', 'description', 'budget', 'deadline', 'contact_email',]

class StartupSerializer(ModelSerializer):
    class Meta:
        model = Startup
        fields = ['id', 'name', 'description', 'creator', 'is_approved', 'created_at']

class InstituteSerializer(ModelSerializer):
    class Meta:
        model = Institute
        fields = '__all__'