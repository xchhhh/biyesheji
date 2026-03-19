# PowerShell 测试脚本 - 登录和注册 API

$APIUrl = "http://127.0.0.1:5000"

Write-Host "=" * 70 -ForegroundColor Cyan
Write-Host "API Testing Script for WeChat Mini Program Auth System" -ForegroundColor Green
Write-Host "=" * 70 -ForegroundColor Cyan

# 生成唯一的手机号和学号 (基于时间戳)
$timestamp = (Get-Date).ToString("HHmmssffff").Substring(0, 8)
$phoneNumber = "136" + $timestamp
$studentId = "202200" + $timestamp.Substring(0, 4)

Write-Host "`nGenerated Test Data:" -ForegroundColor Gray
Write-Host "Phone: $phoneNumber" -ForegroundColor Gray
Write-Host "Student ID: $studentId" -ForegroundColor Gray

# 测试 1: 注册新用户
Write-Host "`n[Test 1] Registering a new user..." -ForegroundColor Yellow

$registerBody = "{`"phone_number`":`"$phoneNumber`",`"password`":`"password123`",`"real_name`":`"Test User`",`"student_id`":`"$studentId`"}"

try {
    $registerResponse = Invoke-WebRequest -Uri "$APIUrl/api/auth/register" `
      -Method POST `
      -Headers @{"Content-Type"="application/json"} `
      -Body $registerBody `
      -UseBasicParsing

    $registerData = $registerResponse.Content | ConvertFrom-Json
    
    if ($registerResponse.StatusCode -eq 201) {
        Write-Host "[SUCCESS] User registered successfully!" -ForegroundColor Green
        Write-Host "User ID: $($registerData.data.user_id)" -ForegroundColor Green
        Write-Host "Phone: $($registerData.data.user.phone)" -ForegroundColor Green
        $userId = $registerData.data.user_id
        $token = $registerData.data.access_token
    } else {
        Write-Host "[FAILED] $($registerData.message)" -ForegroundColor Red
    }
} catch {
    Write-Host "[ERROR] Connection failed" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    exit 1
}

# 测试 2: 使用相同凭证登录
Write-Host "`n[Test 2] Logging in with the same credentials..." -ForegroundColor Yellow

$loginBody = "{`"phone_number`":`"$phoneNumber`",`"password`":`"password123`"}"

try {
    $loginResponse = Invoke-WebRequest -Uri "$APIUrl/api/auth/login" `
      -Method POST `
      -Headers @{"Content-Type"="application/json"} `
      -Body $loginBody `
      -UseBasicParsing

    $loginData = $loginResponse.Content | ConvertFrom-Json
    
    if ($loginResponse.StatusCode -eq 200) {
        Write-Host "[SUCCESS] User logged in successfully!" -ForegroundColor Green
        Write-Host "User ID: $($loginData.data.user_id)" -ForegroundColor Green
        Write-Host "Token: $($loginData.data.access_token.Substring(0,50))..." -ForegroundColor Green
    } else {
        Write-Host "[FAILED] $($loginData.message)" -ForegroundColor Red
    }
} catch {
    Write-Host "[ERROR] Login failed" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
}

# 测试 3: 测试错误的密码
Write-Host "`n[Test 3] Testing with wrong password..." -ForegroundColor Yellow

$wrongLoginBody = "{`"phone_number`":`"$phoneNumber`",`"password`":`"wrongpassword`"}"

try {
    $wrongLoginResponse = Invoke-WebRequest -Uri "$APIUrl/api/auth/login" `
      -Method POST `
      -Headers @{"Content-Type"="application/json"} `
      -Body $wrongLoginBody `
      -UseBasicParsing `
      -ErrorAction Stop
} catch {
    if ($_.Exception.Response.StatusCode -eq 401) {
        $errorStream = $_.Exception.Response.GetResponseStream()
        $reader = New-Object System.IO.StreamReader($errorStream)
        $wrongLoginData = $reader.ReadToEnd() | ConvertFrom-Json
        Write-Host "[SUCCESS] Wrong password correctly rejected!" -ForegroundColor Green
        Write-Host "Error message: $($wrongLoginData.message)" -ForegroundColor Green
    } else {
        Write-Host "[UNEXPECTED] $($_.Exception.Response.StatusCode)" -ForegroundColor Yellow
    }
}

# 测试 4: 测试重复注册
Write-Host "`n[Test 4] Testing duplicate registration with same phone..." -ForegroundColor Yellow

$duplicateBody = "{`"phone_number`":`"$phoneNumber`",`"password`":`"newpassword123`",`"real_name`":`"Another User`",`"student_id`":`"2022006666`"}"

try {
    $duplicateResponse = Invoke-WebRequest -Uri "$APIUrl/api/auth/register" `
      -Method POST `
      -Headers @{"Content-Type"="application/json"} `
      -Body $duplicateBody `
      -UseBasicParsing `
      -ErrorAction Stop
} catch {
    if ($_.Exception.Response.StatusCode -eq 400) {
        $errorStream = $_.Exception.Response.GetResponseStream()
        $reader = New-Object System.IO.StreamReader($errorStream)
        $duplicateData = $reader.ReadToEnd() | ConvertFrom-Json
        Write-Host "[SUCCESS] Duplicate phone correctly rejected!" -ForegroundColor Green
        Write-Host "Error message: $($duplicateData.message)" -ForegroundColor Green
    } else {
        Write-Host "[UNEXPECTED] $($_.Exception.Response.StatusCode)" -ForegroundColor Yellow
    }
}

Write-Host "`n" + ("=" * 70) -ForegroundColor Cyan
Write-Host "All tests completed!" -ForegroundColor Green
Write-Host ("=" * 70) -ForegroundColor Cyan
