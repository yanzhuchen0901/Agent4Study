param(
    [string]$ConfigPath = "ms_deploy.json",
    [string]$Token = $env:MODELSCOPE_API_TOKEN
)

$ErrorActionPreference = "Stop"

if (-not $Token) {
    throw "MODELSCOPE_API_TOKEN is required. Create a ModelScope access token and set it before running this script."
}

if (-not (Test-Path -Path $ConfigPath -PathType Leaf)) {
    throw "ModelScope config file not found: $ConfigPath"
}

$config = Get-Content -Raw -Path $ConfigPath | ConvertFrom-Json
$headers = @{
    Authorization = "Bearer $Token"
    "Content-Type" = "application/json"
}

$createBody = [ordered]@{
    repo_name = $config.repo_name
    owner = $config.owner
    display_name = $config.display_name
    license = $config.license
    private = $config.private
    description = $config.description
    cover_image = $config.cover_image
    sdk_type = $config.sdk_type
    hardware = $config.hardware
}
$body = $createBody | ConvertTo-Json -Depth 10
$baseUrl = "https://modelscope.cn/openapi/v1"

try {
    $createResponse = Invoke-RestMethod -Method Post -Uri "$baseUrl/studios" -Headers $headers -Body $body
    Write-Host "Studio created."
    $createResponse | ConvertTo-Json -Depth 10
} catch {
    $message = $_.Exception.Message
    Write-Host "Create request did not complete cleanly: $message"
    Write-Host "Continuing to deploy in case the Studio already exists."
}

$owner = [uri]::EscapeDataString($config.owner)
$repo = [uri]::EscapeDataString($config.repo_name)
$deployResponse = Invoke-RestMethod -Method Post -Uri "$baseUrl/studios/$owner/$repo/deploy" -Headers $headers
Write-Host "Deploy requested."
$deployResponse | ConvertTo-Json -Depth 10
