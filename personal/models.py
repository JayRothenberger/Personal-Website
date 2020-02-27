from django.db import models

import datetime

from django.db import models
from django.contrib.postgres import fields
from django.utils import timezone


class Question(models.Model):
    question_text = models.CharField(max_length=200)
    pub_date = models.DateTimeField('date published')
    def __str__(self):
        return self.question_text
    def was_published_recently(self):
        now = timezone.now()
        return now - datetime.timedelta(days=1) <= self.pub_date <= now


class Choice(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE)
    choice_text = models.CharField(max_length=200)
    votes = models.IntegerField(default=0)
    def __str__(self):
        return self.choice_text

class Suggestion(models.Model):
    pub_date = models.DateTimeField('date published')
    name = models.CharField(max_length=20)
    suggestion_text = models.CharField(max_length=280)
    def __str__(self):
        return self.suggestion_text

class ImageFile(models.Model):
    image_ID = models.CharField(max_length=32, primary_key=True)
    #tags = fields.ArrayField(models.CharField(max_length=15), null=True, blank=True)
    #the items in this field should be a string of comma-separated substrings
    tags = models.TextField(null = True)
    ext = models.CharField(max_length = 8, null=False)

class Profile(models.Model):
    profile_ID = models.CharField(max_length = 32, primary_key=True)
    resume = models.CharField(max_length = 32, null=True)
    bio = models.CharField(max_length = 280, null=True)
    display_Name = models.CharField(max_length = 64, null=False)
    pword = models.CharField(max_length = 64)
    
    
    
    