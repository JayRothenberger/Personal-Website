from django import forms

class UploadFileForm(forms.Form):
    title = forms.CharField(max_length=50)
    file = forms.FileField()
    
class CreateNewProfileForm(forms.Form):
    #null=true causes an error and I do not understand why
    pid = forms.CharField(max_length = 32)
    resume = forms.FileField()
    bio = forms.CharField(max_length = 280)
    dname = forms.CharField(max_length = 64)
    pword = forms.CharField(max_length = 64)

class ImageSearchForm(forms.Form):
    tag = forms.CharField(max_length = 32)