import datetime
import ast
import json
import logging
from typing import Any
from django.db.models.query import QuerySet
import openai
import os
import random
import time
import pinecone

from channels.db import database_sync_to_async
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.forms import PasswordResetForm
from django.contrib.auth.models import User
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail, BadHeaderError
from django.db.models.query_utils import Q
from django.http import HttpResponse
from django.http import JsonResponse
from django.shortcuts import render, redirect
from django.template.loader import render_to_string
from django.template import Context, Template, loader
from django.utils import timezone
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.views.decorators.csrf import csrf_exempt
from django.views.generic.list import ListView

import numpy as np
from numpy.linalg import norm

from .models import AmyPrompt, UserInput, AmyResponse, Profile, Category
from .forms import NewUserForm, ProfileForm

CHAT_MODEL = 'gpt-3.5-turbo'
COMPLETIONS_MODEL = 'text-davinci-003'
EMBEDDING_MODEL = 'text-embedding-ada-002'
HOME = 'chat:homepage'
PINECONE_INDEX = 'history'
USE_AVATAR = True
CATEGORIES = ['Childhood', 'Education', 'Career', 'Family', 'Spiritual', 'Story']

logger = logging.getLogger(__name__)
openai.api_key = os.getenv('OPENAI_API_KEY')
pinecone.init(os.getenv('PINECONE_API_KEY'), environment='us-east1-gcp')
pinecone_index = pinecone.Index(PINECONE_INDEX)

@csrf_exempt
def reindex(request):
    command = request.GET.get('command')    
    if command == 'pinecone':
        operation = 'Create Index'
        pinecone.create_index(PINECONE_INDEX, dimension=1536)
        user_input = UserInput.objects.all()
        for item in user_input:
            embedding = get_embedding(item.user_text)
            vector = embedding['data'][0]['embedding']
            save_vector(item.id, vector, item.user)
            logger.info(F'Saving {item.id} for {item.user}')
    elif command == 'classify':
        operation = 'Classify'
        user_input = UserInput.objects.all()
        categories = get_categories()
        category_list = ','.join(f"'{x}'" for x in categories )
        
        for item in user_input:
            args = {'<<TEXT>>': item.user_text, '<<CATEGORIES>>': category_list, '<<USER>>': item.user}
            prompt = render_template('classify.txt', args)
            result = completion(prompt).strip()
            
            if result in categories:
                item.category = result
                item.save()  
    
    elif command == 'save':
        operation = 'Save'
        body = json.loads(request.body.decode('utf-8'))        
        text = body['text']
        text_id = int(body['id'])
        
        user_input = UserInput.objects.filter(pk=text_id)[0]
        user_input.user_text = text
        user_input.save()
        
    return render(request, 'chat/session.html', {'command': "CONTINUE", 'speak': F'{operation} Complete.'})

@csrf_exempt
def profile_view(request):
    if request.method == 'GET':
        data = {
            'username': request.user.username,
            'first_name': request.user.first_name,
            'last_name': request.user.last_name,
            'email': request.user.email,
            'display_name': request.user.profile.display_name,
            'chat_mode': request.user.profile.chat_mode,
            'about_you': 'all about you'
        }
        form = ProfileForm(data)
    else:
        data = json.loads(request.body.decode('utf-8'))
        form = ProfileForm(data)    
        if form.is_valid():        
            user = request.user
            user.username = data['username']
            user.first_name = data['first_name']
            user.last_name = data['last_name']
            user.email = data['email']
            user.profile.display_name = data['display_name']
            user.profile.chat_mode = data['chat_mode']
            user.save()
            return HttpResponse(status=204)        
   
    return render(request, 'chat/profile.html', {'form': form})

@database_sync_to_async
def get_categories():
    categories = Category.objects.all()
    if (categories.count() == 0):
        # Initialize Category table
        categories = CATEGORIES
        for name in categories:
            embedding = get_embedding(name)
            vector = embedding['data'][0]['embedding']
            category = Category(name=name, vector=vector)
            category.save()
        
        categories = Category.objects.all()
    
    return [x.name for x in categories]

class SummaryOutput:
    def __init__(self, category, summarization, text):
        self.category = category
        self.summarization = summarization
        self.text = text
    
def summary(request):
    if request.method == 'GET':
        return render(request, 'chat/summary.html', {'summary': None})

def build_summary(username, category):
    try:
        user_input = UserInput.objects.filter(user=username, category=category)
    except:
        logger.error('Database query error.')
        raise
                
    text = ' '.join(x.user_text for x in user_input)
            
    if (text):
        prompt = render_template('summary.txt', {'<<TEXT>>': text})
        summarization = completion(prompt)
        summary_output = SummaryOutput(category, summarization, text)
            
        template = loader.get_template('chat/summary-sections.html')
        return template.render({'summary': summary_output})
    
    return None
    
