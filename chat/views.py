from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.views import generic
from django.utils import timezone
from .models import Utterance, Response
import json
import os
import openai

openai.api_key = os.getenv("OPENAI_API_KEY")


class IndexView(generic.ListView):
    template_name = 'chat/index.html'
    context_object_name = 'recent_utterances'

    def get_queryset(self):
        return Utterance.objects.filter(time__lte=timezone.now()).order_by('-time')[:5]


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

    response = openai.Completion.create(
        model="text-davinci-003",
        prompt=text,
        max_tokens=7,
        temperature=0
    )

    if 'choices' in response:
        if len(response['choices']) > 0:
            context = {'user': user, 'utterance': text,
                       'response': response['choices'][0]['text']}
        else:
            context = {'user': user, 'utterance': text,
                       'response': 'unable to answer'}
    utterance.response_set.create(response_text=response)
    utterance.save()

    return render(request, 'chat/conversation.html', context)
