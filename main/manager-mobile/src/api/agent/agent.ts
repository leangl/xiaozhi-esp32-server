import type {
  Agent,
  AgentCreateData,
  AgentDetail,
  AgentSnapshot,
  AgentSnapshotPageParams,
  CorrectWordFile,
  ModelOption,
  PageData,
  RoleTemplate,
  TtsVoice,
} from './types'
import { http } from '@/http/request/alova'

// Fetch agent details
export function getAgentDetail(id: string) {
  return http.Get<AgentDetail>(`/agent/${id}`, {
    meta: {
      ignoreAuth: false,
      toast: false,
    },
    cacheFor: {
      expire: 0,
    },
  })
}

// Fetch role templates
export function getRoleTemplates() {
  return http.Get<RoleTemplate[]>('/agent/template', {
    meta: {
      ignoreAuth: false,
      toast: false,
    },
    cacheFor: {
      expire: 0,
    },
  })
}

// Fetch model options
export function getModelOptions(modelType: string, modelName: string = '') {
  return http.Get<ModelOption[]>('/models/names', {
    params: {
      modelType,
      modelName,
    },
    meta: {
      ignoreAuth: false,
      toast: false,
    },
    cacheFor: {
      expire: 0,
    },
  })
}

// Fetch the agent list
export function getAgentList() {
  return http.Get<Agent[]>('/agent/list', {
    meta: {
      ignoreAuth: false,
      toast: false,
    },
    cacheFor: {
      expire: 0,
    },
  })
}

// Create an agent
export function createAgent(data: AgentCreateData) {
  return http.Post<string>('/agent', data, {
    meta: {
      ignoreAuth: false,
      toast: true,
    },
  })
}

// Delete an agent
export function deleteAgent(id: string) {
  return http.Delete(`/agent/${id}`, {
    meta: {
      ignoreAuth: false,
      toast: true,
    },
  })
}

// Fetch TTS voices
export function getTTSVoices(ttsModelId: string, voiceName: string = '') {
  return http.Get<TtsVoice[]>(`/models/${ttsModelId}/voices`, {
    params: {
      voiceName,
    },
    meta: {
      ignoreAuth: false,
      toast: false,
    },
    cacheFor: {
      expire: 0,
    },
  })
}

// Update an agent
export function updateAgent(id: string, data: Partial<AgentDetail> & { tagNames?: string[] }) {
  return http.Put(`/agent/${id}`, data, {
    meta: {
      ignoreAuth: false,
      toast: true,
    },
    cacheFor: {
      expire: 0,
    },
  })
}

// Fetch plugins
export function getPluginFunctions() {
  return http.Get<any[]>(`/models/provider/plugin/names`, {
    meta: {
      ignoreAuth: false,
      toast: false,
    },
    cacheFor: {
      expire: 0,
    },
  })
}

// Fetch the MCP endpoint
export function getMcpAddress(agentId: string) {
  return http.Get<string>(`/agent/mcp/address/${agentId}`, {
    meta: {
      ignoreAuth: false,
      toast: false,
      isExposeError: true,
    },
  })
}

// Fetch MCP tools
export function getMcpTools(agentId: string) {
  return http.Get<string[]>(`/agent/mcp/tools/${agentId}`, {
    meta: {
      ignoreAuth: false,
      toast: false,
    },
    cacheFor: {
      expire: 0,
    },
  })
}

// Fetch voiceprints
export function getVoicePrintList(agentId: string) {
  return http.Get<any[]>(`/agent/voice-print/list/${agentId}`, {
    meta: {
      ignoreAuth: false,
      toast: false,
    },
    cacheFor: {
      expire: 0,
    },
  })
}

// Fetch voice conversation history
export function getChatHistoryUser(agentId: string) {
  return http.Get<any[]>(`/agent/${agentId}/chat-history/user`, {
    meta: {
      ignoreAuth: false,
      toast: false,
    },
    cacheFor: {
      expire: 0,
    },
  })
}

// Add a voiceprint speaker
export function createVoicePrint(data: { agentId: string, audioId: string, sourceName: string, introduce: string }) {
  return http.Post('/agent/voice-print', data, {
    meta: {
      ignoreAuth: false,
      toast: true,
    },
  })
}

// Fetch agent tags
export function getAgentTags(agentId: string) {
  return http.Get<any[]>(`/agent/${agentId}/tags`, {
    meta: {
      ignoreAuth: false,
      toast: false,
    },
    cacheFor: {
      expire: 0,
    },
  })
}

// Update agent tags
export function updateAgentTags(agentId: string, data) {
  return http.Put(`/agent/${agentId}/tags`, data, {
    meta: {
      ignoreAuth: false,
      isExposeError: true,
    },
  })
}

// Fetch all languages
export function getAllLanguage(modelId: string) {
  return http.Get<TtsVoice[]>(`/models/${modelId}/voices`, {
    meta: {
      ignoreAuth: false,
      toast: false,
    },
    cacheFor: {
      expire: 0,
    },
  })
}

/**
 * Get a temporary playback ID for a cloned voice
 * @param cloneId Cloned voice record ID
 */
export function getVoiceCloneAudioId(cloneId: string) {
  return http.Post<string>(`/voiceClone/audio/${cloneId}`, {}, {
    meta: {
      ignoreAuth: false,
      toast: false,
    },
  })
}

// Fetch agent snapshot history
export function getAgentSnapshots(agentId: string, params: AgentSnapshotPageParams) {
  return http.Get<PageData<AgentSnapshot>>(`/agent/${agentId}/snapshots`, {
    params,
    meta: {
      ignoreAuth: false,
      toast: false,
    },
    cacheFor: {
      expire: 0,
    },
  })
}

// Fetch agent snapshot details
export function getAgentSnapshot(agentId: string, snapshotId: string) {
  return http.Get<AgentSnapshot>(`/agent/${agentId}/snapshots/${snapshotId}`, {
    meta: {
      ignoreAuth: false,
      toast: false,
    },
    cacheFor: {
      expire: 0,
    },
  })
}

// Restore an agent snapshot
export function restoreAgentSnapshot(agentId: string, snapshotId: string, currentStateToken: string) {
  return http.Post(`/agent/${agentId}/snapshots/${snapshotId}/restore`, { currentStateToken }, {
    meta: {
      ignoreAuth: false,
      toast: false,
    },
  })
}

// Delete an agent snapshot
export function deleteAgentSnapshot(agentId: string, snapshotId: string) {
  return http.Delete(`/agent/${agentId}/snapshots/${snapshotId}`, {
    meta: {
      ignoreAuth: false,
      toast: false,
    },
  })
}

// Fetch all replacement-word files
export function getCorrectWordFiles() {
  return http.Get<CorrectWordFile[]>('/correct-word/file/select', {
    meta: {
      ignoreAuth: false,
      toast: false,
    },
    cacheFor: {
      expire: 0,
    },
  })
}
