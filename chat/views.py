import datetime
import functools
import json
import logging
import openai
import os
import random
import time
import pinecone

from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.utils import timezone
from django.contrib.auth import login, authenticate, logout
from django.contrib import messages
from django.contrib.auth.forms import AuthenticationForm
from django.core.mail import send_mail, BadHeaderError
from django.http import HttpResponse
from django.contrib.auth.forms import PasswordResetForm
from django.contrib.auth.models import User
from django.template.loader import render_to_string
from django.db.models.query_utils import Q
from django.utils.http import urlsafe_base64_encode
from django.contrib.auth.tokens import default_token_generator
from django.utils.encoding import force_bytes
from django.conf import settings

import numpy as np
from numpy.linalg import norm

from .models import AmyPrompt, UserInput, AmyResponse, Profile
from .forms import NewUserForm

COMPLETIONS_MODEL = 'gpt-3.5-turbo'
EMBEDDING_MODEL = 'text-embedding-ada-002'
HOME = 'chat:homepage'
USE_PINECONE = True
USE_AVATAR = True

logger = logging.getLogger(__name__)
openai.api_key = os.getenv('OPENAI_API_KEY')
pinecone.init(os.getenv('PINECONE_API_KEY'), environment='us-east1-gcp')
pinecone_index = pinecone.Index('history')

def summary(request):
    return render(request, 'chat/summary.html')

def transcript(request):
    return render(request, 'chat/transcript.html')

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
    else:
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

def password_reset_request(request):
	if request.method == "GET":
		password_reset_form = PasswordResetForm()
		return render_reset(request, password_reset_form)

	password_reset_form = PasswordResetForm(request.POST)
	if password_reset_form.is_valid():
		data = password_reset_form.cleaned_data['email']
		associated_users = User.objects.filter(Q(email=data))
		if associated_users.exists():
			for user in associated_users:
				return send_reset_mail(user)
		messages.error(request, 'The entered email is not registered.')
	return render_reset(request, password_reset_form)

def render_reset(request, password_reset_form):
	return render(request=request, template_name="chat/password/password_reset.html", context={"password_reset_form":password_reset_form})

def send_reset_mail(user):
	subject = "Password Reset Requested"
	email_template_name = "chat/password/password_reset_email.txt"
	context = {
	"email":user.email,
	'scheme_host':request._current_scheme_host,
	'site_name': 'Website',
	"uid": urlsafe_base64_encode(force_bytes(user.pk)),
	"user": user,
	'token': default_token_generator.make_token(user),
	}
	email = render_to_string(email_template_name, context)
	try:
		send_mail(subject, email, settings.EMAIL_HOST_USER , [user.email], fail_silently=False)
	except BadHeaderError:
		return HttpResponse('Invalid header found.')
	return redirect ("/password_reset/done/")
    

def session(request):
    if not request.user.username:
        return render(request=request, template_name='chat/home.html')

    cur_time = time.time()
    logger.info('session::starting::')

    if request.method == 'GET':
        command = 'START' if not hasattr(request.user, 'profile') else 'INTRO'
        return render(request, 'chat/session.html', {'command': command})

    data = json.loads(request.body)

    if 'prompt_id' in request.session:
        data['prompt_id'] = request.session['prompt_id']

    response = handle_command(request, data)
    logger.info(f'session::ended::{ time.time() - cur_time }')

    return JsonResponse(response)  # {user, text, command}


def handle_start(request):
    response = {}
    response['user'] = ''
    response['text'] = open_file('start.txt')
    response['command'] = 'INTRO'

    request.session['prompt_id'] = save_prompt(response['text'], '')
    return response


def handle_intro(request, data):
    text = data['user_text']
    display_name = ''
    response = {}
    response['command'] = 'CONTINUE'

    # Check if user has provided a name
    if not hasattr(request.user, 'profile') or request.user.profile.display_name == '':
        if text:
            display_name = save_parsed_name(request, text)
        else:
            return handle_start(request)
    else:
        display_name = request.user.profile.display_name

    past_conversations = UserInput.objects.filter(
        user=request.user.username).count()

    if past_conversations > 0:
        template = open_file('welcome.txt')
    else:
        template = open_file('intro.txt')

    response['user'] = display_name
    response['text'] = intro_response(
        template, {'user_text': text, 'display_name': display_name})

    request.session['prompt_id'] = save_prompt(response['text'], '')
    return response


def handle_command(request, data):
    command = data['command']

    if command == 'START':
        return handle_start(request)
    elif command == 'INTRO':
        return handle_intro(request, data)
    else:
        return handle_conversation(request, data)

