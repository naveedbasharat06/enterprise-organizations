<template>
  <div>
    <div class="page-header">
      <div>
        <div class="page-title">Screen Recording</div>
        <div class="page-sub">Record your screen or upload a video — get a timestamped transcript as a PDF</div>
      </div>
    </div>

    <!-- Tabs -->
    <div class="tab-bar">
      <button class="tab-btn" :class="{ active: tab === 'record' }" @click="tab = 'record'">🎥 Record Screen</button>
      <button class="tab-btn" :class="{ active: tab === 'upload' }" @click="tab = 'upload'">📁 Upload Video</button>
      <button class="tab-btn" :class="{ active: tab === 'history' }" @click="tab = 'history'">📋 My Recordings</button>
    </div>

    <!-- ── RECORD TAB ───────────────────────────────────────── -->
    <div v-if="tab === 'record'" class="card tab-panel">
      <div class="section-title">Record Your Screen</div>
      <p class="hint-text">
        Click <strong>Start Recording</strong> to capture your screen with audio. When done, give it a title and upload it for transcription.
      </p>

      <div v-if="!recordingBlob" class="record-controls">
        <button v-if="!isRecording" class="btn btn-primary btn-lg" @click="startRecording">
          ● Start Recording
        </button>
        <button v-else class="btn btn-danger btn-lg pulse" @click="stopRecording">
          ■ Stop Recording &nbsp;<span class="timer">{{ formatTime(elapsed) }}</span>
        </button>
      </div>

      <div v-if="recordingBlob" class="recorded-section">
        <video class="preview-video" :src="recordingURL" controls></video>
        <div class="form-group" style="margin-top:16px;">
          <label>Recording Title</label>
          <input class="form-control" v-model="recordTitle" placeholder="e.g. Product Demo Q2" />
        </div>
        <div v-if="uploadError" class="error-msg">{{ uploadError }}</div>
        <div class="record-controls" style="gap:12px;">
          <button class="btn btn-ghost" @click="discardRecording">Discard</button>
          <button class="btn btn-primary" @click="submitRecording" :disabled="uploading">
            <span v-if="uploading" class="spinner"></span>
            <span v-else>Upload &amp; Transcribe</span>
          </button>
        </div>
      </div>

      <div v-if="!isRecording && !recordingBlob" class="record-info">
        <div class="info-item">🖥️ Captures your full screen or a specific window</div>
        <div class="info-item">🎙️ Include audio from your microphone for transcription</div>
        <div class="info-item">📄 Get a timestamped PDF transcript automatically</div>
      </div>
    </div>

    <!-- ── UPLOAD TAB ───────────────────────────────────────── -->
    <div v-if="tab === 'upload'" class="card tab-panel">
      <div class="section-title">Upload a Video File</div>
      <p class="hint-text">Supported formats: MP4, WebM, MOV, MKV, MP3, WAV, M4A (any format Whisper accepts)</p>

      <div class="form-group">
        <label>Video / Audio File *</label>
        <input type="file" class="form-control" accept="video/*,audio/*" @change="onFileChange" ref="fileInputRef" />
      </div>
      <div class="form-group">
        <label>Title</label>
        <input class="form-control" v-model="uploadTitle" placeholder="e.g. Team Standup 2026-05-14" />
      </div>

      <div v-if="uploadedFile" class="file-preview">
        <span class="file-icon">🎬</span>
        <span>{{ uploadedFile.name }}</span>
        <span class="file-size">({{ (uploadedFile.size / 1024 / 1024).toFixed(2) }} MB)</span>
      </div>

      <div v-if="uploadError" class="error-msg">{{ uploadError }}</div>

      <div class="modal-footer" style="padding:0;margin-top:20px;">
        <button class="btn btn-primary" @click="submitUpload" :disabled="uploading || !uploadedFile">
          <span v-if="uploading" class="spinner"></span>
          <span v-else>Upload &amp; Transcribe</span>
        </button>
      </div>

      <div v-if="uploading" class="upload-progress">
        <div class="spinner large-spinner"></div>
        <div>Uploading video — transcription will run in the background...</div>
      </div>
    </div>

    <!-- ── HISTORY TAB ──────────────────────────────────────── -->
    <div v-if="tab === 'history'" class="card tab-panel">
      <div class="section-title">My Recordings</div>

      <div v-if="loadingHistory" class="loading-state">
        <div class="spinner"></div> Loading recordings...
      </div>

      <div v-else-if="recordings.length === 0" class="empty-state">
        <div class="empty-icon">🎬</div>
        <div>No recordings yet. Record your screen or upload a video to get started.</div>
      </div>

      <div v-else class="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Title</th>
              <th>Date</th>
              <th>Status</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="rec in recordings" :key="rec.id">
              <td style="font-weight:600;">{{ rec.title || 'Untitled' }}</td>
              <td style="color:var(--text-muted);font-size:13px;">{{ formatDate(rec.created_at) }}</td>
              <td>
                <span class="status-badge" :class="'status-' + rec.status">
                  {{ statusLabel(rec.status) }}
                </span>
              </td>
              <td>
                <div class="actions">
                  <a v-if="rec.pdf_url" :href="rec.pdf_url" target="_blank" class="btn btn-success btn-sm">
                    ⬇ Download PDF
                  </a>
                  <button v-if="rec.status === 'done'" class="btn btn-ghost btn-sm" @click="viewTranscript(rec)">
                    View Transcript
                  </button>
                  <button class="btn btn-danger btn-sm" @click="handleDelete(rec)">Delete</button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- Transcript Modal -->
    <div v-if="transcriptModal.show" class="modal-overlay" @click.self="transcriptModal.show = false">
      <div class="modal" style="width:640px;max-height:80vh;overflow-y:auto;">
        <div class="modal-header">
          <div class="modal-title">📄 {{ transcriptModal.title }}</div>
          <button class="modal-close" @click="transcriptModal.show = false">✕</button>
        </div>
        <div class="transcript-body">
          <div v-for="(seg, i) in transcriptModal.segments" :key="i" class="transcript-segment">
            <span class="ts-time">[{{ formatTime(Math.floor(seg.start)) }}]</span>
            <span class="ts-text">{{ seg.text }}</span>
          </div>
          <div v-if="!transcriptModal.segments.length" style="color:var(--text-muted);">No transcript data.</div>
        </div>
        <div class="modal-footer">
          <a v-if="transcriptModal.pdfUrl" :href="transcriptModal.pdfUrl" target="_blank" class="btn btn-success">
            ⬇ Download PDF
          </a>
          <button class="btn btn-ghost" @click="transcriptModal.show = false">Close</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted, onUnmounted } from 'vue'
