"use strict"

const DID_API = { url: "https://api.d-id.com", key: "" }
const RTCPeerConnection = (
  window.RTCPeerConnection ||
  window.webkitRTCPeerConnection ||
  window.mozRTCPeerConnection
).bind(window)

let peerConnection
let streamId
let sessionId
let sessionClientAnswer
let bytesReceived = 0
let bytesSent = 0

const talkVideo = document.getElementById("talk-video")
talkVideo.setAttribute("playsinline", "")
const peerStatusLabel = document.getElementById("peer-status-label")
const iceStatusLabel = document.getElementById("ice-status-label")
const iceGatheringStatusLabel = document.getElementById(
  "ice-gathering-status-label"
)
const signalingStatusLabel = document.getElementById("signaling-status-label")
const dIdKey = document.getElementById("d-id-key")

talkVideo.addEventListener("ended", () => {
  console.log("**** Stream ended ****")
})

window.connect = async () => {
  DID_API.key = dIdKey.value
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
      source_url: "https://techion.net/Amy.png",
    }),
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
    console.log("error during streaming setup", e)
    stopAllStreams()
    closePC()
    return
  }

  await fetch(
    `${DID_API.url}/talks/streams/${streamId}/sdp`,
    {
      method: "POST",
      headers: {
        Authorization: `Basic ${DID_API.key}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        answer: sessionClientAnswer,
        session_id: sessionId,
      }),
    }
  )
}

window.talk = async (text) => {
  if (
    peerConnection?.signalingState === "stable" ||
    peerConnection?.iceConnectionState === "connected"
  ) {
    await fetch(`${DID_API.url}/talks/streams/${streamId}`, {
      method: "POST",
      headers: {
        Authorization: `Basic ${DID_API.key}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({
        script: {
          type: "text",
          subtitles: "false",
          provider: {
            type: "microsoft",
            voice_id: "en-US-SaraNeural",
            voice_config: {
              style: "Cheerful",
            },
          },
          ssml: true,
          input: text, // Use the user input as the input value
        },
        config: {
          fluent: true,
          pad_audio: 0,
          driver_expressions: {
            expressions: [
              { expression: "neutral", start_frame: 0, intensity: 0 },
            ],
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
        },
        driver_url: "bank://lively/",
        config: { stich: true },
        session_id: sessionId,
      }),
    })

    return "OK"
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

window.startStats = (callback) => {
  setInterval(() => {
    let isPlaying = false

    peerConnection.getStats(null).then((stats) => {
      const reports = [...stats].flat()      
      const inbound = reports.find(report => report?.type == 'inbound-rtp'  && report.kind == 'video')      
      const statsOutput = `<strong>Inbound bytes received:</strong> ${inbound?.bytesReceived}`
      
      document.querySelector(".stats-box").innerHTML = statsOutput

      if (inbound?.bytesReceived) {
        if (inbound?.bytesReceived !== bytesReceived) {
          isPlaying = true
          bytesReceived = inbound?.bytesReceived
        }

        if (!isPlaying) {
          console.log("Stopped Playing")
          callback()
        }
      }
    })
  }, 3000)
}

function onIceGatheringStateChange() {
  if (iceGatheringStatusLabel.innerText === "gathering") {
    iceGatheringStatusLabel.innerText = "🟡"
  }
  if (iceGatheringStatusLabel.innerText === "complete") {
    iceGatheringStatusLabel.innerText = "🟢"
  }
  iceGatheringStatusLabel.className =
    "iceGatheringState-" + peerConnection.iceGatheringState
}
function onIceCandidate(event) {
  console.log("onIceCandidate", event)
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
  if (peerConnection.iceConnectionState === "connected") {
    iceStatusLabel.innerText = "🟢"
  }
  if (peerConnection.iceConnectionState === "disconnected") {
    iceStatusLabel.innerText = "🔴"
  }
  if (peerConnection.iceConnectionState === "closed") {
    iceStatusLabel.innerText = "◯"
  }  
  iceStatusLabel.className =
    "iceConnectionState-" + peerConnection.iceConnectionState
  if (
    peerConnection.iceConnectionState === "failed" ||
    peerConnection.iceConnectionState === "closed"
  ) {
    stopAllStreams()
    closePC()
  }
}

function onConnectionStateChange() {
  // not supported in firefox
  if (peerConnection.connectionState === "connected") {
    peerStatusLabel.innerText = "🟢"
  }
  peerStatusLabel.className =
    "peerConnectionState-" + peerConnection.connectionState
}

function onSignalingStateChange() {
  if (peerConnection.signalingState === "stable") {
    signalingStatusLabel.innerText = "🟢"
  }

  signalingStatusLabel.className =
    "signalingState-" + peerConnection.signalingState
}

function onTrack(event) {
  console.log("Setting Remote Stream")
  const remoteStream = event.streams[0]
  setVideoElement(remoteStream)

  event.track.onended = function () {
    iceGatheringStatusLabel.innerText = "◯"
    console.log("A track has ended.")
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
  console.log("set remote sdp OK")

  const sessionClientAnswer = await peerConnection.createAnswer()
  console.log("create local sdp OK")

  await peerConnection.setLocalDescription(sessionClientAnswer)
  console.log("set local sdp OK")

  return sessionClientAnswer
}

function setVideoElement(stream) {
  if (!stream) return
  console.log("Setting Video Element")
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
    console.log("stopping video streams")
    talkVideo.srcObject.getTracks().forEach((track) => track.stop())
    talkVideo.srcObject = null
  }
}

function closePC(pc = peerConnection) {
  if (!pc) return
  console.log("stopping peer connection")
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
  iceGatheringStatusLabel.innerText = ""
  signalingStatusLabel.innerText = ""
  iceStatusLabel.innerText = ""
  peerStatusLabel.innerText = ""
  console.log("stopped peer connection")
  if (pc === peerConnection) {
    peerConnection = null
  }
}
