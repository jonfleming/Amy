import os
import json
import logging
import random

from celery import Celery

logger = logging.getLogger(__name__)

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'Amy.settings')
app = Celery('Amy', broker='redis://localhost:6379/0')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()


@app.task(bind=True)
def classify_user_input(self, id):
    print(f'Classifying user input {id}')
    logger.info(f'Classifying user input {id}')
    
    # import chat.lang as lang
    # import chat.models as models

    # user_input = models.UserInput.objects.filter(pk=id)[0]
    # categories = lang.get_categories()
    # category_list = ','.join(f"'{x}'" for x in categories )
    # print(f"Category list: {category_list}")
    
    # args = {'<<TEXT>>': user_input.user_text, '<<CATEGORIES>>': category_list, '<<USER>>': user_input.user}
    # prompt = render_template('classify.txt', args)
    # result = lang.completion(prompt).strip()
    # print(f"Result: {result}")
    
    # if result in categories:
    #     user_input.category = result
    #     user_input.save()  
        
def render_template(template_name, args):
    import chat.lang as lang
    text = lang.open_file(template_name)
    for placeholder, value in args.items():
        text = text.replace(placeholder, value)
    return text

def render_random_template(json_file, args):
    module_dir = os.path.dirname(__file__)
    file_path = os.path.join(module_dir, 'prompt_templates', json_file)

    with open(file_path, 'r') as file:
        choices = json.load(file)

    text = random.choice(choices)

    for placeholder, value in args.items():
        text = text.replace(placeholder, value)
    return text
