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

from .models import Utterance, Profile
from .forms import NewUserForm

logger = logging.getLogger(__name__)
openai.api_key = os.getenv('OPENAI_API_KEY')
COMPLETIONS_MODEL = 'gpt-3.5-turbo'
EMBEDDING_MODEL = 'text-embedding-ada-002'
HOME = 'chat:homepage'

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
    if not request.user.username:
        return render(request=request, template_name='chat/home.html')
    else:
        return redirect('/session')

def register_request(request):
    if request.method == 'POST':
        form = NewUserForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Registration successful.')
            return redirect(HOME)
        messages.error(
            request, 'Unsuccessful registration. Invalid information.')
    form = NewUserForm()
    return render(request=request, template_name='chat/register.html', context={'register_form': form})

def login_request(request):
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                messages.info(request, f'You are now logged in as {username}.')
                return redirect('/session')
            else:
                messages.error(request, 'Invalid username or password.')
        else:
            messages.error(request, 'Invalid username or password.')
    form = AuthenticationForm()
    return render(request=request, template_name='chat/login.html', context={'login_form': form})

def logout_request(request):
    logout(request)
    messages.info(request, 'You have successfully logged out.')
    return redirect(HOME)

def session(request):
    if not request.user.username:
        return render(request=request, template_name='chat/home.html')

    cur_time = time.time()
    logger.info('session::starting::')

    if request.method == 'GET':
        command = 'START' if not hasattr(request.user, 'profile') else 'INTRO'
        return render(request, 'chat/session.html', {'command': command})

    data = json.loads(request.body)

    if 'prompt_text' in request.session:
        data['prompt_text'] = request.session['prompt_text']

    response = handle_command(request, data)
    request.session['prompt_text'] = response['text']
    logger.info(f'session::ended::{ time.time() - cur_time }')

    return JsonResponse(response)  # {user, text, command}

def handle_start():
    response = {}
    response['user'] = ''
    response['text'] = open_file('start.txt')
    response['command'] = 'INTRO'

    return response

def handle_intro(request, data):
    text = data['utterance']
    display_name = ''
    response = {}
    response['command'] = 'CONTINUE'

    # Check if user has provided a name
    if not hasattr(request.user, 'profile') or request.user.profile.display_name == '':
        if text:
            display_name = save_parsed_name(request, text)
        else:
            return handle_start()
    else:
        display_name = request.user.profile.display_name

    past_conversations = Utterance.objects.filter(
        user=request.user.username).count()

    if past_conversations > 0:
        template = open_file('welcome.txt')
    else:
        template = open_file('intro.txt')

    response['user'] = display_name
    response['text'] = intro_response(
        template, {'user_text': text, 'display_name': display_name})

    return response

def handle_command(request, data):
    command = data['command']

    if command == 'START':
        return handle_start()
    elif command == 'INTRO':
        return handle_intro(request, data)
    else:
        return handle_conversation(request, data)

def save_utterance(text, vector, utterance_time, user):
    logger.info(F'Utterance: {utterance_time}: {user}: {text}')
    utterance = Utterance(
        utterance_text=text, utterance_vector=vector, utterance_time=utterance_time, user=user)
    utterance.save()

    return utterance

def save_prompt(utterance, text):
    logger.info(F'Amy: {text}')
    utterance.prompt_set.create(prompt_text=text)
    utterance.save()


def handle_conversation(request, data):
    user_text = data['utterance']
    prompt_text = data['prompt_text'] or 'Tell me something about yourself.'
    display_name = request.user.profile.display_name
    result = get_embedding(user_text)
    vector = result['data'][0]['embedding']
    relevant_context = relevant_utterances(
        user_text, vector, request.user.username)
    messages = conversation_history(relevant_context, prompt_text, user_text)

    response = {}
    response['user'] = display_name
    response['command'] = 'CONTINUE'

    utterance = save_utterance(user_text, vector, timezone.now(), request.user.username)

    try:
        result = completion(messages)
    except openai.error.RateLimitError as error:
        result = f"{open_file('rate-limit.txt')} {error}"

    if 'choices' not in result or len(result['choices']) == 0:
        logger.warning('get_completion_from_open_ai_failed')
        response['text'] = result
    else:
        response['text'] = result['choices'][0]['message']['content']

    save_prompt(utterance, prompt_text)

    return response

