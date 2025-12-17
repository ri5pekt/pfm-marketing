import { get, post, put, del } from './http'

export async function getRules(adAccountId = null) {
  const url = adAccountId
    ? `/app/meta-campaigns/rules?ad_account_id=${adAccountId}`
    : '/app/meta-campaigns/rules'
  return await get(url)
}

export async function getRule(ruleId) {
  return await get(`/app/meta-campaigns/rules/${ruleId}`)
}

export async function createRule(ruleData) {
  return await post('/app/meta-campaigns/rules', ruleData)
}

export async function updateRule(ruleId, ruleData) {
  return await put(`/app/meta-campaigns/rules/${ruleId}`, ruleData)
}

export async function deleteRule(ruleId) {
  return await del(`/app/meta-campaigns/rules/${ruleId}`)
}

export async function getRuleLogs(ruleId) {
  return await get(`/app/meta-campaigns/rules/${ruleId}/logs`)
}

export async function testRule(ruleId, signal = null) {
  return await post(`/app/meta-campaigns/rules/${ruleId}/test`, null, { signal })
}

export async function deleteRuleLog(ruleId, logId) {
  return await del(`/app/meta-campaigns/rules/${ruleId}/logs/${logId}`)
}

