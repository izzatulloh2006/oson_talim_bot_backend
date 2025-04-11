from django.shortcuts import render
from .models import BotUser, FeedBack, Course, CourseVideo, Author
from .serializers import BotUserSerializer, FeedbackSerializer
from rest_framework.generics import ListCreateAPIView
from django.http import JsonResponse
from .models import Course, CourseVideo, Test, Startup
from rest_framework.viewsets import ModelViewSet
from .serializers import CourseSerializer, CourseVideoSerializer, StartupSerializer
from rest_framework.response import Response
from rest_framework.decorators import action
from django.shortcuts import get_object_or_404
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework import generics
from .models import Job, FreelanceProject, Institute
from .serializers import JobSerializer, FreelanceProjectSerializer, AuthorSerializer


class CourseAuthorsView(APIView):
    def get(self, request, course_id):
        course = Course.objects.get(id=course_id)
        authors = course.authors.all()
        data = [{
            'id': author.id,
            'full_name': author.full_name,
            'photo': author.photo.url if author.photo else None
        } for author in authors]
        return Response(data)


class AuthorVideosView(APIView):
    def get(self, request, author_id):
        course_id = request.query_params.get('course_id')
        if not course_id:
            return Response({'error': 'course_id is required'}, status=400)

        videos = CourseVideo.objects.filter(
            course_id=course_id,
            author_id=author_id
        ).order_by('uploaded_at')

        data = [{
            'id': video.id,
            'module_name': video.module_name,
            'video_file_id': video.video_file_id,
            'uploaded_at': video.uploaded_at
        } for video in videos]

        return Response(data)



class ActiveJobList(generics.ListAPIView):
    serializer_class = JobSerializer

    def get_queryset(self):
        lang = self.request.query_params.get('lang', 'uz')
        return Job.objects.filter(is_active=True, language=lang).order_by('-created_at')[:10]


class ActiveFreelanceProjectList(generics.ListAPIView):
    queryset = FreelanceProject.objects.all()
    serializer_class = FreelanceProjectSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CourseVideosByNameView(APIView):
    def get(self, request, course_name):
        course = get_object_or_404(Course, name=course_name)
        videos = CourseVideo.objects.filter(course=course)
        serializer = CourseVideoSerializer(videos, many=True)
        return Response(serializer.data)


class CourseViewSet(ModelViewSet):
    queryset = Course.objects.all()
    serializer_class = CourseSerializer

    @action(detail=True, methods=['get'])
    def videos(self, request, pk=None):
        course = self.get_object()
        videos = course.videos.all()
        serializer = CourseVideoSerializer(videos, many=True)
        return Response(serializer.data)


class CourseVideoViewSet(ModelViewSet):
    queryset = CourseVideo.objects.all()
    serializer_class = CourseVideoSerializer



class BotUserApiView(ListCreateAPIView):
    queryset = BotUser.objects.all()
    serializer_class = BotUserSerializer


class FeedbackApiView(ListCreateAPIView):
    queryset = FeedBack.objects.all()
    serializer_class = FeedbackSerializer




class InstituteView(APIView):
    def get(self, request, institute_id, format=None):
        try:
            # Bazadan institutni qidirish
            institute = Institute.objects.get(institute_id=institute_id)
            data = {
                "id": institute.id,
                "name": institute.name,
                "institute_id": institute.institute_id
            }
            return Response(data)
        except Institute.DoesNotExist:
            return Response(
                {"error": "Institut topilmadi"},
                status=status.HTTP_404_NOT_FOUND
            )


class StartupView(APIView):
    def get(self, request):
        startups = Startup.objects.filter(is_approved=True)
        serializer = StartupSerializer(startups, many=True)
        return Response(serializer.data)
    #
    # # Startapni yaratish (admin tasdiqlashidan so'ng)
    # def post(self, request):
    #     data = request.data
    #     serializer = StartupSerializer(data=data)
    #     if serializer.is_valid():
    #         serializer.save()
    #         return Response(serializer.data, status=status.HTTP_201_CREATED)
    #     return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)