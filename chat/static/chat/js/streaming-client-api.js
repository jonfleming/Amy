"use strict"

const emoji = "&#x25AC;"

const DID_API = { url: "https://api.d-id.com", key: "", image: "" }
const RTCPeerConnection = (
  window.RTCPeerConnection ||
  window.webkitRTCPeerConnection ||
  window.mozRTCPeerConnection
).bind(window)

let peerConnection
let streamId
let sessionId
let sessionClientAnswer
let interval
let lastBytesReceived = 0
let bytesSent = 0
let isPlaying = false
let statsStarted = false
let triggered = false

const talkVideo = document.getElementById("talk-video")
talkVideo.setAttribute("playsinline", "")
const peerStatusLabel = document.getElementById("peer-status-label")
const iceStatusLabel = document.getElementById("ice-status-label")
const iceGatheringStatusLabel = document.getElementById(
  "ice-gathering-status-label"
)
const signalingStatusLabel = document.getElementById("signaling-status-label")
const dIdKey = document.getElementById("d-id-key")
const dIdImage = document.getElementById("d-id-image")

talkVideo.addEventListener("ended", () => {
  window.log("▭**** Stream ended ****")
})

window.connect = async () => {
  DID_API.key = dIdKey.value
  DID_API.image = dIdImage.value

  if (peerConnection && peerConnection.connectionState === "connected") {
    return
  }

  stopAllStreams()
  closePC()

  const sessionResponse = await fetch(`${DID_API.url}/talks/streams`, {
    method: "POST",
    headers: {
      Authorization: `Basic ${DID_API.key}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({
      source_url: DID_API.image,
    }),
  }).catch((e) => {
    window.log("▭ Error creating talk stream: " + e)
  })

  const {
    id: newStreamId,
    offer,
    ice_servers: iceServers,
    session_id: newSessionId,
  } = await sessionResponse.json()
  streamId = newStreamId
  sessionId = newSessionId

  try {
    sessionClientAnswer = await createPeerConnection(offer, iceServers)
  } catch (e) {
    window.log("▭ error during streaming setup", e)
    stopAllStreams()
    closePC()
    return
  }

  try {
    await fetch(`${DID_API.url}/talks/streams/${streamId}/sdp`, {
      method: "POST",
      headers: {
        Authorization: `Basic ${DID_API.key}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        answer: sessionClientAnswer,
        session_id: sessionId,
      }),
    })
  } catch (e) {
    window.log("▭ Error getting SDP: " + e)
  }
}

window.talk = async (text, errorHandler) => {
  if (
    peerConnection?.signalingState === "stable" ||
    peerConnection?.iceConnectionState === "connected"
  ) {
    const script = {
      type: "text",
      subtitles: "false",
      provider: {
        type: "microsoft",
        voice_id: "en-US-SaraNeural",
        voice_config: {
          style: "Cheerful",
          rate: "1.25",
        },
      },
      ssml: true,
      input: text, // Use the user input as the input value
    }
    const config = {
      fluent: true,
      pad_audio: 0,
      driver_expressions: {
        expressions: [{ expression: "neutral", start_frame: 0, intensity: 0 }],
        transition_frames: 0,
      },
      align_driver: true,
      align_expand_factor: 0,
      auto_match: true,
      motion_factor: 0,
      normalization_factor: 0,
      sharpen: true,
      stitch: true,
      result_format: "mp4",
    }

    const body = JSON.stringify({
      script: script,
      config: config,
      driver_url: "bank://lively/",
      config: { stich: true },
      session_id: sessionId,
    })

    fetch(`${DID_API.url}/talks/streams/${streamId}`, {
      method: "POST",
      headers: {
        Authorization: `Basic ${DID_API.key}`,
        "Content-Type": "application/json",
      },
      body: body,
    })
      .then((response) => {
        if (response.status == 402) {
          return response.text().then((text) => {
            throw new Error(`Out of credits ${text}`)
          })
        }
      })
      .catch((e) => {
        window.log("▭ Error retrieving video: " + e.message)
        errorHandler(text)
      })
  }
}

window.destroy = async () => {
  await fetch(`${DID_API.url}/talks/streams/${streamId}`, {
    method: "DELETE",
    headers: {
      Authorization: `Basic ${DID_API.key}`,
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ session_id: sessionId }),
  })

  stopAllStreams()
  closePC()
}

window.startStats = (callback, frequency) => {
  let hasStarted = false

  if (statsStarted) {
    return
  }

  window.log("▭ Starting Peer Connection Stats")
  statsStarted = true
  lastBytesReceived = 0

  interval = setInterval(() => {
    isPlaying = false

    peerConnection.getStats(null).then((stats) => {
      const reports = [...stats].flat()
      const inbound = reports.find(
        (report) => report?.type == "inbound-rtp" && report.kind == "video"
      )

      if (!triggered) {
        lastBytesReceived = inbound?.bytesReceived
        triggered = true
        
        window.log("▭ Playing has started")
        return
      }

      if (triggered && !hasStarted && inbound?.bytesReceived > lastBytesReceived) {        
        lastBytesReceived = inbound?.bytesReceived
        hasStarted = true

        window.log("▭ Playing was triggered")
        return
      }

      if (hasStarted) {        
        window.log("▭ hasStarted is true")

        if (inbound?.bytesReceived > lastBytesReceived) {
          isPlaying = true
          window.log(
            `▭ Bytes Received: ${lastBytesReceived} ${inbound?.bytesReceived}`
          )

          lastBytesReceived = inbound?.bytesReceived
          callback(false) // still playing
        } else {
          isPlaying = false
          hasStarted = false
          triggered = false

          window.log("▭ Stopped Playing")
          window.stopStats()
          callback(true) // done playing
        }
      }
    })
  }, frequency)
}

