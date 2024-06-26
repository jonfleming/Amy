import logging
import json
import os
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

import os
import time

import numpy as np
from numpy.linalg import norm
import chat.models as models
from asgiref.sync import sync_to_async
from dotenv import load_dotenv
from pinecone.grpc import PineconeGRPC as Pinecone
from pinecone import ServerlessSpec

load_dotenv()
CHAT_MODEL = 'gpt-3.5-turbo'
COMPLETIONS_MODEL = 'gpt-3.5-turbo-instruct'
EMBEDDING_MODEL = 'text-embedding-ada-002'
CATEGORIES = ['Childhood', 'Education', 'Career', 'Family', 'Spiritual', 'Story']

logger = logging.getLogger(__name__)
client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
# pinecone.init(os.getenv('PINECONE_API_KEY'), environment=os.getenv('PINECONE_ENVIRONMENT'))
index_name = os.getenv('PINECONE_INDEX')
pinecone = Pinecone(api_key=os.getenv('PINECONE_API_KEY'))
pinecone_index = pinecone.Index(index_name)

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

def create_index():
        if index_name not in pinecone.list_indexes().names():
            pinecone.create_index(
                name=index_name,
                dimension=1536,
                metric="cosine",
                spec=ServerlessSpec(
                    cloud='aws', 
                    region='us-west-2'
                ) 
            ) 
        
        pinecone_index = pinecone(index_name)
        user_input = models.UserInput.objects.all()

        for item in user_input:
            embedding = get_embedding(item.user_text)
            vector = embedding.data[0].embedding
            save_vector(item.id, vector, item.user)
            logger.info(f'Saving {item.id} for {item.user}')
    
def chat_completion(messages):
    cur_time = time.time()

    logger.info(f'Chat messages: {json.dumps(messages, indent=4)}')
    logger.info('get_completion_from_open_ai::starting::')
    response = client.chat.completions.create(
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

def completion(prompt):
    cur_time = time.time()
    logger.info('Completion:')
    result = client.completions.create(model=COMPLETIONS_MODEL, prompt=prompt, max_tokens=300, top_p=1.0, n=1, stop=None)
    result = first_completion_choice(result)
    logger.info(f'session::ended::{ time.time() - cur_time }')
    
    return result

def conversation_history(exchanges, prompt_text, user_text, chat_mode):
    instruct = open_file(f'{chat_mode or "converse"}.txt')

    messages = [{'role': 'system', 'content': instruct}]

    for exchange in exchanges:
        messages.append({'role': 'assistant', 'content': exchange.prompt_text})
        messages.append({'role': 'user', 'content': exchange.user_text})

    messages.append({'role': 'assistant', 'content': prompt_text})
    messages.append({'role': 'user', 'content': user_text})

    return messages

def first_chat_completion_choice(completion_response):
    if not hasattr(completion_response, 'choices') or len(completion_response.choices) == 0:
        logger.warning('get_chat_completion_from_open_ai_failed')
        response = completion_response
    else:
        response = completion_response.choices[0].message.content
    
    return response

def first_completion_choice(completion_response):
    if not hasattr(completion_response, 'choices') or len(completion_response.choices) == 0:
        logger.warning('get_completion_from_open_ai_failed')
        response = completion_response
    else:
        response = completion_response.choices[0].text
    
    return response

def get_embedding(text: str, model: str = EMBEDDING_MODEL):
    cur_time = time.time()
    logger.info('get_embeddings_from_open_ai::starting::')
    result = client.embeddings.create(model=model,
    input=text)
    logger.info(
        f'get_embeddings_from_open_ai::ended::{ time.time() - cur_time }')

    return result

@sync_to_async
def get_categories():
    categories = models.Category.objects.all()
    records = categories.count()

    if (records == 0):
        # Initialize Category table
        categories = CATEGORIES
        for name in categories:
            embedding = get_embedding(name)
            vector = embedding.data[0].embedding
            category = models.Category(name=name, vector=vector)
            category.save()
        
        categories = models.Category.objects.all()
    
    return [x.name for x in categories]

def get_relevant(text, result):
    relevant = []
    for user_input in result:
        if (text != user_input.user_text):
            prompts = user_input.amyresponse_set.all()
            amy_text = prompts[0].amy_text if prompts.count() > 0 else ''
            relevant.append(RecentExchange(amy_text, user_input.user_text))
    return relevant

def open_file(file):
    module_dir = os.path.dirname(__file__)
    file_path = os.path.join(module_dir, 'prompt_templates', file)
    with open(file_path, 'r', encoding='utf-8') as infile:
        return infile.read()

def parse_name(text):
    return text.split(' ')[-1].replace('.', '')


def relevant_user_text(text, vector, user):
    cur_time = time.time()
    logger.info('get_relevant_user_text::starting::')
    logger.info(f'{user}: {text}')

    # Get similar user_input_ids from Pinecone
    relevant_texts = pinecone_index.query(vector=vector, top_k=3, filter={"user": user})
    ids = [match['id'] for match in relevant_texts['matches']]
    result = models.UserInput.objects.filter(user=user, pk__in=ids)
    relevant = get_relevant(text, result)

    relevant = RecentExchange.sort(relevant)        

    logger.info(f'get_relevant_user_text::ended::{ time.time() - cur_time }')

    return relevant

def save_parsed_name(request, text):
    name = parse_name(text)
    if hasattr(request.user, 'profile'):
        request.user.profile.display_name = name
        request.user.profile.chat_mode = 'converse'
        request.user.save()
    else:
        profile = models.Profile(display_name=name, user=request.user, chat_mode = 'converse')
        profile.save()

    return name

def save_vector(id, vector, user):
    pinecone_index.upsert([(str(id), vector, { "user": user })])

def similarity(v1, v2):
    return np.dot(v1, v2)/(norm(v1)*norm(v2))  # return cosine similarity
