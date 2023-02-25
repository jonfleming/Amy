import datetime
import functools
import json
import logging
import openai
import os
import random
import time

from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render, redirect
from django.urls import reverse
from django.views import generic
from django.utils import timezone
from django.contrib.auth import login, authenticate, logout
from django.contrib import messages
from django.contrib.auth.forms import AuthenticationForm

import numpy as np
from numpy.linalg import norm

from .models import Utterance, Response
from .forms import NewUserForm

logger = logging.getLogger(__name__)
openai.api_key = os.getenv("OPENAI_API_KEY")
COMPLETIONS_MODEL = "text-davinci-003"  # "text-ada-001"  # "text-davinci-003"
EMBEDDING_MODEL = "text-embedding-ada-002"
HOME = "chat:homepage"
SAVE = True


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

def homepage(request):
	return render(request=request, template_name='chat/home.html')

def register_request(request):
	if request.method == "POST":
		form = NewUserForm(request.POST)
		if form.is_valid():
			user = form.save()
			login(request, user)
			messages.success(request, "Registration successful." )
			return redirect(HOME)
		messages.error(request, "Unsuccessful registration. Invalid information.")
	form = NewUserForm()
	return render (request=request, template_name="chat/register.html", context={"register_form":form})

def login_request(request):
	if request.method == "POST":
		form = AuthenticationForm(request, data=request.POST)
		if form.is_valid():
			username = form.cleaned_data.get('username')
			password = form.cleaned_data.get('password')
			user = authenticate(username=username, password=password)
			if user is not None:
				login(request, user)
				messages.info(request, f"You are now logged in as {username}.")
				return redirect("/session")
			else:
				messages.error(request,"Invalid username or password.")
		else:
			messages.error(request,"Invalid username or password.")
	form = AuthenticationForm()
	return render(request=request, template_name="chat/login.html", context={"login_form":form})

def logout_request(request):
	logout(request)
	messages.info(request, "You have successfully logged out.") 
	return redirect(HOME)

def session(request):
    cur_time = time.time()
    logger.info('session::starting::')

    if request.method == 'GET':
        return render(request, 'chat/session.html', {'command': 'START', 'user': ''})

    data = json.loads(request.body)
    
    if 'response' in request.session:
        data['amy_text'] = request.session['response']

    response = handle_command(data)
    request.session['response'] = response['text']
    logger.info(f"session::ended::{ time.time() - cur_time }")
    
    return JsonResponse(response)


def handle_command(data):
    command = data['command']
    text = data['utterance']
    response = {}

    if command == 'START':
        response['user'] = ''
        response['text'] = open_file('start.txt')
        response['command'] = 'INTRO'
        return response
    elif command == 'INTRO':
        user = get_name(text)
        response['user'] = user
        response['command'] = 'CONTINUE'
        
        existing_user = Utterance.objects.filter(user=user).count()
        
        if existing_user > 0:
            template = open_file('welcome.txt')
        else:
            template = open_file('intro.txt')
        response['text'] = template_response(template, {'context': '', 'amy_text': '', 'user_text': '', 'user': user})
        return response
    else:
        return handle_conversation(data)


def save_utterance(text, vector, utterance_time, user):
    if SAVE:
        logger.info(F"Utterance: {utterance_time}: {user}: {text}")
        utterance = Utterance(
            utterance_text=text, utterance_vector=vector, utterance_time=utterance_time, user=user)
        utterance.save()

        return utterance
    else:
        return {}


def save_response(utterance, text):
    if SAVE:
        logger.info(F"Amy: {text}")
        utterance.response_set.create(response_text=text)
        utterance.save()


