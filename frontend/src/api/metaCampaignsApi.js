import { get, post, put, del } from "./http";

export async function getRules(adAccountId = null) {
    const url = adAccountId ? `/app/meta-campaigns/rules?ad_account_id=${adAccountId}` : "/app/meta-campaigns/rules";
    return await get(url);
}

export async function getRule(ruleId) {
    return await get(`/app/meta-campaigns/rules/${ruleId}`);
}

export async function createRule(ruleData) {
    return await post("/app/meta-campaigns/rules", ruleData);
}

export async function updateRule(ruleId, ruleData) {
    return await put(`/app/meta-campaigns/rules/${ruleId}`, ruleData);
}

export async function deleteRule(ruleId) {
    return await del(`/app/meta-campaigns/rules/${ruleId}`);
}

export async function getRuleLogs(ruleId) {
    return await get(`/app/meta-campaigns/rules/${ruleId}/logs`);
}

export async function testRule(ruleId, signal = null) {
    return await post(`/app/meta-campaigns/rules/${ruleId}/test`, null, { signal });
}

export async function deleteRuleLog(ruleId, logId) {
    return await del(`/app/meta-campaigns/rules/${ruleId}/logs/${logId}`);
}

// Folder API functions
export async function getFolders(adAccountId) {
    return await get(`/app/meta-campaigns/folders?ad_account_id=${adAccountId}`);
}

export async function createFolder(folderData) {
    return await post("/app/meta-campaigns/folders", folderData);
}

export async function updateFolder(folderId, folderData) {
    return await put(`/app/meta-campaigns/folders/${folderId}`, folderData);
}

export async function deleteFolder(folderId) {
    return await del(`/app/meta-campaigns/folders/${folderId}`);
}

export async function reorderFolders(adAccountId, items) {
    return await post("/app/meta-campaigns/folders/reorder", {
        ad_account_id: adAccountId,
        items,
    });
}

export async function reorderRules(adAccountId, items) {
    return await post("/app/meta-campaigns/rules/reorder", {
        ad_account_id: adAccountId,
        items,
    });
}