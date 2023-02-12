import json
import os
import openai
import time
import datetime
import logging
import functools

from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.views import generic
from django.utils import timezone

import numpy as np
from numpy.linalg import norm

from .models import Utterance, Response

logger = logging.getLogger(__name__)
openai.api_key = os.getenv("OPENAI_API_KEY")
COMPLETIONS_MODEL = "text-davinci-003"
EMBEDDING_MODEL = "text-embedding-ada-002"
PROMPT = 'Answer the question as truthfully as possible using the provided text, and if\
 the answer is not contained within the text below, say "Sorry, I don\'t know".\n'


class IndexView(generic.ListView):
    template_name = 'chat/index.html'
    context_object_name = 'recent_utterances'

    def get_queryset(self):
        return Utterance.objects.filter(utterance_time__lte=timezone.now()).order_by('-utterance_time')[:5]


class DetailView(generic.DetailView):
    model = Utterance
    template_name = 'chat/detail.html'


class ResultsView(generic.DetailView):
    model = Utterance
    template_name = 'chat/results.html'


class RecentText():
    def __init__(self, text, score):
        self.text = text
        self.score = score

    def __str__(self):
        return self.text


class RelevantText():
    _relevant = []

    def append(self, text):
        self._relevant.append(text)

    def sort(self):
        return sorted(self._relevant, key=lambda x: x.score)

    def add(self, x, y):
        return str(x) + ' ' + str(y)

    def join(self):
        return functools.reduce(self.add, self._relevant)


def session(request):
    user = "Jon"
    if request.method == 'GET':
        return render(request, 'chat/session.html', {'user': user})

    data = json.loads(request.body)
    text = data['utterance']
    result = get_embedding(text)
    vector = result["data"][0]["embedding"]
    prompt_context = relevant_utterances(text, vector)

    utterance = Utterance(
        utterance_text=text, utterance_vector=str(vector), utterance_time=timezone.now())
    utterance.save()  # Need primary key response record

    result = completion(text, prompt_context)

    if 'choices' in result:
        if len(result['choices']) > 0:
            context = {'user': user, 'utterance': text,
                       'response': result['choices'][0]['text'].strip(" \n")}
        else:
            logger.warning("get_completion_from_open_ai_failed")
            context = {'user': user, 'utterance': text,
                       'response': 'I\'m unable to answer that'}
    utterance.response_set.create(response_text=context['response'])
    utterance.save()

    return render(request, 'chat/conversation.html', context)


def relevant_utterances(text, vector):
    cur_time = time.time()
    logger.info("get_relevant_utterances::starting::")

    relevant = RelevantText()
    since = timezone.now() - datetime.timedelta(days=1, seconds=1)
    result = Utterance.objects.filter(utterance_time__gte=since)[:5]
    for u in result:
        if (text != u.utterance_text):
            score = similarity(vector, u.embedding)
            relevant.append(RecentText(u.utterance_text, score))

    relevant.sort()
    logger.info(
        f"get_relevant_utterances::ended::{ time.time() - cur_time }")

    return relevant


def similarity(v1, v2):
    return np.dot(v1, v2)/(norm(v1)*norm(v2))  # return cosine similarity


def get_embedding(text: str, model: str = EMBEDDING_MODEL) -> list[float]:
    cur_time = time.time()
    logger.info("get_embeddings_from_open_ai::starting::")
    result = openai.Embedding.create(
        model=model,
        input=text
    )
    logger.info(
        f"get_embeddings_from_open_ai::ended::{ time.time() - cur_time }")

    return result


def completion(text, relevant_text):
    cur_time = time.time()
    context = relevant_text.join()
    prompt = PROMPT + context + '\n\nQ: ' + text + '\nA: '

    logger.info("INFO::get_completion_from_open_ai::starting::")
    response = openai.Completion.create(
        prompt=prompt,
        temperature=0,
        max_tokens=300,
        model=COMPLETIONS_MODEL
    )
    logger.info(
        f"INFO::get_completion_from_open_ai::ended::{ time.time() - cur_time }")

    return response