import { useStore } from 'vuex'
import { getRecordings, uploadRecording, deleteRecording } from '@/api'

const store = useStore()

// ── state ──────────────────────────────────────────────────────────────────
const tab           = ref('record')
const isRecording   = ref(false)
const elapsed       = ref(0)
const recordingBlob = ref(null)
const recordingURL  = ref(null)
const recordTitle   = ref('')
const uploading     = ref(false)
const uploadError   = ref('')
const uploadedFile  = ref(null)
const uploadTitle   = ref('')
const fileInputRef  = ref(null)
const recordings    = ref([])
const loadingHistory = ref(false)

const transcriptModal = reactive({ show: false, title: '', segments: [], pdfUrl: null })

let mediaRecorder = null
let chunks        = []
let timerInterval = null
let screenStream  = null
let micStream     = null
let pollInterval  = null

// ── recording ──────────────────────────────────────────────────────────────
async function startRecording() {
  uploadError.value = ''
  screenStream = null
  micStream    = null
  try {
    // 1. Capture screen (video only — system audio is unreliable)
    screenStream = await navigator.mediaDevices.getDisplayMedia({ video: true, audio: false })

    // 2. Capture microphone separately so the user's voice is recorded
    try {
      micStream = await navigator.mediaDevices.getUserMedia({ audio: { echoCancellation: true, noiseSuppression: true } })
    } catch {
      uploadError.value = 'Microphone access denied — recording will have no audio for transcription.'
    }

    // 3. Combine screen video + mic audio into one stream
    const tracks = [
      ...screenStream.getVideoTracks(),
      ...(micStream ? micStream.getAudioTracks() : []),
    ]
    const combined = new MediaStream(tracks)

    chunks = []
    mediaRecorder = new MediaRecorder(combined)
    mediaRecorder.ondataavailable = e => { if (e.data.size > 0) chunks.push(e.data) }
    mediaRecorder.onstop = () => {
      screenStream?.getTracks().forEach(t => t.stop())
      micStream?.getTracks().forEach(t => t.stop())
      screenStream = null
      micStream    = null
      const blob = new Blob(chunks, { type: 'video/webm' })
      recordingBlob.value = blob
      recordingURL.value  = URL.createObjectURL(blob)
      stopTimer()
    }

    // If the user closes the browser share dialog (stops sharing), treat it as stop
    screenStream.getVideoTracks()[0].onended = () => stopRecording()

    mediaRecorder.start(1000)
    isRecording.value = true
    startTimer()
  } catch (e) {
    screenStream?.getTracks().forEach(t => t.stop())
    micStream?.getTracks().forEach(t => t.stop())
    screenStream = null
    micStream    = null
    if (e.name !== 'NotAllowedError') {
      uploadError.value = 'Could not start recording: ' + e.message
    }
  }
}

