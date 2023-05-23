const main = document.querySelector('.main')
const mainForm = document.getElementById('main_form')
const conversation = document.getElementById('conversation')
const user = document.getElementById('user')
const command = document.getElementById('command')
const user_text = document.getElementById('user_text')
const status = document.getElementById('status')
const submit = document.getElementById('submit')
const start = document.getElementById('start')
const display_name = document.getElementById('display_name')

if (command.value === "START" || command.value === "INTRO") {
  appendResponse("Click the speaker icon to enable speech")
  speechSynthesis.getVoices();
  setTimeout(myHandler, 3000);
}

document.addEventListener(
  'DOMContentLoaded',
  function () {
    mainForm.addEventListener('submit', (event) => {
      event.preventDefault()
      myHandler()
    })
  },
  false
)

async function myHandler() {
  appendUserText()
  postForm()
    .then((response) => response.json())
    .then((data) => {
      // data = {user, text, command}
      if (user.value !== data.user) {
        user.value = data.user;
        display_name.text = `Welcome, ${data.user}`;
      }
      command.value = data.command
      const text = parse(data.text)
      appendResponse(text)
      speak(text)
      if (command.value == 'START') {
        command.value = 'INTRO'
      }
    })

  return false
}

async function postForm() {
  const url = document.location.href
  const data = Object.fromEntries(new FormData(mainForm))

  const init = {
    method: 'POST',
    mode: 'cors',
    headers: {
      'Content-Type': 'application/json',
      Accept: 'application/json, text/plain, */*',
      'X-CSRFToken': data.csrfmiddlewaretoken,
    },
    body: JSON.stringify(data),
  }

  user_text.value = ''
  const response = await fetch(url, init)

  return response
}

function parse(text) {
  return text.replace('<<USER>>', user.textContent)
}

function appendUserText() {
  if (user_text.value) {
    conversation.innerHTML += `<p class="row w-85 float-end p-2 bubble-right mb-1 text-white rad bg-primary" 
      style="background-color: #f5f6f7">${user_text.value}</p>`
  }
}

function appendResponse(text) {
  if (text) {
    conversation.innerHTML += `<p class="row w-75 p-2 mb-1 text-white rad" 
      style="background-color: #8f8f8f">${text}</p>`
  }
  main.scrollTo(0, main.scrollHeight)
}

function showBox() {
 const msg = sessionStorage.getItem('msgbox')
 alert(msg) 
}
