# Container Apps Setup Script
# ACR admin enable + Container App creation
$ErrorActionPreference = "Continue"

Write-Host "=== Step 1: Enable ACR admin ===" -ForegroundColor Cyan
az acr update --name aiinterviewerdemo01 --admin-enabled true --output none 2>$null
Write-Host "ACR admin enabled"

Write-Host ""
Write-Host "=== Step 2: Get ACR credentials ===" -ForegroundColor Cyan
$acrCreds = az acr credential show --name aiinterviewerdemo01 --output json 2>$null | ConvertFrom-Json
$acrUser = $acrCreds.username
$acrPass = $acrCreds.passwords[0].value
Write-Host "ACR User: $acrUser"

Write-Host ""
Write-Host "=== Step 3: Get Redis access key ===" -ForegroundColor Cyan
$redisKeys = az redis list-keys --resource-group ai-interviewer-demo-rg --name ai-interviewer-demo-redis-01 --output json 2>$null | ConvertFrom-Json
$redisKey = $redisKeys.primaryKey
Write-Host "Redis key obtained"

Write-Host ""
Write-Host "=== Step 4: Create Backend Container App ===" -ForegroundColor Cyan
az containerapp create `
  --name ai-interviewer-api `
  --resource-group ai-interviewer-demo-rg `
  --environment ai-interviewer-demo-env `
  --image aiinterviewerdemo01.azurecr.io/ai-interviewer-api:latest `
  --registry-server aiinterviewerdemo01.azurecr.io `
  --registry-username $acrUser `
  --registry-password $acrPass `
  --target-port 8000 `
  --ingress external `
  --cpu 1.0 `
  --memory 2.0Gi `
  --min-replicas 1 `
  --max-replicas 1 `
  --env-vars `
    "DATABASE_URL=postgresql+asyncpg://aiinterviewer:DemoPass4Azure2026!@ai-interviewer-demo-db-01.postgres.database.azure.com:5432/aiinterviewer?ssl=require" `
    "REDIS_URL=rediss://:${redisKey}@ai-interviewer-demo-redis-01.redis.cache.windows.net:6380/0" `
    "ENVIRONMENT=demo" `
    "SECRET_KEY=demo-secret-key-2026-azure-deploy" `
    "CORS_ORIGINS=*" `
    "LOG_LEVEL=info" `
  --output none 2>$null

Write-Host "Backend Container App created"

Write-Host ""
Write-Host "=== Step 5: Check Frontend image ===" -ForegroundColor Cyan
$webImage = az acr repository show-tags --name aiinterviewerdemo01 --repository ai-interviewer-web --output json 2>$null | ConvertFrom-Json
if ($webImage) {
    Write-Host "Frontend image found: $($webImage -join ', ')"

    Write-Host ""
    Write-Host "=== Step 6: Create Frontend Container App ===" -ForegroundColor Cyan

    $apiUrl = az containerapp show --name ai-interviewer-api --resource-group ai-interviewer-demo-rg --query "properties.configuration.ingress.fqdn" --output tsv 2>$null

    az containerapp create `
      --name ai-interviewer-web `
      --resource-group ai-interviewer-demo-rg `
      --environment ai-interviewer-demo-env `
      --image aiinterviewerdemo01.azurecr.io/ai-interviewer-web:latest `
      --registry-server aiinterviewerdemo01.azurecr.io `
      --registry-username $acrUser `
      --registry-password $acrPass `
      --target-port 3000 `
      --ingress external `
      --cpu 0.5 `
      --memory 1.0Gi `
      --min-replicas 1 `
      --max-replicas 1 `
      --env-vars `
        "NEXT_PUBLIC_API_URL=https://${apiUrl}" `
        "NEXT_PUBLIC_WS_URL=wss://${apiUrl}" `
        "NEXT_PUBLIC_ENVIRONMENT=demo" `
        "NODE_ENV=production" `
      --output none 2>$null

    Write-Host "Frontend Container App created"
} else {
    Write-Host "Frontend image not yet available. Run this script again after the ACR build completes." -ForegroundColor Yellow
}

Write-Host ""
Write-Host "=== Step 7: Show deployment URLs ===" -ForegroundColor Cyan
$apiFqdn = az containerapp show --name ai-interviewer-api --resource-group ai-interviewer-demo-rg --query "properties.configuration.ingress.fqdn" --output tsv 2>$null
$webFqdn = az containerapp show --name ai-interviewer-web --resource-group ai-interviewer-demo-rg --query "properties.configuration.ingress.fqdn" --output tsv 2>$null

Write-Host ""
Write-Host "========================================" -ForegroundColor Green
Write-Host "  DEPLOYMENT COMPLETE" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Green
Write-Host "  Backend API: https://$apiFqdn" -ForegroundColor White
Write-Host "  Frontend:    https://$webFqdn" -ForegroundColor White
Write-Host "========================================" -ForegroundColor Green