def save_prompt(amy_text, message):
    amy_prompt = AmyPrompt(amy_text=amy_text, messages=message)
    amy_prompt.save()
    return amy_prompt.id
    
def save_interaction(user, amy_prompt, user_text, amy_text, vector):
    user_input = UserInput(user_text=user_text, user_vector = vector,
                           created_at=timezone.now(), user=user, amy_prompt=amy_prompt)
    user_input.save()
    amy_response = AmyResponse(amy_text=amy_text, user_input=user_input)
    amy_response.save()
    
    save_vector(user_input.id, vector)
    
def save_vector(id, vector):
    pinecone_index.upsert([(str(id), vector)])

def handle_conversation(request, data):
    default_prompt = 'Tell me something about yourself.'
    user_text = data['user_text']
    prompt_id = request.session['prompt_id'] if 'prompt_id' in request.session else None
    prompt_records = AmyPrompt.objects.filter(id=prompt_id)
    amy_prompt = prompt_records[0] if len(prompt_records) > 0 else AmyPrompt(default_prompt, '')
    prompt_text = amy_prompt.amy_text or default_prompt
    display_name = request.user.profile.display_name
    embedding = get_embedding(user_text)
    # To get embedding for Pinecone: embeds = [record['embedding'] for record in embedding['data']]
    vector = embedding['data'][0]['embedding']
    relevant_context = relevant_user_text(
        user_text, vector, request.user.username)
    messages = conversation_history(relevant_context, prompt_text, user_text, request.user.profile.chat_mode)

    response = {}
    response['user'] = display_name
    response['command'] = 'CONTINUE'

    try:
        result = completion(messages)
    except openai.error.RateLimitError as error:
        result = f"{open_file('rate-limit.txt')} {error}"

    if 'choices' not in result or len(result['choices']) == 0:
        logger.warning('get_completion_from_open_ai_failed')
        response['text'] = result
    else:
        response['text'] = result['choices'][0]['message']['content']

    message_string = ',\n'.join(
        F"{{role = \"{message['role']}\", content = \"{message['content']}\" }}" for message in messages)

    # Save AmyPrompt for future use
    request.session['prompt_id'] = save_prompt(response['text'], message_string)
    save_interaction(request.user.username, amy_prompt, user_text, response['text'], vector)

    return response

#####  Language Processing  #########################################################


class RecentExchange():
    def __init__(self, prompt_text, user_text, score = 0):
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
        request.user.profile.chat_mode = 'converse'
        request.user.save()
    else:
        profile = Profile(display_name=name, user=request.user, chat_mode = 'converse')
        profile.save()

    return name


def relevant_user_text(text, vector, user):
    cur_time = time.time()
    logger.info('get_relevant_user_text::starting::')
    logger.info(F'{user}: {text}')

    since = timezone.now() - datetime.timedelta(days=7, seconds=1)
    
    if USE_PINECONE:
        # Get similar user_input_ids from Pinecone
        relevant_texts = pinecone_index.query(vector=vector, top_k=3)
        ids = [match['id'] for match in relevant_texts['matches']]
        result = UserInput.objects.filter(user=user, created_at__gte=since, pk__in=ids)
        get_relevant(text, result)
    else:
        # Get recent rows from user_input and sort by score
        since = timezone.now() - datetime.timedelta(days=7, seconds=1)
        result = UserInput.objects.filter(userinput_created_at__gte=since, user=user)[:3]
        get_relevant(text, result)

    relevant = RecentExchange.sort(relevant)        

    logger.info(
        f'get_relevant_user_text::ended::{ time.time() - cur_time }')

    return relevant

def get_relevant(text, result):
    relevant = []
    for user_input in result:
        if (text != user_input.user_text):
            prompts = user_input.amyresponse_set.all()
            amy_text = prompts[0].amy_text if prompts.count() > 0 else ''
            relevant.append(RecentExchange(amy_text, user_input.user_text))
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


def conversation_history(exchanges, prompt_text, user_text, chat_mode):
    instruct = open_file(f'{chat_mode or "converse"}.txt')

    messages = [{'role': 'system', 'content': instruct}]

    for exchange in exchanges:
        messages.append({'role': 'assistant', 'content': exchange.prompt_text})
        messages.append({'role': 'user', 'content': exchange.user_text})

    messages.append({'role': 'assistant', 'content': prompt_text})
    messages.append({'role': 'user', 'content': user_text})

    return messages
