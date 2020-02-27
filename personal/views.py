from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.views import generic
from django.utils import timezone

from .models import Choice, Question, Suggestion, Profile, ImageFile
from .forms import UploadFileForm, CreateNewProfileForm, ImageSearchForm
from .filesystem import handle_image_upload, handle_create_new_user

class ProfileView(generic.base.View):
    model = Profile

class IndexView(generic.ListView):
    template_name = 'personal/index.html'
    context_object_name = 'latest_question_list'

    def get_queryset(self):
        """
        Return the last five published questions (not including those set to be
        published in the future).
        """
        return Question.objects.filter(
            pub_date__lte=timezone.now()
        ).order_by('-pub_date')[:5]

class DetailView(generic.DetailView):
    model = Question
    template_name = 'personal/detail.html'
    def get_queryset(self):
        """
        Excludes any questions that aren't published yet.
        """
        return Question.objects.filter(pub_date__lte=timezone.now())


class ResultsView(generic.DetailView):
    model = Question
    template_name = 'personal/results.html'
    
    
def suggestions(request):
    try:
        name = request.POST['name']
        suggestion_text = request.POST['suggestion_text']
        suggestion = Suggestion(name=name, suggestion_text=suggestion_text,pub_date=timezone.now())
        suggestion.save()
    except:
        # Redisplay the question voting form.
        return render(request, 'personal/suggestion.html', {
            'error_message': "You didn't select a choice.",
        })
    else:
        # Always return an HttpResponseRedirect after successfully dealing
        # with POST data. This prevents data from being posted twice if a
        # user hits the Back button.
        return HttpResponseRedirect(reverse('personal:suggestionsList'))

def suggestionsList(request):
    suggestions = Suggestion.objects.filter(pub_date__lte=timezone.now()).order_by('-pub_date')
    context = {'suggestion_list': suggestions}
    return render(request, 'personal/list.html', context)

def index_view(request):
    if request.method == 'POST':
        dest = request.POST['dest']
        return HttpResponseRedirect('/user/' + dest)

    return render(request, 'personal/index.html')

def index(request):
    latest_question_list = Question.objects.order_by('-pub_date')[:5]
    context = {'latest_question_list': latest_question_list}
    return render(request, 'personal/index.html', context)

def index(request):
    return HttpResponse("What's good :)")

def detail(request, question_id):
    question = get_object_or_404(Question, pk=question_id)
    return render(request, 'personal/detail.html', {'question': question})

def results(request, question_id):
    question = get_object_or_404(Question, pk=question_id)
    return render(request, 'personal/results.html', {'question': question})

def vote(request, question_id):
    question = get_object_or_404(Question, pk=question_id)
    try:
        selected_choice = question.choice_set.get(pk=request.POST['choice'])
    except (KeyError, Choice.DoesNotExist):
        # Redisplay the question voting form.
        return render(request, 'personal/detail.html', {
            'question': question,
            'error_message': "You didn't select a choice.",
        })
    else:
        selected_choice.votes += 1
        selected_choice.save()
        # Always return an HttpResponseRedirect after successfully dealing
        # with POST data. This prevents data from being posted twice if a
        # user hits the Back button.
        return HttpResponseRedirect(reverse('personal:results', args=(question.id,)))
    
def profileView(request, profileID):
    profile_data = get_object_or_404(Profile, pk=profileID)
    return render(request, 'personal/profileview.html', {'profile_data': profile_data})

def upload_file(request):
    if request.method == 'POST':
        form = UploadFileForm(request.POST, request.FILES)
        #if form.is_valid():
        ret = 'image uploaded as ' + handle_image_upload(request.FILES['image'],request.FILES['image'].name ,request.POST['iid'], request.POST['tags'])
        return render(request, 'personal/success.html', {'actionID': ret})
    else:
        form = UploadFileForm()
    return render(request, 'personal/upload.html', {'form': form})

def serveImage(request, image_ID):
    return render(request, 'personal/singleImage.html', {'imageID': image_ID})

def create_user(request):
    if request.method == 'POST':
        form = CreateNewProfileForm(request.POST, request.FILES)
        #if form.is_valid():
        ret = 'user created as ' + handle_create_new_user(request.FILES['resume'], request.POST['pid'], request.POST['pword'], request.POST['bio'], request.POST['dname'])
        return render(request, 'personal/success.html', {'actionID': ret})
    else:
        form = CreateNewProfileForm()
    return render(request, 'personal/createProfile.html', {'form': form})

def imageSearch(request):
    if request.method == 'POST':
        form = ImageSearchForm(request.POST, request.FILES)
            #if form.is_valid():
        iids = ImageFile.objects.filter(tags__contains=request.POST['tag'])
        return render(request, 'personal/imageSearch.html', {'iids': iids})
    else:
        form = ImageSearchForm()
    return render(request, 'personal/imageSearch.html', {'form': form})