function stopRecording() {
  if (mediaRecorder && mediaRecorder.state !== 'inactive') {
    mediaRecorder.stop()
  }
  isRecording.value = false
}

function discardRecording() {
  URL.revokeObjectURL(recordingURL.value)
  recordingBlob.value = null
  recordingURL.value  = null
  recordTitle.value   = ''
  elapsed.value       = 0
  uploadError.value   = ''
}

async function submitRecording() {
  if (!recordingBlob.value) return
  uploading.value   = true
  uploadError.value = ''
  try {
    const fd = new FormData()
    fd.append('video', recordingBlob.value, (recordTitle.value || 'recording') + '.webm')
    fd.append('title', recordTitle.value || 'Screen Recording')
    const { data } = await uploadRecording(fd)
    recordings.value.unshift(data)
    store.dispatch('showToast', { message: 'Recording uploaded — transcription started!' })
    discardRecording()
    tab.value = 'history'
    startPolling()
  } catch (e) {
    uploadError.value = e.response?.data?.error || 'Upload failed. Please try again.'
  } finally {
    uploading.value = false
  }
}

// ── upload tab ─────────────────────────────────────────────────────────────
function onFileChange(e) {
  uploadedFile.value = e.target.files[0] || null
  uploadError.value  = ''
}

async function submitUpload() {
  if (!uploadedFile.value) return
  uploading.value   = true
  uploadError.value = ''
  try {
    const fd = new FormData()
    fd.append('video', uploadedFile.value)
    fd.append('title', uploadTitle.value || uploadedFile.value.name)
    const { data } = await uploadRecording(fd)
    recordings.value.unshift(data)
    store.dispatch('showToast', { message: 'Video uploaded — transcription started!' })
    uploadedFile.value = null
    uploadTitle.value  = ''
    if (fileInputRef.value) fileInputRef.value.value = ''
    tab.value = 'history'
    startPolling()
  } catch (e) {
    uploadError.value = e.response?.data?.error || 'Upload failed. Please try again.'
  } finally {
    uploading.value = false
  }
}

// ── history tab ────────────────────────────────────────────────────────────
async function loadRecordings() {
  loadingHistory.value = true
  try {
    const { data } = await getRecordings()
    recordings.value = data
    // Auto-start polling if any recording is still being processed
    if (hasActiveJobs()) startPolling()
  } catch {}
  finally { loadingHistory.value = false }
}

function hasActiveJobs() {
  return recordings.value.some(r => r.status === 'pending' || r.status === 'processing')
}

function startPolling() {
  if (pollInterval) return  // already polling
  pollInterval = setInterval(async () => {
    try {
      const { data } = await getRecordings()
      // Merge updates — only replace entries that changed status
      recordings.value = data
      if (!hasActiveJobs()) stopPolling()
    } catch {}
  }, 5000)
}

function stopPolling() {
  if (pollInterval) {
    clearInterval(pollInterval)
    pollInterval = null
  }
}

async function handleDelete(rec) {
  if (!confirm(`Delete "${rec.title || 'this recording'}"?`)) return
  try {
    await deleteRecording(rec.id)
    recordings.value = recordings.value.filter(r => r.id !== rec.id)
    store.dispatch('showToast', { message: 'Recording deleted' })
  } catch (e) {
    store.dispatch('showToast', { message: e.response?.data?.error || 'Delete failed', type: 'error' })
  }
}

function viewTranscript(rec) {
  transcriptModal.title    = rec.title || 'Transcript'
  transcriptModal.segments = rec.transcript_data?.segments || []
  transcriptModal.pdfUrl   = rec.pdf_url
  transcriptModal.show     = true
}

