import json
import chat.lang as lang
import logging
import openai
import os
import requests
import time

from django.db.models.query import QuerySet
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
from typing import Any

from .models import AmyPrompt, UserInput, AmyResponse, Profile, Category
from .forms import NewUserForm, ProfileForm
from chat.celery import classify_user_input, render_template
from dotenv import load_dotenv

load_dotenv()

HOME = 'chat:homepage'
D_ID_URL = 'https://api.d-id.com/talks'
D_ID_IMAGE = 'https://techion.net/girl2.jpg'
D_ID_API_KEY = os.getenv('D_ID_API_KEY')

logger = logging.getLogger(__name__)

@csrf_exempt
def reindex(request):
    command = request.GET.get('command')    
    index_user = request.GET.get('user')
    if command == 'pinecone':
        operation = 'Reindex'
        lang.reindex(index_user)
    elif command == 'classify':
        operation = 'Classify'
        user_input = UserInput.objects.all()
        categories = lang.get_categories()
        category_list = ','.join(f"'{x}'" for x in categories )
        
        for item in user_input:
            args = {'<<TEXT>>': item.user_text, '<<CATEGORIES>>': category_list, '<<USER>>': item.user}
            prompt = render_template('classify.txt', args)
            result = lang.completion(prompt).strip()
            
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
        
    return render(request, 'chat/session.html', {'command': "CONTINUE", 'speak': f'{operation} Complete.'})


    
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
            'about_you': request.user.profile.about_you,
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
            user.profile.about_you = data['about_you']
            user.profile.save()
            user.save()
            return HttpResponse(status=204)        
   
    return render(request, 'chat/profile.html', {'form': form})

class SummaryOutput:
    def __init__(self, category, summarization, text):
        self.category = category
        self.summarization = summarization
        self.text = text
    
def summary(request):
    if request.method == 'GET':
        proto = 'ws' if request.META['HTTP_X_FORWARDED_PROTO'] == 'http' else 'wss'
        ws_url = f'{proto}://{request.get_host()}/ws/summary/'
        return render(request, 'chat/summary.html', {'summary': None, 'wsUrl': ws_url })

def build_summary(username, category):
    try:
        # TODO: filter on chat_mode
        user_input = UserInput.objects.filter(user=username, category=category)
    except:
        logger.error('Database query error.')
        raise
                
    text = ' '.join(x.user_text for x in user_input)
            
    if (text):
        prompt = render_template('summary.txt', {'<<TEXT>>': text})
        summarization = lang.completion(prompt)
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
        return render(request, 'chat/session.html', {'command': command, 'key': D_ID_API_KEY, 'image': D_ID_IMAGE})

    data = json.loads(request.body)

    if 'prompt_id' in request.session:
        data['prompt_id'] = request.session['prompt_id']

    response = handle_command(request, data)
    logger.info(f'session::ended::{ time.time() - cur_time }')

    # Part of D-ID
    # get_video(response['text'])
    return JsonResponse(response)  # {user, text, command, }

def set_show_summary(user):
    if user.profile.show_summary == False:
        user.profile.show_summary = True
        user.profile.save()
        user.save()
    
def get_video(words):
    headers = {
        'accept':'application/json',
        'authorization': 'Basic dGVjaGlvbkBlbWFpbC5jb20:pn1OgUuBfx-Ibx7Aeelnj',
        'content-type': 'application/json'
    }
    payload = {
        'source': D_ID_IMAGE,
        'script': {
            'type': 'text',
            'input': words
        },
        'webhook': 'https://myhost.com/webhook'
    }
    
    requests.post(D_ID_URL, headers=headers, json=payload)
    
    
def handle_start(request):
    response = {}
    response['user'] = ''
    response['text'] = lang.open_file('start.txt')
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
            display_name = lang.save_parsed_name(request, text)
        else:
            return handle_start(request)
    else:
        display_name = request.user.profile.display_name

    past_conversations = UserInput.objects.filter(
        user=request.user.username).count()
    
    if past_conversations > 5:
        set_show_summary(request.user)

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
    
def save_interaction(user, amy_prompt, user_text, amy_text, vector, chat_mode):
    user_input = UserInput(user_text=user_text, user_vector=vector, chat_mode=chat_mode,
                           created_at=timezone.now(), user=user, amy_prompt=amy_prompt)
    user_input.save()
    amy_response = AmyResponse(amy_text=amy_text, user_input=user_input)
    amy_response.save()
    
    lang.save_vector(user_input.id, vector, user)
    classify_user_input.delay(user_input.id)
    
def handle_conversation(request, data):
    default_prompt = 'Tell me something about yourself.'
    user_text = data['user_text']
    prompt_id = request.session['prompt_id'] if 'prompt_id' in request.session else None
    prompt_records = AmyPrompt.objects.filter(id=prompt_id)
    amy_prompt = prompt_records[0] if len(prompt_records) > 0 else AmyPrompt(default_prompt, '')
    prompt_text = amy_prompt.amy_text or default_prompt
    display_name = request.user.profile.display_name
    embedding = lang.get_embedding(user_text)
    # To get embedding for Pinecone: embeds = [record['embedding'] for record in embedding['data']]
    vector = embedding['data'][0]['embedding']
    relevant_context = lang.relevant_user_text(user_text, vector, request.user.username)
    messages = lang.conversation_history(relevant_context, prompt_text, user_text, request.user.profile.chat_mode)

    response = {}
    response['user'] = display_name
    response['command'] = 'CONTINUE'

    try:
        result = lang.chat_completion(messages)
    except openai.error.RateLimitError as error:
        result = f"{lang.open_file('rate-limit.txt')} {error}"

    response['text'] = lang.first_chat_completion_choice(result)

    message_string = ',\n'.join(
        F"{{role = \"{message['role']}\", content = \"{message['content']}\" }}" for message in messages)

    # Save AmyPrompt for future use
    request.session['prompt_id'] = save_prompt(response['text'], message_string)
    save_interaction(request.user.username, amy_prompt, user_text, response['text'], vector, request.user.profile.chat_mode)
    return response