#####  Language Processing  #########################################################

class RecentExchange():
    def __init__(self, prompt_text, user_text, score):
        self.prompt_text = prompt_text
        self.user_text = user_text
        self.score = score

    def __str__(self):
        return self.text

    @staticmethod
    def sort(exchanges):
        return sorted(exchanges, key=lambda x: x.score)

def parse_name(text):
    return text.split(' ')[-1].replace('.', '')

def save_parsed_name(request, text):
    name = parse_name(text)
    if hasattr(request.user, 'profile'):
        request.user.profile.display_name = name
        request.user.save()
    else:
        profile = Profile(display_name=name, user=request.user)
        profile.save()

    return name

def relevant_utterances(text, vector, user):
    cur_time = time.time()
    logger.info('get_relevant_utterances::starting::')
    logger.info(F'{user}: {text}')

    relevant = []
    since = timezone.now() - datetime.timedelta(days=7, seconds=1)
    result = Utterance.objects.filter(utterance_time__gte=since, user=user)[:3]
    for u in result:
        if (text != u.utterance_text):
            score = similarity(vector, u.embedding)
            prompts = u.prompt_set.all()
            prompt = prompts[0].prompt_text if prompts.count() > 0 else ''
            relevant.append(RecentExchange(prompt, u.utterance_text, score))
            logger.info(F'Relevant Text: {score}: {u.utterance_text}')

    relevant = RecentExchange.sort(relevant)

    logger.info(
        f'get_relevant_utterances::ended::{ time.time() - cur_time }')

    return relevant


def similarity(v1, v2):
    return np.dot(v1, v2)/(norm(v1)*norm(v2))  # return cosine similarity


def get_embedding(text: str, model: str = EMBEDDING_MODEL):
    cur_time = time.time()
    logger.info('get_embeddings_from_open_ai::starting::')
    result = openai.Embedding.create(
        model=model,
        input=text
    )
    logger.info(
        f'get_embeddings_from_open_ai::ended::{ time.time() - cur_time }')

    return result


def open_file(file):
    module_dir = os.path.dirname(__file__)
    file_path = os.path.join(module_dir, 'response_templates', file)
    with open(file_path, 'r', encoding='utf-8') as infile:
        return infile.read()


def scramble(sentence):
    words = sentence.split()
    random.shuffle(words)
    return ' '.join(words)


def completion(messages):
    cur_time = time.time()

    logger.info(f'Chat messages: {messages}')
    logger.info('get_completion_from_open_ai::starting::')
    response = openai.ChatCompletion.create(
        messages=messages,
        temperature=0,
        max_tokens=300,
        model=COMPLETIONS_MODEL,
        presence_penalty=-1.0,
        frequency_penalty=1.0,
    )
    logger.info(
        f'get_completion_from_open_ai::ended::{ time.time() - cur_time }')

    return response

def intro_response(template, args):
    replacements = [('<<TEXT>>', 'user_text'), ('<<USER>>', 'display_name')]
    for phrase in replacements:
        template = template.replace(phrase[0], args[phrase[1]])
    return template


def conversation_history(exchanges, prompt_text, user_text):
    instruct = """
        You are Amy.  You ask thought-provoking questions about family and personal history.
        Capture highlights of a person's life. Everything from childhood, school, marriage, 
        retirement, and old age. Ask open-ended questions to get interesting responses.
    """
    messages = [{'role':'system', 'content': instruct}]

    for exchange in exchanges:
        messages.append({'role': 'assistant', 'content': exchange.prompt_text})
        messages.append({'role': 'user', 'content': exchange.user_text})

    messages.append({'role': 'assistant', 'content': prompt_text})
    messages.append({'role': 'user', 'content': user_text})
    
    return messages
