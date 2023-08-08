window.socket.onopen = function (e) {
  // Send a message to the server to start the get_summary method
  const username = document.getElementById('username').value
  socket.send(JSON.stringify({ message: 'get_summary', username }))

  // Display the spinner
  document.getElementById('spinner').style.display = 'block'
}

window.socket.onmessage = function (event) {
  const data = JSON.parse(event.data)
  const summary = data.summary

  if (summary != 'END') {
    // Display the summary
    document.getElementById('summary').innerHTML += summary
  } else {
    // Hide the spinner
    document.getElementById('spinner').style.display = 'none'
  }
}

window.socket.onerror = function (error) {
  console.log(`[error] ${error.message}`)
}