window.stopStats = () => {
  if (!statsStarted) {
    return
  }

  statsStarted = false
  window.log("▭ Stopping Peer Connection Stats")
  clearInterval(interval)
}

function setLabelStatus(label, status) {
  label.className = status
  const title = label.getAttribute("data-title")
  label.setAttribute("title", `${title} - ${status}`)
}

function onIceGatheringStateChange() {
  setLabelStatus(iceGatheringStatusLabel, peerConnection.iceGatheringState)
}

function onIceCandidate(event) {
  if (event.candidate) {
    const { candidate, sdpMid, sdpMLineIndex } = event.candidate

    fetch(`${DID_API.url}/talks/streams/${streamId}/ice`, {
      method: "POST",
      headers: {
        Authorization: `Basic ${DID_API.key}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        candidate,
        sdpMid,
        sdpMLineIndex,
        session_id: sessionId,
      }),
    })
  }
}

function onIceConnectionStateChange() {
  setLabelStatus(iceStatusLabel, peerConnection.iceConnectionState)

  if (
    peerConnection.iceConnectionState === "failed" ||
    peerConnection.iceConnectionState === "closed"
  ) {
    stopAllStreams()
    closePC()
  }
}

function onConnectionStateChange() {
  setLabelStatus(peerStatusLabel, peerConnection.connectionState)
  if (peerConnection.connectionState === "connected") {
    document.getElementById("connect-btn").style.display = "none"
  } else {
    document.getElementById("connect-btn").style.display = "block"
  }
}

function onSignalingStateChange() {
  setLabelStatus(signalingStatusLabel, peerConnection.signalingState)
}

function onTrack(event) {
  window.log("▭ Setting Remote Stream")
  const remoteStream = event.streams[0]
  setVideoElement(remoteStream)

  event.track.onended = function () {
    setLabelStatus(iceGatheringStatusLabel, peerConnection.iceGatheringState)
    window.log("▭ A track has ended.")
  }
}

async function createPeerConnection(offer, iceServers) {
  if (!peerConnection) {
    peerConnection = new RTCPeerConnection({ iceServers })
    peerConnection.addEventListener(
      "icegatheringstatechange",
      onIceGatheringStateChange,
      true
    )
    peerConnection.addEventListener("icecandidate", onIceCandidate, true)
    peerConnection.addEventListener(
      "iceconnectionstatechange",
      onIceConnectionStateChange,
      true
    )
    peerConnection.addEventListener(
      "connectionstatechange",
      onConnectionStateChange,
      true
    )
    peerConnection.addEventListener(
      "signalingstatechange",
      onSignalingStateChange,
      true
    )

    peerConnection.addEventListener("track", onTrack, true)
  }

  await peerConnection.setRemoteDescription(offer)
  window.log("▭ set remote sdp OK")

  const sessionClientAnswer = await peerConnection.createAnswer()
  window.log("▭ create local sdp OK")

  await peerConnection.setLocalDescription(sessionClientAnswer)
  window.log("▭ set local sdp OK")

  return sessionClientAnswer
}

function setVideoElement(stream) {
  if (!stream) return
  window.log("▭ Setting Video Element")
  talkVideo.srcObject = stream

  // safari hotfix
  if (talkVideo.paused) {
    talkVideo
      .play()
      .then((_) => {})
      .catch((e) => {})
  }
}

function stopAllStreams() {
  if (talkVideo.srcObject) {
    window.log("▭ stopping video streams")
    talkVideo.srcObject.getTracks().forEach((track) => track.stop())
    talkVideo.srcObject = null
  }
}

function closePC(pc = peerConnection) {
  if (!pc) return
  window.log("▭ stopping peer connection")
  pc.close()
  pc.removeEventListener(
    "icegatheringstatechange",
    onIceGatheringStateChange,
    true
  )
  pc.removeEventListener("icecandidate", onIceCandidate, true)
  pc.removeEventListener(
    "iceconnectionstatechange",
    onIceConnectionStateChange,
    true
  )
  pc.removeEventListener("connectionstatechange", onConnectionStateChange, true)
  pc.removeEventListener("signalingstatechange", onSignalingStateChange, true)
  pc.removeEventListener("track", onTrack, true)
  iceGatheringStatusLabel.className = ""
  signalingStatusLabel.className = ""
  iceStatusLabel.className = ""
  peerStatusLabel.className = ""
  window.log("▭ stopped peer connection")

  if (pc === peerConnection) {
    peerConnection = null
  }
}
