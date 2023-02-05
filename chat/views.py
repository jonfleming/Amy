from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.views import generic
from django.utils import timezone
from .models import Utterance, Response
import json


class IndexView(generic.ListView):
    template_name = 'chat/index.html'
    context_object_name = 'recent_utterances'

    def get_queryset(self):
        return Utterance.objects.order_by('-time')[:5]


class DetailView(generic.DetailView):
    model = Utterance
    template_name = 'chat/detail.html'


class ResultsView(generic.DetailView):
    model = Utterance
    template_name = 'chat/results.html'


def session(request):
    user = "Jon"
    if request.method == 'GET':
        return render(request, 'chat/session.html', {'user': user})

    data = json.loads(request.body)
    text = data['utterance']
    utterance = Utterance(utterance_text=text, time=timezone.now())
    utterance.save()  # Need primary key response record

    response = 'a new response'
    context = {'user': user, 'utterance': text, 'response': response}
    utterance.response_set.create(response_text=response)
    utterance.save()

    return render(request, 'chat/conversation.html', context)
