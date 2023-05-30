const socket = new WebSocket('ws://localhost:8000/ws/chat/')

socket.onopen = function (e) {
  // don't do anything in onopen()
}

socket.onmessage = function (event) {
  // The form POST will get back a response but nothing needs to be done.
  // The server will send a chat completion when it is read
  // Completions can be queued here

  const data = JSON.parse(event.data)
  let response = data.response

  if (response) {
    // feed response into session
    // data = {user, text, command}
    if (user.value !== data.user) {
      user.value = data.user
      display_name.text = `Welcome, ${data.user}`
    }
    command.value = data.command
    const text = parse(data.text)
    appendResponse(text)
    speak(text)
    if (command.value == "START") {
      command.value = "INTRO"
    }
  }
}


socket.onerror = function (error) {
  console.log(`[error] ${error.message}`)
}
