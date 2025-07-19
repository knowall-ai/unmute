const { chromium } = require('playwright');

async function testVoiceMCP() {
  console.log('🎤 Testing MCP via voice interaction');
  
  const browser = await chromium.launch({
    headless: false,
    args: ['--use-fake-ui-for-media-stream']
  });
  
  const page = await browser.newPage();
  
  // Monitor logs
  page.on('console', msg => console.log(`Browser: ${msg.text()}`));
  
  await page.goto('http://localhost:3000');
  await page.waitForTimeout(2000);
  
  // Click play button
  const playButton = await page.locator('canvas.rounded-full.cursor-pointer');
  await playButton.click();
  
  // Wait for agent to initialize
  console.log('Waiting for agent initialization...');
  await page.waitForTimeout(15000);
  
  // Take screenshot
  await page.screenshot({ path: 'test-voice-ready.png' });
  console.log('Screenshot saved. Agent should be ready.');
  
  // Monitor backend logs in separate terminal
  console.log('\n⚠️  Now speak into your microphone: "What time is it?"');
  console.log('Monitor backend logs with: docker logs -f unmute-backend | grep -E "(TOOL_CALL|MCP|time\\.get_current_time)"');
  
  // Keep browser open for manual testing
  await page.waitForTimeout(60000);
  
  await browser.close();
}

testVoiceMCP().catch(console.error);