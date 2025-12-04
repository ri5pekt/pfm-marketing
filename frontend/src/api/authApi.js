import { post, get } from './http'

export async function loginApi(email, password) {
  return await post('/auth/login', { email, password })
}

export async function meApi() {
  return await get('/auth/me')
}

