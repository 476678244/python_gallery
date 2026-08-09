/**
 * Browser log export — tee Playwright page console + network to log files.
 * Aligns with flow_coding_logging skill (④ browser feedback for CDP/Boss 直聘).
 */

import fs from "fs";
import path from "path";
import type { Page } from "@playwright/test";
import { BOSS_HIRE_WORKDIR, sessionStamp } from "./readonly-guard";

export const BROWSER_LOG_FILES = {
  console: "browser-console.log",
  network: "browser-network.log",
  navigation: "browser-navigation.log",
} as const;

export interface BrowserLogPaths {
  logDir: string;
  console: string;
  network: string;
  navigation: string;
  sessionMeta: string;
}

function appendLine(filePath: string, line: string): void {
  fs.appendFileSync(filePath, line + "\n", "utf-8");
}

function ts(): string {
  return new Date().toISOString();
}

/** Ensure logs/ under BOSS_HIRE_WORKDIR and return file paths. */
export function prepareBrowserLogDir(sessionId?: string): BrowserLogPaths {
  const sid = sessionId ?? sessionStamp();
  const logDir = path.join(BOSS_HIRE_WORKDIR, "logs");
  fs.mkdirSync(logDir, { recursive: true });

  const paths: BrowserLogPaths = {
    logDir,
    console: path.join(logDir, BROWSER_LOG_FILES.console),
    network: path.join(logDir, BROWSER_LOG_FILES.network),
    navigation: path.join(logDir, BROWSER_LOG_FILES.navigation),
    sessionMeta: path.join(logDir, `session-${sid}.json`),
  };

  if (!fs.existsSync(paths.console)) {
    appendLine(paths.console, `# browser-console.log — started ${ts()}`);
  }
  if (!fs.existsSync(paths.network)) {
    appendLine(paths.network, `# browser-network.log — started ${ts()}`);
  }
  if (!fs.existsSync(paths.navigation)) {
    appendLine(paths.navigation, `# browser-navigation.log — started ${ts()}`);
  }

  return paths;
}

/**
 * Attach listeners: console / request / response / framenavigated → append to log files.
 * Call once per page at session start.
 */
export function installBrowserLogExport(
  page: Page,
  sessionId?: string,
): BrowserLogPaths {
  const sid = sessionId ?? sessionStamp();
  const paths = prepareBrowserLogDir(sid);

  fs.writeFileSync(
    paths.sessionMeta,
    JSON.stringify(
      {
        sessionId: sid,
        startedAt: ts(),
        initialUrl: page.url(),
        logDir: paths.logDir,
        files: BROWSER_LOG_FILES,
      },
      null,
      2,
    ),
    "utf-8",
  );

  page.on("console", (msg) => {
    const loc = msg.location();
    appendLine(
      paths.console,
      `[${ts()}] [${msg.type()}] ${msg.text()} (${loc.url}:${loc.lineNumber})`,
    );
  });

  page.on("pageerror", (err) => {
    appendLine(paths.console, `[${ts()}] [pageerror] ${err.message}`);
  });

  page.on("request", (req) => {
    appendLine(
      paths.network,
      `[${ts()}] → ${req.method()} ${req.url()}`,
    );
  });

  page.on("response", (res) => {
    const req = res.request();
    appendLine(
      paths.network,
      `[${ts()}] ← ${res.status()} ${req.method()} ${res.url()}`,
    );
  });

  page.on("requestfailed", (req) => {
    appendLine(
      paths.network,
      `[${ts()}] ✗ FAILED ${req.method()} ${req.url()} ${req.failure()?.errorText ?? ""}`,
    );
  });

  page.on("framenavigated", (frame) => {
    if (frame === page.mainFrame()) {
      appendLine(paths.navigation, `[${ts()}] navigate ${frame.url()}`);
    }
  });

  appendLine(paths.navigation, `[${ts()}] log export attached url=${page.url()}`);
  console.log(`[browser-log-export] logs → ${paths.logDir}`);

  return paths;
}
