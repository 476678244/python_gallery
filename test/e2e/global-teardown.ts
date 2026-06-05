/**
 * Global Teardown for Playwright Tests
 * Automatically cleanup servers after all tests complete
 */

import { execSync } from "child_process";

async function globalTeardown() {
  console.log("\n🧹 Global Teardown: Cleaning up servers...");
  
  try {
    // Kill API server (uvicorn)
    execSync("pkill -f 'uvicorn.*main:app' 2>/dev/null || true", { stdio: "inherit" });
    execSync("pkill -f 'start_api.py' 2>/dev/null || true", { stdio: "inherit" });
    
    // Kill Next.js dev server
    execSync("pkill -f 'next dev' 2>/dev/null || true", { stdio: "inherit" });
    
    // Wait a moment for processes to terminate
    await new Promise(resolve => setTimeout(resolve, 1000));
    
    // Force kill any remaining processes on ports 8000 and 3000
    try {
      const apiPids = execSync("lsof -ti:8000 2>/dev/null || echo ''", { encoding: "utf-8" }).trim();
      if (apiPids) {
        console.log(`   Killing API processes: ${apiPids}`);
        execSync(`kill -9 ${apiPids} 2>/dev/null || true`);
      }
    } catch (e) {
      // Ignore errors
    }
    
    try {
      const uiPids = execSync("lsof -ti:3000 2>/dev/null || echo ''", { encoding: "utf-8" }).trim();
      if (uiPids) {
        console.log(`   Killing UI processes: ${uiPids}`);
        execSync(`kill -9 ${uiPids} 2>/dev/null || true`);
      }
    } catch (e) {
      // Ignore errors
    }
    
    console.log("✅ Servers cleaned up");
  } catch (error) {
    console.log("⚠️  Cleanup warning:", error);
  }
}

export default globalTeardown;
