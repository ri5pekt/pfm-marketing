import { get, post, put, del } from './http'

export async function getBusinessAccounts() {
  return await get('/app/meta-campaigns/business-accounts')
}

export async function getDefaultBusinessAccount() {
  return await get('/app/meta-campaigns/business-accounts/default')
}

export async function getBusinessAccount(accountId) {
  return await get(`/app/meta-campaigns/business-accounts/${accountId}`)
}

export async function createBusinessAccount(accountData) {
  return await post('/app/meta-campaigns/business-accounts', accountData)
}

export async function updateBusinessAccount(accountId, accountData) {
  return await put(`/app/meta-campaigns/business-accounts/${accountId}`, accountData)
}

export async function deleteBusinessAccount(accountId) {
  return await del(`/app/meta-campaigns/business-accounts/${accountId}`)
}

export async function getBusinessAccountCampaigns(accountId) {
  return await get(`/app/meta-campaigns/business-accounts/${accountId}/campaigns`)
}

export async function testBusinessAccountConnection(accountId) {
  return await post(`/app/meta-campaigns/business-accounts/${accountId}/test-connection`)
}

