from django.db import models

import datetime

from django.db import models
from django.contrib.postgres import fields
from django.utils import timezone

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

class MatchDetail(models.Model):
    time = models.BigIntegerField(primary_key=True)
    data = models.TextField()

class MatchHistory(models.Model):
    time = models.BigIntegerField(primary_key=True)
    data = models.TextField()
    summoner = models.TextField()
    region = models.TextField()

class APICallHistory(models.Model):
    time = models.BigIntegerField(primary_key=True)
    desc = models.TextField()
    service = models.TextField(default='Riot', null=False)

class APIKey(models.Model):
    time = models.BigIntegerField(primary_key=True)
    key = models.TextField()
    service = models.TextField(default='Riot', null=False)
    
class KrogerServiceData(models.Model):
    time = models.BigIntegerField(primary_key=True)
    data = models.TextField() # {brands:[''], abv_dict:{'':float()},products:{'':''},price_size:{()},loc_id_list:['']}