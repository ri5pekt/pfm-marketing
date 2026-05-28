import { get, post, del } from './http'

export async function getUsers() {
  return await get('/users')
}

export async function createUser(data) {
  return await post('/users', data)
}

export async function deleteUser(id) {
  return await del(`/users/${id}`)
}