def handle_conversation(data):
    user_text = data['utterance']
    amy_text = data['amy_text'] or 'Tell me something about yourself.'
    user = data['user']
    result = get_embedding(user_text)
    vector = result['data'][0]['embedding']
    prompt_context = relevant_utterances(user_text, vector, user)

    response = {}
    response['user'] = user
    response['command'] = 'CONTINUE'

    utterance = save_utterance(user_text, vector, timezone.now(), user)

    try:
        result = completion(prompt_context, amy_text, user_text, user)
    except openai.error.RateLimitError as error:
        result = f'{open_file("rate-limit.txt")} {error}'

    if 'choices' not in result or len(result['choices']) == 0:
        logger.warning('get_completion_from_open_ai_failed')
        response['text'] = result
    else:
        response['text'] = result['choices'][0]['text'].strip(' \n')

    save_response(utterance, response['text'])    

    return response

#####  language processing  #########################################################


class RecentText():
    def __init__(self, text, score):
        self.text = text
        self.score = score

    def __str__(self):
        return self.text


class RelevantText():
    def __init__(self):
        self.relevant = []

    def append(self, text):
        self.relevant.append(text)

    def sort(self):
        return sorted(self.relevant, key=lambda x: x.score)

    def add(self, x, y):
        return str(x) + ' ' + str(y)

    def join(self):
        return functools.reduce(self.add, self.relevant, '')


def get_name(text):
    return text.split(' ')[-1]


def relevant_utterances(text, vector, user):
    cur_time = time.time()
    logger.info("get_relevant_utterances::starting::")
    logger.info(F"{user}: {text}")

    relevant = RelevantText()
    since = timezone.now() - datetime.timedelta(days=7, seconds=1)
    result = Utterance.objects.filter(utterance_time__gte=since, user=user)[:7]
    for u in result:
        if (text != u.utterance_text):
            score = similarity(vector, u.embedding)
            relevant.append(RecentText(u.utterance_text, score))
            logger.info(F"Relevant Text: {score}: {u.utterance_text}")

    relevant.sort()
    logger.info(
        f"get_relevant_utterances::ended::{ time.time() - cur_time }")

    return relevant


def similarity(v1, v2):
    return np.dot(v1, v2)/(norm(v1)*norm(v2))  # return cosine similarity


def get_embedding(text: str, model: str = EMBEDDING_MODEL):
    if not SAVE:
        vector = [random.uniform(-1.0, 1.0) for _ in range(1536)]
        return {'data': [{'embedding': vector}]}

    cur_time = time.time()
    logger.info('get_embeddings_from_open_ai::starting::')
    result = openai.Embedding.create(
        model=model,
        input=text
    )
    logger.info(
        f"get_embeddings_from_open_ai::ended::{ time.time() - cur_time }")

    return result


def open_file(file):
    module_dir = os.path.dirname(__file__)
    file_path = os.path.join(module_dir, 'prompts', file)
    with open(file_path, 'r', encoding='utf-8') as infile:
        return infile.read()


def scramble(sentence):
    words = sentence.split()
    random.shuffle(words)
    return ' '.join(words)


def completion(context, amy_text, user_text, user):
    if not SAVE:
        return {'choices': [{'user_text': scramble(user_text)}]}

    cur_time = time.time()
    prompt = template_response(open_file('prompt.txt'),
        {'context': context.join(), 'amy_text': amy_text, 'user_text': user_text, 'user': user})

    logger.info(F'Amy_prompt: {prompt}')
    logger.info('get_completion_from_open_ai::starting::')
    response = openai.Completion.create(
        prompt=prompt,
        temperature=0,
        max_tokens=300,
        model=COMPLETIONS_MODEL,
        stop=['Amy:', f'{user}:']
    )
    logger.info(
        f'get_completion_from_open_ai::ended::{ time.time() - cur_time }')

    return response


def template_response(template, response):
    replacements = [('<<CONTEXT>>','context'), ('<<AMY>>','amy_text'), ('<<TEXT>>','user_text'), ('<<USER>>','user')]
    for phrase in replacements:
        template = template.replace(phrase[0], response[phrase[1]])
    return template
