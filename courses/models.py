from django.db import models
from django.utils.translation import gettext_lazy as _


class Author(models.Model):
    full_name = models.CharField(max_length=225)
    bio = models.TextField(blank=True)
    photo = models.ImageField(upload_to="authors", blank=True)

    def __str__(self):
        return self.full_name


class Course(models.Model):
    name = models.CharField(max_length=225)
    lesson_count = models.IntegerField(default=0)
    authors = models.ManyToManyField(Author, related_name='courses')

    def __str__(self):
        return f"{self.name} ({self.lesson_count})"


class CourseVideo(models.Model):
    course = models.ForeignKey(Course, related_name='videos', on_delete=models.CASCADE)
    author = models.ForeignKey(Author, related_name='videos', on_delete=models.CASCADE)
    module_name = models.CharField(max_length=225)
    video_file_id = models.CharField(max_length=225)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'course_video'
        ordering = ['uploaded_at']

    def __str__(self):
        return f"{self.module_name} - {self.course.name} - {self.author.full_name}"

class BotUser(models.Model):
    user_id = models.CharField(max_length=120, unique=True)
    name = models.CharField(max_length=120)
    username = models.CharField(max_length=120, null=True, blank=True)
    created_at = models.DateField(auto_now_add=True)

    def __str__(self):
        return str(self.name)


class FeedBack(models.Model):
    user_id = models.CharField(max_length=120, null=True, blank=True)
    create_at = models.DateTimeField(auto_now_add=True)
    body = models.CharField(max_length=120, null=True, blank=True)

    def __str__(self):
        return str(self.name)


class Test(models.Model):
    course_video = models.ForeignKey(CourseVideo, on_delete=models.CASCADE, related_name='tests')
    question = models.TextField(verbose_name="Question")  # Savol uchun maydon
    answer_a = models.CharField(max_length=255, verbose_name="Variant A")  # Variant A
    answer_b = models.CharField(max_length=255, verbose_name="Variant B")  # Variant B
    answer_c = models.CharField(max_length=255, verbose_name="Variant C")  # Variant C
    answer_d = models.CharField(max_length=255, verbose_name="Variant D")  # Variant D
    right_answer = models.CharField(
        max_length=1,
        choices=[('A', 'A'), ('B', 'B'), ('C', 'C'), ('D', 'D')],
        verbose_name="Right answer"
    )  # To‘g‘ri javob
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Test for {self.course_video}: {self.question[:50]}"


class UserAnswer(models.Model):
    user = models.ForeignKey('auth.User', on_delete=models.CASCADE)
    test = models.ForeignKey(Test, on_delete=models.CASCADE)
    user_choice = models.CharField(
        max_length=1,
        choices=[('A', 'A'), ('B', 'B'), ('C', 'C'), ('D', 'D')],
        verbose_name="User's answer"
    )
    created_at = models.DateTimeField(auto_now_add=True)



class Job(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField()
    salary = models.CharField(max_length=100)
    contact_info = models.CharField(max_length=255)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    language = models.CharField(max_length=2, choices=[
        ('uz', 'Uzbek'),
        ('ru', 'Russian'),
        ('en', 'English')
    ], default='uz')

    class Meta:
        verbose_name = _("Job")
        verbose_name_plural = _("Jobs")

    def __str__(self):
        return self.title


class FreelanceProject(models.Model):
    title = models.CharField(max_length=255)
    description = models.TextField()
    budget = models.CharField(max_length=100)
    deadline = models.DateField(null=True, blank=True)
    contact_email = models.CharField(max_length=225)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    language = models.CharField(max_length=2, choices=[
        ('uz', 'Uzbek'),
        ('ru', 'Russian'),
        ('en', 'English')
    ], default='uz')

    class Meta:
        verbose_name = _("Freelance Project")
        verbose_name_plural = _("Freelance Projects")

    def __str__(self):
        return self.title


class Startup(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    creator = models.CharField(max_length=255)
    is_approved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name



class Institute(models.Model):
    name = models.CharField(max_length=255)
    institute_id = models.TextField(max_length=10, unique=True)

    def __str__(self):
        return self.name

    def get_institute_by_id(institute_id: str):
        try:
            institute = Institute.objects.get(institute_id=institute_id)
            return institute.name
        except Institute.DoesNotExist:
            return None