// ── helpers ────────────────────────────────────────────────────────────────
function startTimer() {
  elapsed.value = 0
  timerInterval = setInterval(() => { elapsed.value++ }, 1000)
}
function stopTimer() { clearInterval(timerInterval) }

function formatTime(totalSeconds) {
  const h = Math.floor(totalSeconds / 3600)
  const m = Math.floor((totalSeconds % 3600) / 60)
  const s = totalSeconds % 60
  return h > 0
    ? `${String(h).padStart(2,'0')}:${String(m).padStart(2,'0')}:${String(s).padStart(2,'0')}`
    : `${String(m).padStart(2,'0')}:${String(s).padStart(2,'0')}`
}

function formatDate(iso) {
  return new Date(iso).toLocaleString(undefined, { dateStyle: 'medium', timeStyle: 'short' })
}

function statusLabel(s) {
  return { pending: 'Pending', processing: 'Processing', done: 'Done', failed: 'Failed' }[s] || s
}

onMounted(loadRecordings)
onUnmounted(() => {
  stopTimer()
  stopPolling()
  if (isRecording.value) stopRecording()
  screenStream?.getTracks().forEach(t => t.stop())
  micStream?.getTracks().forEach(t => t.stop())
})
</script>

<style scoped>
.tab-bar { display: flex; gap: 8px; margin-bottom: 20px; }
.tab-btn {
  padding: 8px 20px; border: 1px solid var(--border); border-radius: 8px;
  background: var(--surface); color: var(--text-muted); cursor: pointer;
  font-size: 14px; transition: all .2s;
}
.tab-btn.active {
  background: var(--accent); color: #fff; border-color: var(--accent); font-weight: 600;
}
.tab-panel { padding: 28px; }
.section-title { font-size: 16px; font-weight: 700; margin-bottom: 8px; }
.hint-text { color: var(--text-muted); font-size: 13px; margin-bottom: 20px; }

.record-controls { display: flex; align-items: center; gap: 12px; margin: 20px 0; }
.btn-lg { padding: 12px 28px; font-size: 15px; }
.pulse { animation: pulse 1.5s infinite; }
@keyframes pulse { 0%,100%{ opacity:1 } 50%{ opacity:.7 } }
.timer { font-size: 13px; font-weight: 600; font-variant-numeric: tabular-nums; }

.preview-video { width: 100%; max-width: 600px; border-radius: 8px; background: #000; margin-bottom: 8px; }

.record-info { display: flex; flex-direction: column; gap: 10px; margin-top: 24px; }
.info-item { font-size: 14px; color: var(--text-muted); padding: 8px 12px; background: rgba(108,99,255,.06); border-radius: 6px; }

.file-preview {
  display: flex; align-items: center; gap: 10px; padding: 10px 14px;
  background: rgba(108,99,255,.06); border-radius: 8px; margin-top: 8px;
  font-size: 14px;
}
.file-icon { font-size: 20px; }
.file-size { color: var(--text-muted); font-size: 12px; }

.upload-progress {
  display: flex; align-items: center; gap: 12px; margin-top: 20px;
  color: var(--text-muted); font-size: 14px;
}
.large-spinner { width: 22px; height: 22px; }

.loading-state { display: flex; align-items: center; gap: 10px; color: var(--text-muted); padding: 20px 0; }

.status-badge {
  display: inline-block; padding: 2px 10px; border-radius: 12px;
  font-size: 12px; font-weight: 600; text-transform: capitalize;
}
.status-done       { background: rgba(40,200,100,.15); color: #28c864; }
.status-failed     { background: rgba(255,90,90,.15);  color: #ff5a5a; }
.status-processing { background: rgba(255,170,0,.15);  color: #f90; }
.status-pending    { background: rgba(150,150,150,.12); color: var(--text-muted); }

.transcript-body { padding: 16px 0; max-height: 50vh; overflow-y: auto; }
.transcript-segment { display: flex; gap: 12px; padding: 6px 0; align-items: flex-start; }
.ts-time { color: var(--accent); font-size: 12px; font-weight: 600; white-space: nowrap; padding-top: 2px; font-variant-numeric: tabular-nums; }
.ts-text { font-size: 14px; line-height: 1.6; }
</style>
