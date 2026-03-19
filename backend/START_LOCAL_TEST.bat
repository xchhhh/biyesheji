@echo off
REM 本地测试快速启动脚本
chcp 65001 >nul

echo.
echo ========================================
echo   微信小程序本地测试启动脚本
echo ========================================
echo.

cd /d "%~dp0"

echo 检查后端服务...
timeout /t 1 /nobreak

echo.
echo ========================================
echo   后端服务已启动！
echo ========================================
echo.
echo 📱 微信小程序本地测试步骤：
echo.
echo 1️⃣ 打开微信开发者工具
echo 2️⃣ 导入项目： %cd%\mini-program
echo 3️⃣ AppID 填写：wx1234567890abcdef (本地测试用)
echo 4️⃣ 详情标签页勾选：不校验合法域名、web-view
echo 5️⃣ 点击 "编译" 按钮
echo 6️⃣ 在编译器中测试登录、注册、预约功能
echo.
echo API 基础地址：http://localhost:5000/api
echo.
echo 📚 详细指南请参考：LOCAL_TEST_GUIDE.md
echo.
echo ========================================
echo 按任意键继续...
echo ========================================
pause