class Transcript(ListView):    
    model = 'AmyResponse'
    context_object_name = 'transcript'
    template_name = 'chat/transcript.html'

    def get_queryset(self) -> QuerySet[Any]:
        return AmyResponse.objects.filter(user_input__user=self.request.user.username)[:100]
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['offset'] = int(self.kwargs['offset']) # browser timezone offset
        return context
    
def homepage(request):
    if not request.user.username:
        return render(request, 'chat/home.html')
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
				return send_reset_mail(request, user)
		messages.error(request, 'The entered email is not registered.')
	return render_reset(request, password_reset_form)

def render_reset(request, password_reset_form):
	return render(request=request, template_name="chat/password/password_reset.html", context={"password_reset_form":password_reset_form})

def send_reset_mail(request, user):
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

    args = {'<<TEXT>>': text, '<<USER>>': display_name}
    
    # Check for past conversations
    if past_conversations > 0 and request.user.profile.chat_mode != '':
        response['text'] = render_template('welcome.txt', args)
    else:
        response['text'] = render_template('intro.txt', args)

    response['user'] = display_name
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
    
    save_vector(user_input.id, vector, user)
    
def save_vector(id, vector, user):
    pinecone_index.upsert([(str(id), vector, { user: user })])

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
    relevant_context = relevant_user_text(user_text, vector, request.user.username)
    messages = conversation_history(relevant_context, prompt_text, user_text, request.user.profile.chat_mode)

    response = {}
    response['user'] = display_name
    response['command'] = 'CONTINUE'

    try:
        result = chat_completion(messages)
    except openai.error.RateLimitError as error:
        result = f"{open_file('rate-limit.txt')} {error}"

    response['text'] = first_chat_completion_choice(result)

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

    # Get similar user_input_ids from Pinecone
    relevant_texts = pinecone_index.query(vector=vector, top_k=3)
    ids = [match['id'] for match in relevant_texts['matches']]
    result = UserInput.objects.filter(user=user, pk__in=ids)
    relevant = get_relevant(text, result)

    relevant = RecentExchange.sort(relevant)        

    logger.info(f'get_relevant_user_text::ended::{ time.time() - cur_time }')

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
    file_path = os.path.join(module_dir, 'prompt_templates', file)
    with open(file_path, 'r', encoding='utf-8') as infile:
        return infile.read()

def chat_completion(messages):
    cur_time = time.time()

    logger.info(f'Chat messages: {json.dumps(messages, indent=4)}')
    logger.info('get_completion_from_open_ai::starting::')
    response = openai.ChatCompletion.create(
        messages=messages,
        temperature=0,
        max_tokens=300,
        model=CHAT_MODEL,
        presence_penalty=-1.0,
        frequency_penalty=1.0,
    )
    logger.info(
        f'get_completion_from_open_ai::ended::{ time.time() - cur_time }')

    return response

def render_template(template_name, args):
    text = open_file(template_name)
    for placeholder, value in args.items():
        text = text.replace(placeholder, value)
    return text

def conversation_history(exchanges, prompt_text, user_text, chat_mode):
    instruct = open_file(f'{chat_mode or "converse"}.txt')

    messages = [{'role': 'system', 'content': instruct}]

    for exchange in exchanges:
        messages.append({'role': 'assistant', 'content': exchange.prompt_text})
        messages.append({'role': 'user', 'content': exchange.user_text})

    messages.append({'role': 'assistant', 'content': prompt_text})
    messages.append({'role': 'user', 'content': user_text})

    return messages

def completion(prompt):
    cur_time = time.time()
    logger.info('Completion:')
    result = openai.Completion.create(model=COMPLETIONS_MODEL, prompt=prompt, max_tokens=300, top_p=1.0, n=1, stop=None)
    result = first_completion_choice(result)
    logger.info(f'session::ended::{ time.time() - cur_time }')
    
    return result

def first_chat_completion_choice(completion_response):
    if 'choices' not in completion_response or len(completion_response['choices']) == 0:
        logger.warning('get_chat_completion_from_open_ai_failed')
        response = completion_response
    else:
        response = completion_response.choices[0].message.content
    
    return response

def first_completion_choice(completion_response):
    if 'choices' not in completion_response or len(completion_response['choices']) == 0:
        logger.warning('get_completion_from_open_ai_failed')
        response = completion_response
    else:
        response = completion_response.choices[0].text
    
    return response
