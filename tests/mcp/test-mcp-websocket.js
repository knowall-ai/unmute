const { chromium } = require('playwright');
const { exec } = require('child_process');
const { promisify } = require('util');
const execAsync = promisify(exec);

async function testMCPWebSocket() {
  console.log('🎭 Starting MCP WebSocket Direct Test');
  console.log('=' .repeat(60));
  
  // Launch browser
  const browser = await chromium.launch({
    headless: false,
    args: ['--use-fake-ui-for-media-stream', '--autoplay-policy=no-user-gesture-required']
  });
  
  const context = await browser.newContext({
    permissions: ['microphone'],
    ignoreHTTPSErrors: true
  });
  
  const page = await context.newPage();
  
  // Enable console logging
  page.on('console', msg => {
    console.log(`🖥️  Browser console: ${msg.text()}`);
  });
  
  // Monitor WebSocket messages
  let wsConnection = null;
  page.on('websocket', ws => {
    console.log(`🌐 WebSocket created: ${ws.url()}`);
    wsConnection = ws;
    
    ws.on('framesent', event => {
      console.log(`📤 WS Sent: ${event.payload}`);
    });
    
    ws.on('framereceived', event => {
      console.log(`📥 WS Received: ${event.payload}`);
    });
  });
  
  try {
    // Step 1: Navigate to Unmute
    console.log('\n📍 Step 1: Navigating to http://localhost:3000');
    await page.goto('http://localhost:3000');
    
    await page.screenshot({ path: 'test-ws-1-loaded.png' });
    console.log('✅ Page loaded');
    
    await page.waitForTimeout(2000);
    
    // Step 2: Click Play button
    console.log('\n🎯 Step 2: Clicking Play button');
    const playButton = await page.locator('canvas.rounded-full.cursor-pointer');
    await playButton.waitFor({ state: 'visible', timeout: 10000 });
    await playButton.click();
    console.log('✅ Clicked Play button');
    
    // Wait for WebSocket connection
    console.log('⏳ Waiting for WebSocket connection...');
    await page.waitForTimeout(5000);
    
    // Step 3: Send message directly via WebSocket
    console.log('\n💬 Step 3: Sending text message directly');
    
    // Inject function to send WebSocket message
    await page.evaluate(() => {
      // Find the WebSocket connection
      const sockets = Array.from(window.performance.getEntries())
        .filter(e => e.name.includes('ws://') || e.name.includes('wss://'));
      
      console.log('Found WebSocket entries:', sockets.length);
      
      // Try to send through the app's WebSocket directly
      // This depends on how the app exposes its WebSocket
      if (window.ws || window.websocket || window.socket) {
        const ws = window.ws || window.websocket || window.socket;
        const message = JSON.stringify({
          type: 'user_text',
          text: 'What time is it?'
        });
        ws.send(message);
        console.log('Sent message via app WebSocket');
      } else {
        console.log('Could not find WebSocket reference in window');
      }
    });
    
    // Alternative: simulate text input if WebSocket approach doesn't work
    console.log('\n🔄 Trying alternative text input method...');
    
    // Look for any text input fields
    const textInputs = await page.locator('input[type="text"], textarea').all();
    if (textInputs.length > 0) {
      console.log(`Found ${textInputs.length} text input(s)`);
      await textInputs[0].fill('What time is it?');
      await textInputs[0].press('Enter');
      console.log('✅ Submitted text via input field');
    }
    
    // Wait for response
    console.log('\n⏳ Waiting for response...');
    await page.waitForTimeout(10000);
    
    await page.screenshot({ path: 'test-ws-2-after-message.png' });
    
    // Check backend logs for MCP activity
    console.log('\n📋 Checking backend logs for MCP activity...');
    try {
      const { stdout } = await execAsync(`
        docker logs unmute-backend 2>&1 | tail -100 | grep -E "(TOOL_CALL|Executing tool|time\\.get_current_time|MCP Tool|Invalid request)" | tail -30
      `);
      console.log('\n📜 Recent MCP-related logs:');
      console.log(stdout || '(No MCP activity found in logs)');
    } catch (logError) {
      console.log('⚠️  Could not fetch logs:', logError.message);
    }
    
    // Final summary
    console.log('\n' + '=' .repeat(60));
    console.log('📊 Test Summary:');
    console.log('- Check screenshots for visual verification');
    console.log('- Check logs above for MCP tool execution');
    
  } catch (error) {
    console.error('❌ Test failed:', error);
  } finally {
    await browser.close();
  }
}

// Run the test
testMCPWebSocket().catch(console.error);