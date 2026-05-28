import { get, put } from './http'

export async function getSettings() {
  return await get('/settings')
}

export async function updateSettings(data) {
  return await put('/settings', data)
}
