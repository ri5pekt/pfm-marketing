import { get, post, put, del } from './http'

export async function getAdAccounts() {
  return await get('/app/meta-campaigns/ad-accounts')
}

export async function getDefaultAdAccount() {
  return await get('/app/meta-campaigns/ad-accounts/default')
}

export async function getAdAccount(accountId) {
  return await get(`/app/meta-campaigns/ad-accounts/${accountId}`)
}

export async function createAdAccount(accountData) {
  return await post('/app/meta-campaigns/ad-accounts', accountData)
}

export async function updateAdAccount(accountId, accountData) {
  return await put(`/app/meta-campaigns/ad-accounts/${accountId}`, accountData)
}

export async function deleteAdAccount(accountId) {
  return await del(`/app/meta-campaigns/ad-accounts/${accountId}`)
}

export async function getAdAccountCampaigns(accountId) {
  return await get(`/app/meta-campaigns/ad-accounts/${accountId}/campaigns`)
}

export async function testAdAccountConnection(accountId) {
  return await post(`/app/meta-campaigns/ad-accounts/${accountId}/test-connection`)
}

export async function getCampaignAdSets(accountId, campaignId) {
  return await get(`/app/meta-campaigns/ad-accounts/${accountId}/campaigns/${campaignId}/adsets`)
}

export async function getAdSetAds(accountId, adsetId) {
  return await get(`/app/meta-campaigns/ad-accounts/${accountId}/adsets/${adsetId}/ads`)
}

