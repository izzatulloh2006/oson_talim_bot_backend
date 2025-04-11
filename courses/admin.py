# myapp/admin.py
from django.contrib import admin
from .models import Course, CourseVideo, BotUser, FeedBack,Test, FreelanceProject, Job, Institute, Startup, Author



@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ('name', 'lesson_count')
    search_fields = ('name', )

@admin.register(CourseVideo)
class CourseVideoAdmin(admin.ModelAdmin):
    list_display = ('module_name', 'course', 'video_file_id', 'author', 'uploaded_at')
    list_filter = ('course', 'uploaded_at')
    search_fields = ('module_name', 'video_file_id')

@admin.register(Author)
class AuthorAdmin(admin.ModelAdmin):
    list_display = ('full_name',)
    search_fields = ('full_name',)

@admin.register(FreelanceProject)
class FreelanceProjectAdmin(admin.ModelAdmin):
    list_display = ('title', 'description', 'budget', 'deadline', 'contact_email', 'is_active')

# admin.site.register(FreelanceProject)
admin.site.register(Job)
admin.site.register(Institute)
admin.site.register(Startup)


# admin.site.register(BotUser)
admin.site.register(FeedBack)

#
# class CustomAdmin(admin.ModelAdmin):
#     class Media:
#         css = {
#             "all": ("css/custom_admin.css",)
#         }
#
# admin.site.register(BotUser, CustomAdmin)