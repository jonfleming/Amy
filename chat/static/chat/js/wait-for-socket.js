const socket = new WebSocket("ws://localhost:8000/ws/summary/")

socket.onopen = function (e) {
  // Send a message to the server to start the get_summary method
  const username = document.getElementById("username").value
  socket.send(JSON.stringify({ message: "get_summary", username }))

  // Display the spinner
  document.getElementById("spinner").style.display = "block"
}

socket.onmessage = function (event) {
  let data = JSON.parse(event.data)
  let summary = data.summary

  if (summary != 'END') {
    // Display the summary
    document.getElementById("summary").innerHTML += summary
  } else {
    // Hide the spinner
    document.getElementById("spinner").style.display = "none"
  }
}

socket.onerror = function (error) {
  console.log(`[error] ${error.message}`)
}

// Attach the WebSocket to the link click event
// setTimeout(() => {
//   socket.open()
// }, 2000)
